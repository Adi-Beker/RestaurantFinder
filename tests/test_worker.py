"""Tests for the Arq worker task using fakeredis + in-memory SQLite."""
import json
import sqlite3

import fakeredis.aioredis
import pytest

from app.database import init_schema
from app.summary import build_summary as _build_summary
from worker.main import refresh_restaurants_task


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def worker_ctx():
    """Provide a fake worker context with in-memory SQLite and fake async Redis."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    init_schema(conn)
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield {"db": conn, "redis": redis}
    conn.close()


def _seed(conn: sqlite3.Connection, user_id: int, restaurants: list[dict]) -> None:
    for r in restaurants:
        conn.execute(
            """
            INSERT INTO restaurants
                (name, city, country, cuisine, price_level, rating, is_open, user_id)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (r["name"], r["city"], r["country"], r["cuisine"], r.get("price_level", 3), r["rating"], user_id),
        )
    conn.commit()


# ── Unit tests for summary computation (sync, no Redis needed) ───────────────

def test_build_summary_empty():
    result = _build_summary([])
    assert result["total_visited"] == 0
    assert result["top_cuisine"] is None
    assert result["highest_rated"] is None
    assert result["avg_rating"] is None
    assert result["by_cuisine"] == {}


def test_build_summary_single_restaurant():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_schema(conn)
    conn.execute(
        "INSERT INTO restaurants (name, city, country, cuisine, price_level, rating, is_open, user_id) VALUES (?, ?, ?, ?, ?, ?, 1, 1)",
        ("La Piazza", "Tel Aviv", "Israel", "Italian", 3, 4.5),
    )
    conn.commit()
    rows = conn.execute("SELECT name, cuisine, rating FROM restaurants").fetchall()

    result = _build_summary(rows)
    assert result["total_visited"] == 1
    assert result["top_cuisine"] == "Italian"
    assert result["avg_rating"] == 4.5
    assert result["highest_rated"]["name"] == "La Piazza"
    assert result["by_cuisine"]["Italian"]["count"] == 1


def test_build_summary_multiple_cuisines():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_schema(conn)
    for name, cuisine, rating in [
        ("La Piazza", "Italian", 4.5),
        ("Trattoria Roma", "Italian", 4.2),
        ("Tokyo Table", "Japanese", 4.8),
    ]:
        conn.execute(
            "INSERT INTO restaurants (name, city, country, cuisine, price_level, rating, is_open, user_id) VALUES (?, 'X', 'X', ?, 3, ?, 1, 1)",
            (name, cuisine, rating),
        )
    conn.commit()
    rows = conn.execute("SELECT name, cuisine, rating FROM restaurants").fetchall()

    result = _build_summary(rows)
    assert result["total_visited"] == 3
    assert result["top_cuisine"] == "Italian"  # 2 Italian vs 1 Japanese
    assert result["highest_rated"]["name"] == "Tokyo Table"
    assert result["highest_rated"]["rating"] == 4.8
    assert result["by_cuisine"]["Italian"]["count"] == 2
    assert result["by_cuisine"]["Italian"]["avg_rating"] == 4.35
    assert result["by_cuisine"]["Japanese"]["count"] == 1
    assert round(result["avg_rating"], 2) == round((4.5 + 4.2 + 4.8) / 3, 2)


# ── Async integration tests (task + Redis) ────────────────────────────────────

@pytest.mark.anyio
async def test_task_sets_status_done(worker_ctx):
    _seed(worker_ctx["db"], 1, [
        {"name": "La Piazza", "city": "Tel Aviv", "country": "Israel", "cuisine": "Italian", "rating": 4.5},
    ])

    await refresh_restaurants_task(worker_ctx, user_id=1, job_id="job-001")

    status = await worker_ctx["redis"].hget("job:job-001", "status")
    assert status == "done"


@pytest.mark.anyio
async def test_task_writes_finished_at(worker_ctx):
    await refresh_restaurants_task(worker_ctx, user_id=1, job_id="job-002")
    finished_at = await worker_ctx["redis"].hget("job:job-002", "finished_at")
    assert finished_at is not None
    assert "T" in finished_at  # ISO 8601 format


@pytest.mark.anyio
async def test_task_result_contains_summary_fields(worker_ctx):
    _seed(worker_ctx["db"], 1, [
        {"name": "La Piazza", "city": "Tel Aviv", "country": "Israel", "cuisine": "Italian", "rating": 4.5},
        {"name": "Tokyo Table", "city": "Tokyo", "country": "Japan", "cuisine": "Japanese", "rating": 4.8},
        {"name": "Trattoria", "city": "Rome", "country": "Italy", "cuisine": "Italian", "rating": 4.2},
    ])

    await refresh_restaurants_task(worker_ctx, user_id=1, job_id="job-003")

    result = json.loads(await worker_ctx["redis"].hget("job:job-003", "result"))
    assert result["total_visited"] == 3
    assert result["top_cuisine"] == "Italian"
    assert result["highest_rated"]["name"] == "Tokyo Table"
    assert result["highest_rated"]["rating"] == 4.8
    assert "Italian" in result["by_cuisine"]
    assert result["by_cuisine"]["Italian"]["count"] == 2


@pytest.mark.anyio
async def test_task_empty_restaurants(worker_ctx):
    await refresh_restaurants_task(worker_ctx, user_id=1, job_id="job-empty")

    status = await worker_ctx["redis"].hget("job:job-empty", "status")
    result = json.loads(await worker_ctx["redis"].hget("job:job-empty", "result"))

    assert status == "done"
    assert result["total_visited"] == 0
    assert result["top_cuisine"] is None
    assert result["highest_rated"] is None


@pytest.mark.anyio
async def test_task_scoped_to_user(worker_ctx):
    """Task only sees the restaurants belonging to the requested user_id."""
    _seed(worker_ctx["db"], 1, [
        {"name": "La Piazza", "city": "Tel Aviv", "country": "Israel", "cuisine": "Italian", "rating": 4.5},
    ])
    _seed(worker_ctx["db"], 2, [
        {"name": "Tokyo Table", "city": "Tokyo", "country": "Japan", "cuisine": "Japanese", "rating": 4.8},
        {"name": "Sushi Place", "city": "Tokyo", "country": "Japan", "cuisine": "Japanese", "rating": 4.6},
    ])

    await refresh_restaurants_task(worker_ctx, user_id=1, job_id="job-user1")

    result = json.loads(await worker_ctx["redis"].hget("job:job-user1", "result"))
    assert result["total_visited"] == 1
    assert result["top_cuisine"] == "Italian"
