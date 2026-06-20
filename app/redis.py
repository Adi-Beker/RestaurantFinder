from __future__ import annotations

import os
from collections.abc import AsyncGenerator, Generator
from typing import Annotated

import redis
from arq import create_pool
from arq.connections import ArqRedis, RedisSettings
from fastapi import Depends, HTTPException, status

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

_RATE_LIMIT_WINDOW = 60   # seconds
_RATE_LIMIT_MAX = 10      # attempts per window


def get_redis() -> Generator[redis.Redis, None, None]:
    """Yield a Redis client. Override in tests via dependency_overrides."""
    client: redis.Redis = redis.from_url(REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        client.close()


RedisDep = Annotated[redis.Redis, Depends(get_redis)]


async def get_arq_pool() -> AsyncGenerator[ArqRedis, None]:
    """Yield an Arq Redis pool for enqueueing jobs. Override in tests via dependency_overrides."""
    pool = await create_pool(RedisSettings.from_dsn(REDIS_URL))
    try:
        yield pool
    finally:
        await pool.aclose()


ArqDep = Annotated[ArqRedis, Depends(get_arq_pool)]


def check_login_rate_limit(client: redis.Redis, ip: str) -> None:
    """Raise 429 if the given IP has exceeded the login rate limit."""
    key = f"rate_limit:login:{ip}"
    count = client.incr(key)
    if count == 1:
        client.expire(key, _RATE_LIMIT_WINDOW)
    if count > _RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again in a minute.",
            headers={"Retry-After": str(_RATE_LIMIT_WINDOW)},
        )


# ── Idempotency primitives (for future /refresh-jobs) ────────────────────────

_IDEMPOTENCY_TTL = 86_400  # 24 hours


def set_idempotency(client: redis.Redis, key: str, value: str) -> bool:
    """
    Store value under the idempotency key with a 24-hour TTL.
    Returns True if the key was newly set, False if it already existed.
    """
    return bool(client.set(f"idempotency:{key}", value, ex=_IDEMPOTENCY_TTL, nx=True))


def get_idempotency(client: redis.Redis, key: str) -> str | None:
    """Return the stored value for an idempotency key, or None if expired/missing."""
    return client.get(f"idempotency:{key}")
