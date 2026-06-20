"""Tests for POST /token login rate limiting."""


def _register(client, username: str = "adi", password: str = "secret") -> None:
    client.post("/auth/register", json={"username": username, "password": password})


def test_login_succeeds_within_rate_limit(client):
    _register(client)
    for _ in range(10):
        response = client.post("/token", data={"username": "adi", "password": "secret"})
        assert response.status_code == 200


def test_login_returns_429_after_10_attempts(client):
    _register(client)
    for _ in range(10):
        client.post("/token", data={"username": "adi", "password": "secret"})

    response = client.post("/token", data={"username": "adi", "password": "secret"})
    assert response.status_code == 429
    assert "Too many login attempts" in response.json()["detail"]
    assert response.headers["Retry-After"] == "60"


def test_failed_attempts_also_count_toward_rate_limit(client):
    _register(client)
    # 10 failed attempts
    for _ in range(10):
        client.post("/token", data={"username": "adi", "password": "wrongpass"})

    # 11th attempt (correct credentials) is still rate-limited
    response = client.post("/token", data={"username": "adi", "password": "secret"})
    assert response.status_code == 429


def test_rate_limit_is_isolated_per_test(client):
    # Each test gets a fresh fakeredis, so the counter starts at zero here.
    _register(client)
    response = client.post("/token", data={"username": "adi", "password": "secret"})
    assert response.status_code == 200
