from __future__ import annotations

import sqlite3
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends

from app.database import DB_PATH, get_connection, init_schema
from app.repository import RestaurantRepository

# Lazily-initialised module-level connection.
# Created on the first request so that importing this module during tests
# does not create a restaurants.db file on disk.
_conn: sqlite3.Connection | None = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = get_connection(DB_PATH)
        init_schema(_conn)
    return _conn


def get_conn() -> Generator[sqlite3.Connection, None, None]:
    """Yield the shared SQLite connection. Override in tests via dependency_overrides."""
    yield _get_conn()


def get_repository() -> Generator[RestaurantRepository, None, None]:
    """Provide the repository to route handlers via FastAPI DI."""
    yield RestaurantRepository(_get_conn())


ConnDep = Annotated[sqlite3.Connection, Depends(get_conn)]
RepositoryDep = Annotated[RestaurantRepository, Depends(get_repository)]
