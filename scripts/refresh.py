"""CLI to enqueue a restaurant-refresh job and poll until done."""
from __future__ import annotations

import asyncio
import uuid

import httpx
import logfire
import typer
from tenacity import retry, stop_after_attempt, wait_exponential

logfire.configure(send_to_logfire=False)

app = typer.Typer(add_completion=False)

_CONCURRENCY = 1  # one job per invocation — semaphore is here for testability


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
async def _enqueue(
    client: httpx.AsyncClient,
    base_url: str,
    token: str,
    sem: asyncio.Semaphore,
    idempotency_key: str,
) -> dict:
    async with sem:
        with logfire.span("enqueue refresh job", idempotency_key=idempotency_key):
            resp = await client.post(
                f"{base_url}/refresh-jobs",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Idempotency-Key": idempotency_key,
                    "X-Trace-Id": str(uuid.uuid4()),
                },
            )
            resp.raise_for_status()
            return resp.json()


@app.command()
def run(
    url: str = typer.Option(..., help="Base URL of the API, e.g. http://localhost:8000"),
    token: str = typer.Option(..., help="Bearer token for authentication"),
    concurrency: int = typer.Option(_CONCURRENCY, help="Max concurrent requests"),
) -> None:
    """Enqueue a restaurant-refresh job and print the job id."""

    async def _main() -> None:
        sem = asyncio.Semaphore(concurrency)
        idempotency_key = str(uuid.uuid4())  # stable across retries for this run

        async with httpx.AsyncClient() as client:
            with logfire.span("refresh script run"):
                result = await _enqueue(client, url, token, sem, idempotency_key)
                typer.echo(f"Job enqueued: {result['job_id']}")

    asyncio.run(_main())


if __name__ == "__main__":
    app()
