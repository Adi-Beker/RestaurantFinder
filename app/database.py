from __future__ import annotations

import os
import sqlite3
from pathlib import Path

# Default: restaurants.db next to the project root.
# Override with the DB_PATH environment variable (used in Docker).
DB_PATH = Path(os.getenv("DB_PATH", str(Path(__file__).parent.parent / "restaurants.db")))


def get_connection(path: str | Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # WAL mode allows concurrent reads while a write is in progress.
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """Create all tables if they do not exist."""
    # users must be created before restaurants (FK dependency).
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY,
            username      TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            role          TEXT    NOT NULL DEFAULT 'user'
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS restaurants (
            id          INTEGER PRIMARY KEY,
            name        TEXT    NOT NULL,
            city        TEXT    NOT NULL,
            country     TEXT    NOT NULL,
            cuisine     TEXT    NOT NULL,
            price_level INTEGER NOT NULL,
            rating      REAL    NOT NULL,
            is_open     INTEGER NOT NULL,
            user_id     INTEGER NOT NULL REFERENCES users(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS discover_restaurants (
            id           INTEGER PRIMARY KEY,
            osm_id       TEXT    NOT NULL UNIQUE,
            name         TEXT    NOT NULL,
            city         TEXT    NOT NULL,
            country      TEXT    NOT NULL DEFAULT 'Israel',
            cuisine      TEXT    NOT NULL,
            address      TEXT    NOT NULL DEFAULT '',
            lat          REAL    NOT NULL DEFAULT 0.0,
            lon          REAL    NOT NULL DEFAULT 0.0,
            price_level  INTEGER NOT NULL DEFAULT 3,
            rating       REAL    NOT NULL DEFAULT 4.0,
            is_open      INTEGER NOT NULL DEFAULT 1,
            last_updated TEXT    NOT NULL DEFAULT ''
        )
        """
    )
    conn.commit()

    from app.discover_seed import seed_discover_restaurants
    count = conn.execute("SELECT COUNT(*) FROM discover_restaurants").fetchone()[0]
    if count == 0:
        seed_discover_restaurants(conn)
