"""Tests for GET /ai/recommendation."""
import pytest

from app.discover_seed import SEED_RESTAURANTS

_SEED_NAMES = {r["name"] for r in SEED_RESTAURANTS}
_SEED_CITIES = {r["city"] for r in SEED_RESTAURANTS}

_MOCK_RESPONSE = {
    "restaurant_name": "HaBasta",
    "city": "Tel Aviv",
    "reason": "Great match for your taste",
}

_RESTAURANT = {
    "name": "La Piazza",
    "city": "Tel Aviv",
    "country": "Israel",
    "cuisine": "Italian",
    "price_level": 3,
    "rating": 4.5,
    "is_open": True,
}


@pytest.fixture(autouse=True)
def mock_ai_client(monkeypatch):
    async def _fake(username, summary, visited_names=None, excluded_names=None, candidate_restaurants=None):
        return _MOCK_RESPONSE

    monkeypatch.setattr("app.main.get_recommendation", _fake)


def test_ai_recommendation_requires_auth(client):
    resp = client.get("/ai/recommendation")
    assert resp.status_code == 401


def test_ai_recommendation_returns_200(auth_client):
    resp = auth_client.get("/ai/recommendation")
    assert resp.status_code == 200
    data = resp.json()
    assert data["restaurant_name"] == "HaBasta"
    assert data["city"] == "Tel Aviv"
    assert data["reason"] == "Great match for your taste"


def test_ai_recommendation_with_no_restaurants(auth_client, monkeypatch):
    captured = {}

    async def _capture(username, summary, visited_names=None, excluded_names=None, candidate_restaurants=None):
        captured["summary"] = summary
        captured["visited_names"] = visited_names or []
        return _MOCK_RESPONSE

    monkeypatch.setattr("app.main.get_recommendation", _capture)
    auth_client.get("/ai/recommendation")

    assert captured["summary"]["total_visited"] == 0
    assert captured["summary"]["top_cuisine"] is None
    assert captured["visited_names"] == []


def test_ai_recommendation_passes_correct_summary(auth_client, monkeypatch):
    captured = {}

    async def _capture(username, summary, visited_names=None, excluded_names=None, candidate_restaurants=None):
        captured["username"] = username
        captured["summary"] = summary
        return _MOCK_RESPONSE

    monkeypatch.setattr("app.main.get_recommendation", _capture)
    auth_client.post("/restaurants", json=_RESTAURANT)
    auth_client.get("/ai/recommendation")

    assert captured["summary"]["total_visited"] == 1
    assert captured["summary"]["top_cuisine"] == "Italian"
    assert captured["username"] == "testuser"


def test_ai_recommendation_passes_correct_avg_rating(auth_client, monkeypatch):
    captured = {}

    async def _capture(username, summary, visited_names=None, excluded_names=None, candidate_restaurants=None):
        captured["summary"] = summary
        return _MOCK_RESPONSE

    monkeypatch.setattr("app.main.get_recommendation", _capture)
    auth_client.post("/restaurants", json={**_RESTAURANT, "rating": 4.0})
    auth_client.post("/restaurants", json={**_RESTAURANT, "name": "Another Place", "rating": 5.0})
    auth_client.get("/ai/recommendation")

    assert captured["summary"]["avg_rating"] == 4.5
    assert captured["summary"]["total_visited"] == 2


def test_ai_recommendation_passes_visited_names(auth_client, monkeypatch):
    captured = {}

    async def _capture(username, summary, visited_names=None, excluded_names=None, candidate_restaurants=None):
        captured["visited_names"] = visited_names or []
        return _MOCK_RESPONSE

    monkeypatch.setattr("app.main.get_recommendation", _capture)
    auth_client.post("/restaurants", json=_RESTAURANT)
    auth_client.post("/restaurants", json={**_RESTAURANT, "name": "Sushi Place"})
    auth_client.get("/ai/recommendation")

    assert "La Piazza" in captured["visited_names"]
    assert "Sushi Place" in captured["visited_names"]


