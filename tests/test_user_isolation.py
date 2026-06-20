"""Tests that restaurant data is scoped to the owning user."""

_PIZZA = {
    "name": "La Piazza",
    "city": "Tel Aviv",
    "country": "Israel",
    "cuisine": "Italian",
    "price_level": 3,
    "rating": 4.5,
    "is_open": True,
}


def _login(client, username: str, password: str) -> dict[str, str]:
    """Register, log in, and return an Authorization header dict."""
    client.post("/auth/register", json={"username": username, "password": password})
    token = client.post("/token", data={"username": username, "password": password}).json()[
        "access_token"
    ]
    return {"Authorization": f"Bearer {token}"}


def test_user_b_cannot_see_user_a_restaurant(client):
    headers_a = _login(client, "userA", "passA")
    headers_b = _login(client, "userB", "passB")

    r_id = client.post("/restaurants", headers=headers_a, json=_PIZZA).json()["id"]

    # user B's list is empty
    assert client.get("/restaurants", headers=headers_b).json() == []
    # user B cannot fetch by id
    assert client.get(f"/restaurants/{r_id}", headers=headers_b).status_code == 404


def test_user_b_cannot_update_user_a_restaurant(client):
    headers_a = _login(client, "userA", "passA")
    headers_b = _login(client, "userB", "passB")

    r_id = client.post("/restaurants", headers=headers_a, json=_PIZZA).json()["id"]

    response = client.put(
        f"/restaurants/{r_id}",
        headers=headers_b,
        json={**_PIZZA, "name": "Hijacked"},
    )
    assert response.status_code == 404

    # original is unchanged
    original = client.get(f"/restaurants/{r_id}", headers=headers_a).json()
    assert original["name"] == "La Piazza"


def test_user_b_cannot_delete_user_a_restaurant(client):
    headers_a = _login(client, "userA", "passA")
    headers_b = _login(client, "userB", "passB")

    r_id = client.post("/restaurants", headers=headers_a, json=_PIZZA).json()["id"]

    assert client.delete(f"/restaurants/{r_id}", headers=headers_b).status_code == 404
    # still exists for user A
    assert client.get(f"/restaurants/{r_id}", headers=headers_a).status_code == 200


def test_duplicate_prevention_still_works_for_same_user(client):
    headers = _login(client, "userA", "passA")

    client.post("/restaurants", headers=headers, json=_PIZZA)
    response = client.post("/restaurants", headers=headers, json=_PIZZA)

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_same_restaurant_allowed_for_different_users(client):
    headers_a = _login(client, "userA", "passA")
    headers_b = _login(client, "userB", "passB")

    assert client.post("/restaurants", headers=headers_a, json=_PIZZA).status_code == 201
    assert client.post("/restaurants", headers=headers_b, json=_PIZZA).status_code == 201
