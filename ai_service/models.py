from __future__ import annotations

from pydantic import BaseModel


class CandidateRestaurant(BaseModel):
    name: str
    city: str
    cuisine: str


class RecommendRequest(BaseModel):
    username: str
    top_cuisine: str | None = None
    avg_rating: float | None = None
    total_visited: int = 0
    visited_names: list[str] = []
    excluded_names: list[str] = []
    candidate_restaurants: list[CandidateRestaurant] = []


class RecommendResponse(BaseModel):
    restaurant_name: str
    city: str
    reason: str
