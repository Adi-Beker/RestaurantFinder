from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

from app.dependencies import ConnDep
from app.models import UserPublic

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-do-not-use-in-production!!")
JWT_ALGORITHM = "HS256"
JWT_ISSUER = "restaurant-finder"
JWT_AUDIENCE = "restaurant-finder-api"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
_oauth2 = OAuth2PasswordBearer(tokenUrl="/token")


def hash_password(plain: str) -> str:
    return _pwd.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


def create_access_token(username: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "sub": username,
        "role": role,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
            audience=JWT_AUDIENCE,
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def find_user(conn: sqlite3.Connection, username: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT id, username, password_hash, role FROM users WHERE username = ?",
        (username,),
    ).fetchone()


def create_user(conn: sqlite3.Connection, username: str, hashed_password: str) -> sqlite3.Row:
    cursor = conn.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'user')",
        (username, hashed_password),
    )
    conn.commit()
    return conn.execute(
        "SELECT id, username, role FROM users WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()


def get_current_user(
    token: Annotated[str, Depends(_oauth2)],
    conn: ConnDep,
) -> UserPublic:
    payload = _decode_token(token)
    username: str = payload["sub"]
    row = find_user(conn, username)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return UserPublic(id=row["id"], username=row["username"], role=row["role"])


CurrentUser = Annotated[UserPublic, Depends(get_current_user)]


def list_users(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT id, username, role FROM users").fetchall()


def require_admin(current_user: CurrentUser) -> UserPublic:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


AdminUser = Annotated[UserPublic, Depends(require_admin)]


def update_password(conn: sqlite3.Connection, username: str, new_hash: str) -> None:
    conn.execute(
        "UPDATE users SET password_hash = ? WHERE username = ?",
        (new_hash, username),
    )
    conn.commit()
