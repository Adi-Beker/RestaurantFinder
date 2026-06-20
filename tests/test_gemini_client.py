"""Unit tests for ai_service.gemini_client — no live Gemini calls."""
from ai_service.models import CandidateRestaurant, RecommendRequest


# ── Helpers ───────────────────────────────────────────────────────────────────

_CANDIDATES = [
    CandidateRestaurant(name="HaBasta", city="Tel Aviv", cuisine="Israeli"),
    CandidateRestaurant(name="Machneyuda", city="Jerusalem", cuisine="Israeli"),
    CandidateRestaurant(name="Toto", city="Tel Aviv", cuisine="Italian"),
    CandidateRestaurant(name="Fattoush", city="Haifa", cuisine="Arab-Israeli"),
]


def _req(**kwargs) -> RecommendRequest:
    defaults = {
        "username": "adi",
        "top_cuisine": "Israeli",
        "avg_rating": 4.5,
        "total_visited": 3,
        "candidate_restaurants": _CANDIDATES,
    }
    return RecommendRequest(**{**defaults, **kwargs})


def _mock_client(response_text: str):
    """Return a fake genai.Client whose generate_content returns response_text."""
    class _Response:
        text = response_text

    class _Models:
        def generate_content(self, model, contents, config=None):
            return _Response()

    class _Client:
        models = _Models()

    return _Client()


# ── Fallback behaviour ────────────────────────────────────────────────────────

