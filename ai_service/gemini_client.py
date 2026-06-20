from __future__ import annotations

import json
import logging
import os
import random
import re

from google import genai
from google.genai import types

from ai_service.models import RecommendRequest, RecommendResponse

logger = logging.getLogger(__name__)


def _fallback(request: RecommendRequest) -> RecommendResponse:
    """Pick the best candidate from the provided list without calling Gemini."""
    candidates = request.candidate_restaurants
    if not candidates:
        return RecommendResponse(
            restaurant_name="",
            city="",
            reason="You've explored everything in our catalogue — check back after we add more restaurants!",
        )

    # Prefer candidates matching the user's top cuisine, pick randomly within the group
    top = (request.top_cuisine or "").strip().title()
    matching = [c for c in candidates if c.cuisine.strip().title() == top]
    pick = random.choice(matching) if matching else random.choice(candidates)

    return RecommendResponse(
        restaurant_name=pick.name,
        city=pick.city,
        reason=f"A highly-regarded {pick.cuisine} restaurant in {pick.city} that fits your dining profile",
    )


def _build_prompt(request: RecommendRequest) -> str:
    top_cuisine = request.top_cuisine or "not specified"
    avg_rating = str(request.avg_rating) if request.avg_rating is not None else "not available"

    candidate_lines = "\n".join(
        f"- {c.name} ({c.cuisine}, {c.city}, Israel)"
        for c in request.candidate_restaurants
    )
    if not candidate_lines:
        candidate_lines = "(no candidates available)"

    return (
        f"You are a restaurant recommendation assistant. "
        f"Choose exactly ONE restaurant from the candidate list below.\n\n"
        f"User: {request.username}\n"
        f"Dining profile:\n"
        f"- Total restaurants visited: {request.total_visited}\n"
        f"- Favourite cuisine: {top_cuisine}\n"
        f"- Average rating given: {avg_rating}\n\n"
        f"Candidate restaurants (all in Israel — choose ONLY from this list):\n"
        f"{candidate_lines}\n\n"
        f"Rules:\n"
        f"- You MUST choose exactly one restaurant from the candidate list above\n"
        f"- Do NOT invent or suggest any restaurant not in the candidate list\n"
        f"- Do NOT recommend any restaurant the user has already visited\n\n"
        f'Return a JSON object with exactly these keys: "restaurant_name", "city", "reason". '
        f"Use the exact restaurant name and city as they appear in the candidate list. "
        f"The reason should be one sentence tailored to the user's profile."
    )


def _parse_response(text: str) -> RecommendResponse:
    text = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
    data = json.loads(text)
    return RecommendResponse(
        restaurant_name=data["restaurant_name"],
        city=data["city"],
        reason=data["reason"],
    )


def _is_valid_candidate(result: RecommendResponse, request: RecommendRequest) -> bool:
    """Return True if Gemini's pick is actually in the candidate list."""
    if not request.candidate_restaurants:
        return False
    candidate_names_lower = {c.name.lower() for c in request.candidate_restaurants}
    return result.restaurant_name.lower() in candidate_names_lower


def get_recommendation(request: RecommendRequest) -> RecommendResponse:
    if not request.candidate_restaurants:
        return _fallback(request)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY not set — using fallback recommendation")
        return _fallback(request)

    try:
        client = genai.Client(api_key=api_key)
        prompt = _build_prompt(request)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        result = _parse_response(response.text)
        if not _is_valid_candidate(result, request):
            logger.warning(
                "Gemini returned %r which is not in the candidate list — using fallback",
                result.restaurant_name,
            )
            return _fallback(request)
        return result
    except Exception as exc:
        logger.error("Gemini call failed (%s: %s) — using fallback", type(exc).__name__, exc)
        return _fallback(request)