def test_ai_recommendation_candidates_come_from_discover_catalogue(auth_client, monkeypatch):
    """Candidates passed to get_recommendation must all be from the discover catalogue."""
    captured = {}

    async def _capture(username, summary, visited_names=None, excluded_names=None, candidate_restaurants=None):
        captured["candidates"] = candidate_restaurants or []
        return _MOCK_RESPONSE

    monkeypatch.setattr("app.main.get_recommendation", _capture)
    auth_client.get("/ai/recommendation")

    assert len(captured["candidates"]) > 0
    candidate_names = {c["name"] for c in captured["candidates"]}
    assert candidate_names.issubset(_SEED_NAMES)


def test_ai_recommendation_candidates_are_all_in_israel(auth_client, monkeypatch):
    """Every candidate must be an Israeli city."""
    captured = {}

    async def _capture(username, summary, visited_names=None, excluded_names=None, candidate_restaurants=None):
        captured["candidates"] = candidate_restaurants or []
        return _MOCK_RESPONSE

    monkeypatch.setattr("app.main.get_recommendation", _capture)
    auth_client.get("/ai/recommendation")

    for c in captured["candidates"]:
        assert c["city"] in _SEED_CITIES, f"{c['city']} is not an Israeli city in the catalogue"


def test_ai_recommendation_candidates_exclude_visited(auth_client, monkeypatch):
    """A restaurant the user has visited must not appear in the candidate list."""
    captured = {}

    async def _capture(username, summary, visited_names=None, excluded_names=None, candidate_restaurants=None):
        captured["candidates"] = candidate_restaurants or []
        return _MOCK_RESPONSE

    monkeypatch.setattr("app.main.get_recommendation", _capture)

    # Add "HaBasta" (a seed restaurant) to the visited list
    auth_client.post("/restaurants", json={
        "name": "HaBasta", "city": "Tel Aviv", "country": "Israel",
        "cuisine": "Israeli", "price_level": 3, "rating": 4.7, "is_open": True,
    })
    auth_client.get("/ai/recommendation")

    candidate_names = [c["name"] for c in captured["candidates"]]
    assert "HaBasta" not in candidate_names


def test_ai_recommendation_candidates_exclude_excluded_param(auth_client, monkeypatch):
    """?exclude=Name must remove that restaurant from the candidate list."""
    captured = {}

    async def _capture(username, summary, visited_names=None, excluded_names=None, candidate_restaurants=None):
        captured["candidates"] = candidate_restaurants or []
        return _MOCK_RESPONSE

    monkeypatch.setattr("app.main.get_recommendation", _capture)
    auth_client.get("/ai/recommendation?exclude=Toto")

    candidate_names = [c["name"] for c in captured["candidates"]]
    assert "Toto" not in candidate_names


def test_ai_recommendation_exclude_param_forwarded(auth_client, monkeypatch):
    captured = {}

    async def _capture(username, summary, visited_names=None, excluded_names=None, candidate_restaurants=None):
        captured["excluded_names"] = excluded_names or []
        return _MOCK_RESPONSE

    monkeypatch.setattr("app.main.get_recommendation", _capture)
    auth_client.get("/ai/recommendation?exclude=Mock+Bistro")

    assert "Mock Bistro" in captured["excluded_names"]


def test_ai_recommendation_no_exclude_param_gives_empty_excluded(auth_client, monkeypatch):
    captured = {}

    async def _capture(username, summary, visited_names=None, excluded_names=None, candidate_restaurants=None):
        captured["excluded_names"] = excluded_names or []
        return _MOCK_RESPONSE

    monkeypatch.setattr("app.main.get_recommendation", _capture)
    auth_client.get("/ai/recommendation")

    assert captured["excluded_names"] == []


