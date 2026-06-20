"""Async tests for POST /refresh-jobs and GET /refresh-jobs/{job_id}."""
import sqlite3

import fakeredis
import httpx
import pytest

from app.database import init_schema
from app.dependencies import get_conn, get_repository
from app.main import app
from app.redis import get_arq_pool, get_redis
from app.repository import RestaurantRepository


# ── Fake Arq pool ─────────────────────────────────────────────────────────────

class FakeArqPool:
    """Records enqueue_job calls without executing tasks."""

    def __init__(self):
        self.enqueued: list[dict] = []

    async def enqueue_job(self, function_name: str, **kwargs) -> None:
        self.enqueued.append({"function": function_name, **kwargs})

    async def aclose(self) -> None:
        pass


# ── Fixture ───────────────────────────────────────────────────────────────────

@pytest.fixture
def refresh_setup():
    """
    Sync fixture: creates isolated in-memory SQLite + fakeredis + fake Arq pool
    and wires them into app.dependency_overrides.  Compatible with @pytest.mark.anyio
    tests because the overrides are set before the event loop starts and cleared after.
    """
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    init_schema(conn)

    fake_redis = fakeredis.FakeRedis(decode_responses=True)
    fake_pool = FakeArqPool()
    repo = RestaurantRepository(conn)

    def _override_conn():
        yield conn

    def _override_repo():
        yield repo

    def _override_redis():
        yield fake_redis

    async def _override_arq():
        yield fake_pool

    app.dependency_overrides[get_conn] = _override_conn
    app.dependency_overrides[get_repository] = _override_repo
    app.dependency_overrides[get_redis] = _override_redis
    app.dependency_overrides[get_arq_pool] = _override_arq

    yield {"redis": fake_redis, "pool": fake_pool}

    app.dependency_overrides.clear()
    conn.close()


# ── Helper ────────────────────────────────────────────────────────────────────

async def _auth_headers(client: httpx.AsyncClient, username: str = "adi", password: str = "secret") -> dict:
    await client.post("/auth/register", json={"username": username, "password": password})
    resp = await client.post("/token", data={"username": username, "password": password})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _async_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_post_refresh_jobs_returns_202_and_job_id(refresh_setup):
    async with _async_client() as client:
        headers = await _auth_headers(client)
        resp = await client.post("/refresh-jobs", headers=headers)

    assert resp.status_code == 202
    assert "job_id" in resp.json()
    assert len(resp.json()["job_id"]) > 0


@pytest.mark.anyio
async def test_post_refresh_jobs_enqueues_task(refresh_setup):
    async with _async_client() as client:
        headers = await _auth_headers(client)
        await client.post("/refresh-jobs", headers=headers)

    assert len(refresh_setup["pool"].enqueued) == 1
    job = refresh_setup["pool"].enqueued[0]
    assert job["function"] == "refresh_restaurants_task"
    assert "user_id" in job
    assert "job_id" in job


@pytest.mark.anyio
async def test_get_refresh_job_returns_pending_status(refresh_setup):
    async with _async_client() as client:
        headers = await _auth_headers(client)
        job_id = (await client.post("/refresh-jobs", headers=headers)).json()["job_id"]
        resp = await client.get(f"/refresh-jobs/{job_id}", headers=headers)

    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"


@pytest.mark.anyio
async def test_get_refresh_job_returns_done_result(refresh_setup):
    """Simulate a completed job by writing directly to fake Redis before the GET."""
    import json
    summary = {"total_visited": 3, "top_cuisine": "Italian"}

    async with _async_client() as client:
        headers = await _auth_headers(client)
        # Get the user's id by registering and checking — user was created in _auth_headers
        # We know the first user gets id=1
        refresh_setup["redis"].hset(
            "job:completed-job",
            mapping={
                "status": "done",
                "result": json.dumps(summary),
                "finished_at": "2026-01-01T00:00:00+00:00",
                "user_id": "1",
            },
        )
        resp = await client.get("/refresh-jobs/completed-job", headers=headers)

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "done"
    assert data["result"]["top_cuisine"] == "Italian"
    assert data["finished_at"] is not None


@pytest.mark.anyio
async def test_same_idempotency_key_returns_same_job_id_and_no_double_enqueue(refresh_setup):
    async with _async_client() as client:
        headers = await _auth_headers(client)
        idem_headers = {**headers, "Idempotency-Key": "unique-key-123"}

        resp1 = await client.post("/refresh-jobs", headers=idem_headers)
        resp2 = await client.post("/refresh-jobs", headers=idem_headers)

    assert resp1.status_code == 202
    assert resp2.status_code == 202
    assert resp1.json()["job_id"] == resp2.json()["job_id"]
    assert len(refresh_setup["pool"].enqueued) == 1  # only one enqueue


@pytest.mark.anyio
async def test_different_idempotency_keys_enqueue_separate_jobs(refresh_setup):
    async with _async_client() as client:
        headers = await _auth_headers(client)
        resp1 = await client.post("/refresh-jobs", headers={**headers, "Idempotency-Key": "key-A"})
        resp2 = await client.post("/refresh-jobs", headers={**headers, "Idempotency-Key": "key-B"})

    assert resp1.json()["job_id"] != resp2.json()["job_id"]
    assert len(refresh_setup["pool"].enqueued) == 2


@pytest.mark.anyio
async def test_post_refresh_jobs_without_auth_returns_401(refresh_setup):
    async with _async_client() as client:
        resp = await client.post("/refresh-jobs")
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_get_refresh_job_without_auth_returns_401(refresh_setup):
    async with _async_client() as client:
        resp = await client.get("/refresh-jobs/some-job-id")
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_get_nonexistent_job_returns_404(refresh_setup):
    async with _async_client() as client:
        headers = await _auth_headers(client)
        resp = await client.get("/refresh-jobs/does-not-exist", headers=headers)
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Job not found"


@pytest.mark.anyio
async def test_get_refresh_job_belonging_to_other_user_returns_403(refresh_setup):
    """A job created by user A cannot be read by user B."""
    async with _async_client() as client:
        # User A creates a job
        headers_a = await _auth_headers(client, username="user_a", password="pass_a")
        job_id = (await client.post("/refresh-jobs", headers=headers_a)).json()["job_id"]

        # User B tries to read that job
        headers_b = await _auth_headers(client, username="user_b", password="pass_b")
        resp = await client.get(f"/refresh-jobs/{job_id}", headers=headers_b)

    assert resp.status_code == 403
    assert resp.json()["detail"] == "Access denied"
