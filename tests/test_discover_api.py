"""Tests for GET /discover/cities and GET /discover/restaurants."""
from app.discover_seed import SEED_RESTAURANTS


def test_discover_cities_requires_auth(client):
    resp = client.get("/discover/cities")
    assert resp.status_code == 401


def test_discover_restaurants_requires_auth(client):
    resp = client.get("/discover/restaurants")
    assert resp.status_code == 401


def test_discover_cities_returns_all_seeded_cities(auth_client):
    resp = auth_client.get("/discover/cities")
    assert resp.status_code == 200
    cities = resp.json()
    assert cities == ["Ashdod", "Haifa", "Jerusalem", "Tel Aviv"]


def test_discover_cities_are_sorted(auth_client):
    resp = auth_client.get("/discover/cities")
    cities = resp.json()
    assert cities == sorted(cities)


def test_discover_restaurants_returns_all_seeded_rows(auth_client):
    resp = auth_client.get("/discover/restaurants")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == len(SEED_RESTAURANTS)


def test_discover_restaurants_city_filter(auth_client):
    resp = auth_client.get("/discover/restaurants?city=Tel+Aviv")
    assert resp.status_code == 200
    data = resp.json()
    tel_aviv_count = sum(1 for r in SEED_RESTAURANTS if r["city"] == "Tel Aviv")
    assert len(data) == tel_aviv_count
    assert all(r["city"] == "Tel Aviv" for r in data)


def test_discover_restaurants_city_filter_jerusalem(auth_client):
    resp = auth_client.get("/discover/restaurants?city=Jerusalem")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    assert all(r["city"] == "Jerusalem" for r in data)


def test_discover_restaurants_unknown_city_returns_empty(auth_client):
    resp = auth_client.get("/discover/restaurants?city=Atlantis")
    assert resp.status_code == 200
    assert resp.json() == []


def test_discover_restaurant_shape(auth_client):
    resp = auth_client.get("/discover/restaurants?city=Tel+Aviv")
    row = resp.json()[0]
    assert "id" in row
    assert "osm_id" in row
    assert row["osm_id"].startswith("seed-")
    assert "name" in row
    assert "city" in row
    assert "country" in row
    assert row["country"] == "Israel"
    assert "cuisine" in row
    assert "address" in row
    assert "lat" in row
    assert "lon" in row
    assert "price_level" in row
    assert "rating" in row
    assert "is_open" in row


def test_discover_restaurants_is_open_is_boolean(auth_client):
    # SQLite stores is_open as INTEGER; verify it reaches the client as a JSON boolean.
    resp = auth_client.get("/discover/restaurants?city=Tel+Aviv")
    data = resp.json()
    assert len(data) > 0
    assert isinstance(data[0]["is_open"], bool)


def test_discover_restaurants_haifa_filter(auth_client):
    resp = auth_client.get("/discover/restaurants?city=Haifa")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    assert all(r["city"] == "Haifa" for r in data)


def test_discover_restaurants_ashdod_filter(auth_client):
    resp = auth_client.get("/discover/restaurants?city=Ashdod")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    assert all(r["city"] == "Ashdod" for r in data)


def test_discover_restaurants_without_filter_spans_multiple_cities(auth_client):
    resp = auth_client.get("/discover/restaurants")
    data = resp.json()
    cities_present = {r["city"] for r in data}
    assert len(cities_present) > 1


def test_discover_restaurants_country_always_israel(auth_client):
    resp = auth_client.get("/discover/restaurants")
    data = resp.json()
    assert len(data) > 0
    assert all(r["country"] == "Israel" for r in data)