def test_ai_recommendation_returns_graceful_message_when_no_candidates(auth_client, monkeypatch):
    """When all catalogue restaurants are visited, return a graceful no-more-restaurants response."""
    from app.discover_seed import SEED_RESTAURANTS as seeds

    async def _should_not_be_called(*args, **kwargs):
        raise AssertionError("get_recommendation should not be called when no candidates remain")

    monkeypatch.setattr("app.main.get_recommendation", _should_not_be_called)

    # Visit every seed restaurant
    for seed in seeds:
        auth_client.post("/restaurants", json={
            "name": seed["name"],
            "city": seed["city"],
            "country": "Israel",
            "cuisine": seed["cuisine"],
            "price_level": seed["price_level"],
            "rating": seed["rating"],
            "is_open": True,
        })

    resp = auth_client.get("/ai/recommendation")
    assert resp.status_code == 200
    data = resp.json()
    assert "catalogue" in data["reason"].lower() or "explored" in data["reason"].lower()


def test_ai_recommendation_accepts_multiple_exclude_params(auth_client, monkeypatch):
    """Multiple ?exclude= params must all be removed from the candidate list."""
    captured = {}

    async def _capture(username, summary, visited_names=None, excluded_names=None, candidate_restaurants=None):
        captured["candidates"] = candidate_restaurants or []
        captured["excluded_names"] = excluded_names or []
        return _MOCK_RESPONSE

    monkeypatch.setattr("app.main.get_recommendation", _capture)
    auth_client.get("/ai/recommendation?exclude=Toto&exclude=HaBasta&exclude=Machneyuda")

    candidate_names = [c["name"] for c in captured["candidates"]]
    assert "Toto" not in candidate_names
    assert "HaBasta" not in candidate_names
    assert "Machneyuda" not in candidate_names
    assert "Toto" in captured["excluded_names"]
    assert "HaBasta" in captured["excluded_names"]
    assert "Machneyuda" in captured["excluded_names"]


def test_ai_recommendation_ask_again_exclusions_grow(auth_client, monkeypatch):
    """Simulates Ask Again: each successive call with an expanded exclude list removes more candidates."""
    captured_calls = []

    async def _capture(username, summary, visited_names=None, excluded_names=None, candidate_restaurants=None):
        captured_calls.append({
            "candidates": [c["name"] for c in (candidate_restaurants or [])],
            "excluded": excluded_names or [],
        })
        return _MOCK_RESPONSE

    monkeypatch.setattr("app.main.get_recommendation", _capture)

    # First call — no exclusions
    auth_client.get("/ai/recommendation")
    # Second call — exclude HaBasta (simulates "Ask again" after seeing HaBasta)
    auth_client.get("/ai/recommendation?exclude=HaBasta")
    # Third call — exclude HaBasta and Toto (accumulated)
    auth_client.get("/ai/recommendation?exclude=HaBasta&exclude=Toto")

    assert len(captured_calls) == 3
    assert "HaBasta" not in captured_calls[1]["candidates"]
    assert "HaBasta" not in captured_calls[2]["candidates"]
    assert "Toto" not in captured_calls[2]["candidates"]
    assert len(captured_calls[0]["candidates"]) > len(captured_calls[2]["candidates"])


def test_ai_recommendation_candidates_are_shuffled(auth_client, monkeypatch):
    """Candidates must be shuffled so the same ordering is not always sent to ai_service."""
    import random as _random

    shuffle_calls = []
    original_shuffle = _random.shuffle

    def _tracking_shuffle(lst):
        shuffle_calls.append(True)
        return original_shuffle(lst)

    monkeypatch.setattr("app.main.random.shuffle", _tracking_shuffle)

    async def _capture(username, summary, visited_names=None, excluded_names=None, candidate_restaurants=None):
        return _MOCK_RESPONSE

    monkeypatch.setattr("app.main.get_recommendation", _capture)
    auth_client.get("/ai/recommendation")

    assert len(shuffle_calls) == 1
