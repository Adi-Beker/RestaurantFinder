"""Tests for scripts/refresh.py CLI logic."""
from __future__ import annotations

import asyncio
import json
import uuid

import httpx
import pytest
from tenacity import RetryError, stop_after_attempt, wait_none

from scripts.refresh import _enqueue


# ── Fake transport ────────────────────────────────────────────────────────────

class CapturingTransport(httpx.AsyncBaseTransport):
    """Returns pre-configured responses in order; records every request."""

    def __init__(self, responses: list[httpx.Response]) -> None:
        self.responses = list(responses)
        self.requests: list[httpx.Request] = []

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self.responses.pop(0)


def _ok(job_id: str = "test-job-id") -> httpx.Response:
    return httpx.Response(202, json={"job_id": job_id})


def _err(status_code: int = 503) -> httpx.Response:
    return httpx.Response(status_code, json={"detail": "error"})


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def fast_retry(monkeypatch):
    """Remove retry wait so tests run instantly."""
    monkeypatch.setattr(_enqueue.retry, "wait", wait_none())
    monkeypatch.setattr(_enqueue.retry, "stop", stop_after_attempt(3))


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_enqueue_sends_required_headers():
    transport = CapturingTransport([_ok()])
    sem = asyncio.Semaphore(1)
    idempotency_key = "idem-key-xyz"

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        result = await _enqueue(client, "http://test", "my-token", sem, idempotency_key)

    assert result["job_id"] == "test-job-id"
    req = transport.requests[0]
    assert req.headers["Authorization"] == "Bearer my-token"
    assert req.headers["Idempotency-Key"] == idempotency_key
    assert "X-Trace-Id" in req.headers
    # X-Trace-Id must be a valid UUID
    uuid.UUID(req.headers["X-Trace-Id"])


@pytest.mark.anyio
async def test_enqueue_retries_on_transient_failure():
    """503 on first two attempts, 202 on third — should succeed."""
    transport = CapturingTransport([_err(503), _err(503), _ok()])
    sem = asyncio.Semaphore(1)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        result = await _enqueue(client, "http://test", "tok", sem, "idem-key")

    assert result["job_id"] == "test-job-id"
    assert len(transport.requests) == 3


@pytest.mark.anyio
async def test_enqueue_raises_after_max_retries(monkeypatch):
    """All 3 attempts fail → RetryError raised."""
    transport = CapturingTransport([_err(503), _err(503), _err(503)])
    sem = asyncio.Semaphore(1)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        with pytest.raises(RetryError):
            await _enqueue(client, "http://test", "tok", sem, "idem-key")

    assert len(transport.requests) == 3


@pytest.mark.anyio
async def test_enqueue_uses_same_idempotency_key_across_retries():
    """The idempotency key must be identical on every retry attempt."""
    transport = CapturingTransport([_err(503), _ok()])
    sem = asyncio.Semaphore(1)
    idem_key = "stable-key"

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        await _enqueue(client, "http://test", "tok", sem, idem_key)

    for req in transport.requests:
        assert req.headers["Idempotency-Key"] == idem_key


@pytest.mark.anyio
async def test_enqueue_uses_fresh_trace_id_per_attempt():
    """X-Trace-Id must differ between retry attempts."""
    transport = CapturingTransport([_err(503), _ok()])
    sem = asyncio.Semaphore(1)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        await _enqueue(client, "http://test", "tok", sem, "idem-key")

    trace_ids = [r.headers["X-Trace-Id"] for r in transport.requests]
    assert trace_ids[0] != trace_ids[1]
