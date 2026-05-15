import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.database import init_schema
from app.dependencies import get_repository
from app.main import app
from app.repository import RestaurantRepository


@pytest.fixture
def client():
    """
    Provide a TestClient backed by a fresh in-memory SQLite database.

    Each test gets an isolated database so tests cannot interfere with each
    other.  The dependency override is cleared after the test so other
    fixtures are unaffected.
    """
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    init_schema(conn)

    repo = RestaurantRepository(conn)

    def _override():
        yield repo

    app.dependency_overrides[get_repository] = _override
    yield TestClient(app)
    app.dependency_overrides.clear()
    conn.close()
