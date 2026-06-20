import sqlite3

import fakeredis
import pytest
from fastapi.testclient import TestClient

from app.database import init_schema
from app.dependencies import get_conn, get_repository
from app.main import app
from app.redis import get_redis
from app.repository import RestaurantRepository


@pytest.fixture
def test_db():
    """
    Provide a fresh in-memory SQLite connection and wire it into FastAPI's
    get_conn dependency.  Tests that need direct DB access (e.g. to seed an
    admin user) can declare this fixture alongside client.
    """
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    init_schema(conn)

    def _override_conn():
        yield conn

    app.dependency_overrides[get_conn] = _override_conn
    yield conn
    conn.close()


@pytest.fixture
def client(test_db):
    """
    Provide a TestClient backed by the test_db in-memory database and an
    isolated fakeredis instance.  Each test gets a fresh Redis state so rate
    limit counters never bleed between tests.
    """
    repo = RestaurantRepository(test_db)
    fake_redis = fakeredis.FakeRedis(decode_responses=True)

    def _override_repo():
        yield repo

    def _override_redis():
        yield fake_redis

    app.dependency_overrides[get_repository] = _override_repo
    app.dependency_overrides[get_redis] = _override_redis
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def auth_client(client):
    """
    TestClient with a pre-authenticated regular user.

    The Bearer token is set as a default header so every request the fixture
    makes is automatically authenticated as 'testuser'.
    """
    client.post("/auth/register", json={"username": "testuser", "password": "testpass"})
    token = client.post(
        "/token", data={"username": "testuser", "password": "testpass"}
    ).json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client
