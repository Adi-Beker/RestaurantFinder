from __future__ import annotations

import json
import random
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm

from app.ai_client import get_recommendation
from app.discover_repo import get_cities, get_discover_restaurants
from app.auth import (
    AdminUser,
    CurrentUser,
    create_access_token,
    create_user,
    find_user,
    hash_password,
    list_users,
    update_password,
    verify_password,
)
from app.dependencies import ConnDep, RepositoryDep
from app.models import (
    AIRecommendation,
    ChangePasswordRequest,
    DiscoverRestaurant,
    RefreshJobCreated,
    RefreshJobStatus,
    Restaurant,
    RestaurantCreate,
    TokenResponse,
    UserCreate,
    UserPublic,
)
from app.summary import build_summary
from app.redis import ArqDep, RedisDep, check_login_rate_limit, get_idempotency, set_idempotency

app = FastAPI(title="Restaurant Finder", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/auth/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, conn: ConnDep) -> UserPublic:
    if find_user(conn, payload.username) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )
    row = create_user(conn, payload.username, hash_password(payload.password))
    return UserPublic(id=row["id"], username=row["username"], role=row["role"])


@app.post("/token", response_model=TokenResponse)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    conn: ConnDep,
    redis: RedisDep,
    request: Request,
) -> TokenResponse:
    ip = request.client.host if request.client else "unknown"
    check_login_rate_limit(redis, ip)
    row = find_user(conn, form.username)
    if row is None or not verify_password(form.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return TokenResponse(access_token=create_access_token(row["username"], row["role"]))


@app.get("/auth/me", response_model=UserPublic)
def me(current_user: CurrentUser) -> UserPublic:
    return current_user


@app.post("/auth/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: ChangePasswordRequest,
    current_user: CurrentUser,
    conn: ConnDep,
) -> None:
    row = find_user(conn, current_user.username)
    if row is None or not verify_password(payload.current_password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )
    update_password(conn, current_user.username, hash_password(payload.new_password))


@app.get("/admin/users", response_model=list[UserPublic])
def admin_list_users(conn: ConnDep, _: AdminUser) -> list[UserPublic]:
    return [UserPublic(id=r["id"], username=r["username"], role=r["role"]) for r in list_users(conn)]


@app.post("/refresh-jobs", response_model=RefreshJobCreated, status_code=status.HTTP_202_ACCEPTED)
async def create_refresh_job(
    current_user: CurrentUser,
    redis: RedisDep,
    arq: ArqDep,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> RefreshJobCreated:
    if idempotency_key:
        existing = get_idempotency(redis, idempotency_key)
        if existing:
            return RefreshJobCreated(job_id=existing)

    job_id = str(uuid4())

    if idempotency_key:
        set_idempotency(redis, idempotency_key, job_id)

    redis.hset(f"job:{job_id}", mapping={"status": "pending", "user_id": str(current_user.id)})
    await arq.enqueue_job("refresh_restaurants_task", user_id=current_user.id, job_id=job_id)

    return RefreshJobCreated(job_id=job_id)


@app.get("/refresh-jobs/{job_id}", response_model=RefreshJobStatus)
def get_refresh_job(
    job_id: str,
    current_user: CurrentUser,
    redis: RedisDep,
) -> RefreshJobStatus:
    raw = redis.hgetall(f"job:{job_id}")
    if not raw:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if raw.get("user_id") != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    result = json.loads(raw["result"]) if raw.get("result") else None

    return RefreshJobStatus(
        status=raw["status"],
        result=result,
        finished_at=raw.get("finished_at"),
        error=raw.get("error"),
    )


@app.get("/ai/recommendation", response_model=AIRecommendation)
async def ai_recommendation(
    current_user: CurrentUser,
    conn: ConnDep,
    exclude: list[str] = Query(default=[]),
) -> AIRecommendation:
    rows = conn.execute(
        "SELECT name, cuisine, rating FROM restaurants WHERE user_id = ?",
        (current_user.id,),
    ).fetchall()
    summary = build_summary(rows)
    visited_names = [row["name"] for row in rows]
    excluded_names = list(exclude)

    all_excluded_lower = {n.lower() for n in visited_names + excluded_names}
    discover_rows = conn.execute(
        "SELECT name, city, cuisine FROM discover_restaurants"
    ).fetchall()
    candidates = [
        {"name": row["name"], "city": row["city"], "cuisine": row["cuisine"]}
        for row in discover_rows
        if row["name"].lower() not in all_excluded_lower
    ]
    random.shuffle(candidates)

    if not candidates:
        return AIRecommendation(
            restaurant_name="",
            city="",
            reason="You've explored everything in our catalogue — check back after we add more restaurants!",
        )

    data = await get_recommendation(
        current_user.username,
        summary,
        visited_names=visited_names,
        excluded_names=excluded_names,
        candidate_restaurants=candidates,
    )
    return AIRecommendation(**data)


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "app": "Restaurant Finder"}


@app.get("/restaurants", response_model=list[Restaurant])
def list_restaurants(repository: RepositoryDep, current_user: CurrentUser) -> list[Restaurant]:
    return repository.list(current_user.id)


@app.post("/restaurants", response_model=Restaurant, status_code=status.HTTP_201_CREATED)
def create_restaurant(
    payload: RestaurantCreate,
    repository: RepositoryDep,
    current_user: CurrentUser,
) -> Restaurant:
    try:
        return repository.create(payload, current_user.id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@app.get("/restaurants/{restaurant_id}", response_model=Restaurant)
def get_restaurant(
    restaurant_id: int,
    repository: RepositoryDep,
    current_user: CurrentUser,
) -> Restaurant:
    restaurant = repository.get(restaurant_id, current_user.id)
    if restaurant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )
    return restaurant


@app.put("/restaurants/{restaurant_id}", response_model=Restaurant)
def update_restaurant(
    restaurant_id: int,
    payload: RestaurantCreate,
    repository: RepositoryDep,
    current_user: CurrentUser,
) -> Restaurant:
    try:
        updated_restaurant = repository.update(restaurant_id, payload, current_user.id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    if updated_restaurant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )
    return updated_restaurant


@app.delete("/restaurants/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_restaurant(
    restaurant_id: int,
    repository: RepositoryDep,
    current_user: CurrentUser,
) -> None:
    deleted = repository.delete(restaurant_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )


@app.get("/discover/cities", response_model=list[str])
def discover_cities(_: CurrentUser, conn: ConnDep) -> list[str]:
    return get_cities(conn)


@app.get("/discover/restaurants", response_model=list[DiscoverRestaurant])
def discover_restaurants(
    _: CurrentUser,
    conn: ConnDep,
    city: str | None = None,
) -> list[DiscoverRestaurant]:
    return get_discover_restaurants(conn, city)