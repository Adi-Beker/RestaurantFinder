"""Tests for discover_restaurants table creation and seed behavior."""
import sqlite3

import pytest

from app.database import init_schema
from app.discover_seed import SEED_RESTAURANTS, seed_discover_restaurants


@pytest.fixture()
def conn():
    """In-memory SQLite connection, schema initialised."""
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    init_schema(c)
    yield c
    c.close()


def _count(c: sqlite3.Connection) -> int:
    return c.execute("SELECT COUNT(*) FROM discover_restaurants").fetchone()[0]


def test_table_exists_after_init(conn):
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert "discover_restaurants" in tables


def test_seed_inserted_on_empty_table(conn):
    assert _count(conn) == len(SEED_RESTAURANTS)


def test_seed_is_idempotent(conn):
    before = _count(conn)
    seed_discover_restaurants(conn)
    assert _count(conn) == before


def test_seed_rows_have_required_fields(conn):
    row = conn.execute("SELECT * FROM discover_restaurants LIMIT 1").fetchone()
    assert row["osm_id"].startswith("seed-")
    assert row["name"]
    assert row["city"]
    assert row["country"] == "Israel"
    assert row["cuisine"]


def test_seed_covers_all_four_cities(conn):
    cities = {
        row[0]
        for row in conn.execute(
            "SELECT DISTINCT city FROM discover_restaurants"
        ).fetchall()
    }
    assert cities == {"Tel Aviv", "Jerusalem", "Haifa", "Ashdod"}


def test_no_seed_when_table_already_has_rows():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    # Manually create the table and insert one row before init_schema runs.
    c.execute(
        """
        CREATE TABLE discover_restaurants (
            id INTEGER PRIMARY KEY, osm_id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL, city TEXT NOT NULL,
            country TEXT NOT NULL DEFAULT 'Israel', cuisine TEXT NOT NULL,
            address TEXT NOT NULL DEFAULT '', lat REAL NOT NULL DEFAULT 0.0,
            lon REAL NOT NULL DEFAULT 0.0, price_level INTEGER NOT NULL DEFAULT 3,
            rating REAL NOT NULL DEFAULT 4.0, is_open INTEGER NOT NULL DEFAULT 1,
            last_updated TEXT NOT NULL DEFAULT ''
        )
        """
    )
    c.execute(
        "INSERT INTO discover_restaurants (osm_id, name, city, cuisine) VALUES (?, ?, ?, ?)",
        ("existing-1", "Already There", "Tel Aviv", "Israeli"),
    )
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'user')")
    c.execute("CREATE TABLE IF NOT EXISTS restaurants (id INTEGER PRIMARY KEY, name TEXT NOT NULL, city TEXT NOT NULL, country TEXT NOT NULL, cuisine TEXT NOT NULL, price_level INTEGER NOT NULL, rating REAL NOT NULL, is_open INTEGER NOT NULL, user_id INTEGER NOT NULL REFERENCES users(id))")
    c.commit()

    # init_schema sees COUNT(*) = 1 → must NOT seed
    init_schema(c)

    assert c.execute("SELECT COUNT(*) FROM discover_restaurants").fetchone()[0] == 1
    c.close()
