from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone

from arq.connections import RedisSettings

from app.database import DB_PATH, init_schema
from app.summary import build_summary


# ── Lifecycle hooks ───────────────────────────────────────────────────────────

async def startup(ctx: dict) -> None:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    init_schema(conn)
    ctx["db"] = conn


async def shutdown(ctx: dict) -> None:
    if "db" in ctx:
        ctx["db"].close()


# ── Task ─────────────────────────────────────────────────────────────────────

async def refresh_restaurants_task(ctx: dict, user_id: int, job_id: str) -> None:
    """
    Compute a personalized dining summary for the user and store the result
    in Redis under job:{job_id}.

    Summary fields:
      total_visited   — total number of restaurants in the visited list
      top_cuisine     — cuisine with the most visited entries
      avg_rating      — overall average rating across all restaurants
      highest_rated   — {name, rating, cuisine} of the top-rated restaurant
      by_cuisine      — per-cuisine {count, avg_rating} breakdown
    """
    redis = ctx["redis"]
    await redis.hset(f"job:{job_id}", mapping={"status": "running"})

    try:
        conn: sqlite3.Connection = ctx["db"]
        rows = conn.execute(
            "SELECT name, cuisine, rating FROM restaurants WHERE user_id = ?",
            (user_id,),
        ).fetchall()

        summary = build_summary(rows)

        await redis.hset(
            f"job:{job_id}",
            mapping={
                "status": "done",
                "result": json.dumps(summary),
                "finished_at": datetime.now(timezone.utc).isoformat(),
            },
        )
    except Exception as exc:
        await redis.hset(
            f"job:{job_id}",
            mapping={"status": "failed", "error": str(exc)},
        )
        raise


# ── Worker settings ───────────────────────────────────────────────────────────

class WorkerSettings:
    functions = [refresh_restaurants_task]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(os.getenv("REDIS_URL", "redis://localhost:6379"))
    max_jobs = 10
