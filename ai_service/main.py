from __future__ import annotations

from fastapi import FastAPI

from ai_service.gemini_client import get_recommendation
from ai_service.models import RecommendRequest, RecommendResponse

app = FastAPI(title="AI Service", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai_service"}


@app.post("/recommend", response_model=RecommendResponse)
def recommend(payload: RecommendRequest) -> RecommendResponse:
    return get_recommendation(payload)
