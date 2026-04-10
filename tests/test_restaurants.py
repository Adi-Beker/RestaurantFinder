def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "Restaurant Finder"


def test_create_restaurant_returns_201_and_payload(client):
    response = client.post(
        "/restaurants",
        json={
            "name": "La Piazza",
            "city": "tel aviv",
            "country": "israel",
            "cuisine": "italian",
            "price_level": 3,
            "rating": 4.5,
            "is_open": True
        },
    )

    assert response.status_code == 201
    payload = response.json()

    assert payload["id"] == 1
    assert payload["name"] == "La Piazza"
    assert payload["city"] == "Tel Aviv"
    assert payload["country"] == "Israel"
    assert payload["cuisine"] == "Italian"
    assert payload["price_level"] == 3
    assert payload["rating"] == 4.5
    assert payload["is_open"] is True


def test_list_restaurants_returns_empty_list_initially(client):
    response = client.get("/restaurants")
    assert response.status_code == 200
    assert response.json() == []


def test_list_restaurants_returns_created_restaurant(client):
    client.post(
        "/restaurants",
        json={
            "name": "La Piazza",
            "city": "Tel Aviv",
            "country": "Israel",
            "cuisine": "Italian",
            "price_level": 3,
            "rating": 4.5,
            "is_open": True
        },
    )

    response = client.get("/restaurants")
    assert response.status_code == 200

    restaurants = response.json()
    assert len(restaurants) == 1
    assert restaurants[0]["name"] == "La Piazza"


def test_get_restaurant_by_id(client):
    create_response = client.post(
        "/restaurants",
        json={
            "name": "Tokyo Table",
            "city": "Tokyo",
            "country": "Japan",
            "cuisine": "Japanese",
            "price_level": 4,
            "rating": 4.8,
            "is_open": True
        },
    )

    restaurant_id = create_response.json()["id"]

    response = client.get(f"/restaurants/{restaurant_id}")
    assert response.status_code == 200

    restaurant = response.json()
    assert restaurant["id"] == restaurant_id
    assert restaurant["name"] == "Tokyo Table"


def test_get_missing_restaurant_returns_404(client):
    response = client.get("/restaurants/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Restaurant not found"


def test_update_restaurant(client):
    create_response = client.post(
        "/restaurants",
        json={
            "name": "La Piazza",
            "city": "Tel Aviv",
            "country": "Israel",
            "cuisine": "Italian",
            "price_level": 3,
            "rating": 4.5,
            "is_open": True
        },
    )

    restaurant_id = create_response.json()["id"]

    update_response = client.put(
        f"/restaurants/{restaurant_id}",
        json={
            "name": "La Piazza Updated",
            "city": "Haifa",
            "country": "Israel",
            "cuisine": "Italian",
            "price_level": 4,
            "rating": 4.7,
            "is_open": False
        },
    )

    assert update_response.status_code == 200
    updated_restaurant = update_response.json()

    assert updated_restaurant["id"] == restaurant_id
    assert updated_restaurant["name"] == "La Piazza Updated"
    assert updated_restaurant["city"] == "Haifa"
    assert updated_restaurant["price_level"] == 4
    assert updated_restaurant["rating"] == 4.7
    assert updated_restaurant["is_open"] is False


def test_update_missing_restaurant_returns_404(client):
    response = client.put(
        "/restaurants/999",
        json={
            "name": "Unknown",
            "city": "Paris",
            "country": "France",
            "cuisine": "French",
            "price_level": 3,
            "rating": 4.0,
            "is_open": True
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Restaurant not found"


def test_delete_restaurant(client):
    create_response = client.post(
        "/restaurants",
        json={
            "name": "Ocean View",
            "city": "Eilat",
            "country": "Israel",
            "cuisine": "Seafood",
            "price_level": 4,
            "rating": 4.6,
            "is_open": True
        },
    )

    restaurant_id = create_response.json()["id"]

    delete_response = client.delete(f"/restaurants/{restaurant_id}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/restaurants/{restaurant_id}")
    assert get_response.status_code == 404


def test_delete_missing_restaurant_returns_404(client):
    response = client.delete("/restaurants/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Restaurant not found"


def test_create_restaurant_rejects_invalid_price_level(client):
    response = client.post(
        "/restaurants",
        json={
            "name": "Cheap Eats",
            "city": "Beer Sheva",
            "country": "Israel",
            "cuisine": "Street Food",
            "price_level": 10,
            "rating": 4.0,
            "is_open": True
        },
    )

    assert response.status_code == 422


def test_create_restaurant_rejects_invalid_rating(client):
    response = client.post(
        "/restaurants",
        json={
            "name": "Bad Rating Place",
            "city": "Jerusalem",
            "country": "Israel",
            "cuisine": "Middle Eastern",
            "price_level": 3,
            "rating": 6.0,
            "is_open": True
        },
    )

    assert response.status_code == 422


def test_create_restaurant_rejects_missing_name(client):
    response = client.post(
        "/restaurants",
        json={
            "city": "Tel Aviv",
            "country": "Israel",
            "cuisine": "Italian",
            "price_level": 3,
            "rating": 4.5,
            "is_open": True
        },
    )

    assert response.status_code == 422