from __future__ import annotations

import os

import httpx
from fastapi import HTTPException, status

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8001")


async def get_recommendation(
    username: str,
    summary: dict,
    visited_names: list[str] | None = None,
    excluded_names: list[str] | None = None,
    candidate_restaurants: list[dict] | None = None,
) -> dict:
    """Call ai_service POST /recommend and return the parsed response dict."""
    payload = {
        "username": username,
        "top_cuisine": summary.get("top_cuisine"),
        "avg_rating": summary.get("avg_rating"),
        "total_visited": summary.get("total_visited", 0),
        "visited_names": visited_names or [],
        "excluded_names": excluded_names or [],
        "candidate_restaurants": candidate_restaurants or [],
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{AI_SERVICE_URL}/recommend",
                json=payload,
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI service error: {exc.response.status_code}",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is unreachable",
        ) from exc
