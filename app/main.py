from __future__ import annotations

from fastapi import FastAPI, HTTPException, status

from app.dependencies import RepositoryDep
from app.models import Restaurant, RestaurantCreate

app = FastAPI(title="Restaurant Finder", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "app": "Restaurant Finder"}


@app.get("/restaurants", response_model=list[Restaurant])
def list_restaurants(repository: RepositoryDep) -> list[Restaurant]:
    """Return all restaurants."""
    return repository.list()


@app.post("/restaurants", response_model=Restaurant, status_code=status.HTTP_201_CREATED)
def create_restaurant(
    payload: RestaurantCreate,
    repository: RepositoryDep,
) -> Restaurant:
    """Create a new restaurant."""
    return repository.create(payload)


@app.get("/restaurants/{restaurant_id}", response_model=Restaurant)
def get_restaurant(restaurant_id: int, repository: RepositoryDep) -> Restaurant:
    """Return a restaurant by ID."""
    restaurant = repository.get(restaurant_id)
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
) -> Restaurant:
    """Update an existing restaurant."""
    updated_restaurant = repository.update(restaurant_id, payload)
    if updated_restaurant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )
    return updated_restaurant


@app.delete("/restaurants/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_restaurant(restaurant_id: int, repository: RepositoryDep) -> None:
    """Delete a restaurant by ID."""
    deleted = repository.delete(restaurant_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )