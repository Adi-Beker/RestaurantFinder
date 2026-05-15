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
    """Create the restaurants table if it does not exist."""
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
            is_open     INTEGER NOT NULL
        )
        """
    )
    conn.commit()