def test_fallback_picks_from_candidate_list(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    from ai_service.gemini_client import get_recommendation
    result = get_recommendation(_req())

    candidate_names = {c.name for c in _CANDIDATES}
    assert result.restaurant_name in candidate_names


def test_fallback_prefers_matching_cuisine(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    from ai_service.gemini_client import get_recommendation
    result = get_recommendation(_req(top_cuisine="Italian"))

    assert result.restaurant_name == "Toto"
    assert result.city == "Tel Aviv"


def test_fallback_picks_from_all_candidates_when_no_cuisine_match(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    from ai_service.gemini_client import get_recommendation
    result = get_recommendation(_req(top_cuisine="Mexican"))

    candidate_names = {c.name for c in _CANDIDATES}
    assert result.restaurant_name in candidate_names


def test_fallback_returns_graceful_message_when_no_candidates(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    from ai_service.gemini_client import get_recommendation
    result = get_recommendation(_req(candidate_restaurants=[]))

    assert result.restaurant_name == ""
    assert "catalogue" in result.reason.lower() or "explored" in result.reason.lower()


def test_falls_back_when_api_key_missing(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    from ai_service.gemini_client import get_recommendation
    result = get_recommendation(_req(top_cuisine="Israeli"))

    candidate_names = {c.name for c in _CANDIDATES}
    assert result.restaurant_name in candidate_names


def test_falls_back_on_gemini_exception(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    class _BrokenClient:
        class models:
            @staticmethod
            def generate_content(**kwargs):
                raise RuntimeError("network error")

    monkeypatch.setattr("ai_service.gemini_client.genai.Client", lambda api_key: _BrokenClient())

    from ai_service.gemini_client import get_recommendation
    result = get_recommendation(_req())

    candidate_names = {c.name for c in _CANDIDATES}
    assert result.restaurant_name in candidate_names


def test_falls_back_on_malformed_json(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        "ai_service.gemini_client.genai.Client",
        lambda api_key: _mock_client("not valid json at all"),
    )

    from ai_service.gemini_client import get_recommendation
    result = get_recommendation(_req())

    candidate_names = {c.name for c in _CANDIDATES}
    assert result.restaurant_name in candidate_names


def test_falls_back_on_missing_json_keys(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        "ai_service.gemini_client.genai.Client",
        lambda api_key: _mock_client('{"restaurant_name": "X", "reason": "Y"}'),
    )

    from ai_service.gemini_client import get_recommendation
    result = get_recommendation(_req())

    candidate_names = {c.name for c in _CANDIDATES}
    assert result.restaurant_name in candidate_names


def test_falls_back_with_zero_restaurants(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    from ai_service.gemini_client import get_recommendation
    result = get_recommendation(_req(total_visited=0))

    candidate_names = {c.name for c in _CANDIDATES}
    assert result.restaurant_name in candidate_names


# ── Gemini result validation ──────────────────────────────────────────────────

def test_gemini_result_not_in_candidate_list_triggers_fallback(monkeypatch):
    """If Gemini returns a restaurant not in the candidate list, fallback is used."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    outside_candidate = '{"restaurant_name": "Noma", "city": "Copenhagen", "reason": "Great."}'
    monkeypatch.setattr(
        "ai_service.gemini_client.genai.Client",
        lambda api_key: _mock_client(outside_candidate),
    )

    from ai_service.gemini_client import get_recommendation
    result = get_recommendation(_req())

    candidate_names = {c.name for c in _CANDIDATES}
    assert result.restaurant_name in candidate_names
    assert result.restaurant_name != "Noma"


def test_gemini_valid_candidate_is_returned(monkeypatch):
    """If Gemini returns a name that is in the candidate list, it passes validation."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    valid_response = '{"restaurant_name": "Machneyuda", "city": "Jerusalem", "reason": "Excellent Israeli cuisine."}'
    monkeypatch.setattr(
        "ai_service.gemini_client.genai.Client",
        lambda api_key: _mock_client(valid_response),
    )

    from ai_service.gemini_client import get_recommendation
    result = get_recommendation(_req())

    assert result.restaurant_name == "Machneyuda"
    assert result.city == "Jerusalem"


def test_returns_gemini_recommendation(monkeypatch):
    payload = '{"restaurant_name": "HaBasta", "city": "Tel Aviv", "reason": "Classic Israeli excellence."}'
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr("ai_service.gemini_client.genai.Client", lambda api_key: _mock_client(payload))

    from ai_service.gemini_client import get_recommendation
    result = get_recommendation(_req())

    assert result.restaurant_name == "HaBasta"
    assert result.city == "Tel Aviv"
    assert result.reason == "Classic Israeli excellence."


def test_strips_markdown_code_fences(monkeypatch):
    payload = '```json\n{"restaurant_name": "HaBasta", "city": "Tel Aviv", "reason": "Fits your profile."}\n```'
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr("ai_service.gemini_client.genai.Client", lambda api_key: _mock_client(payload))

    from ai_service.gemini_client import get_recommendation
    result = get_recommendation(_req())

    assert result.restaurant_name == "HaBasta"


# ── Prompt structure ──────────────────────────────────────────────────────────

def test_prompt_includes_candidate_list():
    from ai_service.gemini_client import _build_prompt

    prompt = _build_prompt(_req())

    for candidate in _CANDIDATES:
        assert candidate.name in prompt


def test_prompt_enforces_candidate_only_rule():
    from ai_service.gemini_client import _build_prompt

    prompt = _build_prompt(_req())

    assert "ONLY from this list" in prompt or "only from this list" in prompt.lower()
    assert "Do NOT invent" in prompt


def test_prompt_has_no_candidates_placeholder_when_empty():
    from ai_service.gemini_client import _build_prompt

    prompt = _build_prompt(_req(candidate_restaurants=[]))

    assert "no candidates available" in prompt.lower()


# ── Randomness ────────────────────────────────────────────────────────────────

def test_fallback_uses_random_choice(monkeypatch):
    """Fallback must use random.choice, not always pick the first candidate."""
    import random as _random

    chosen_args = []
    original_choice = _random.choice

    def _tracking_choice(seq):
        chosen_args.append(list(seq))
        return original_choice(seq)

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr("ai_service.gemini_client.random.choice", _tracking_choice)

    from ai_service.gemini_client import get_recommendation
    get_recommendation(_req())

    assert len(chosen_args) == 1
    assert len(chosen_args[0]) > 0


def test_fallback_does_not_always_return_same_item(monkeypatch):
    """Running the fallback many times with multiple same-cuisine candidates produces varied results."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    many_israeli = [
        CandidateRestaurant(name=f"Restaurant{i}", city="Tel Aviv", cuisine="Israeli")
        for i in range(8)
    ]

    from ai_service.gemini_client import get_recommendation
    results = {get_recommendation(_req(candidate_restaurants=many_israeli)).restaurant_name for _ in range(30)}

    # With 8 candidates and 30 draws, it's astronomically unlikely to always pick the same one
    assert len(results) > 1
