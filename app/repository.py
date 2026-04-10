from __future__ import annotations

from typing import Dict

from app.models import Restaurant, RestaurantCreate


class RestaurantRepository:
    """In-memory storage for restaurants."""

    def __init__(self) -> None:
        self._items: Dict[int, Restaurant] = {}
        self._next_id = 1

    def list(self) -> list[Restaurant]:
        """Return all restaurants."""
        return list(self._items.values())

    def create(self, payload: RestaurantCreate) -> Restaurant:
        """Create a new restaurant and return it."""
        restaurant = Restaurant(id=self._next_id, **payload.model_dump())
        self._items[restaurant.id] = restaurant
        self._next_id += 1
        return restaurant

    def get(self, restaurant_id: int) -> Restaurant | None:
        """Return a restaurant by ID, or None if not found."""
        return self._items.get(restaurant_id)

    def update(self, restaurant_id: int, payload: RestaurantCreate) -> Restaurant | None:
        """Update an existing restaurant and return it, or None if not found."""
        existing_restaurant = self.get(restaurant_id)
        if existing_restaurant is None:
            return None

        updated_restaurant = Restaurant(id=restaurant_id, **payload.model_dump())
        self._items[restaurant_id] = updated_restaurant
        return updated_restaurant

    def delete(self, restaurant_id: int) -> bool:
        """Delete a restaurant by ID. Return True if deleted, otherwise False."""
        if restaurant_id in self._items:
            del self._items[restaurant_id]
            return True
        return False

    def clear(self) -> None:
        """Remove all restaurants. Useful for tests."""
        self._items.clear()
        self._next_id = 1