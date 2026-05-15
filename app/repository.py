from __future__ import annotations

import sqlite3

from app.models import Restaurant, RestaurantCreate


class RestaurantRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    # ── Queries ──────────────────────────────────────────────────────────────

    def list(self) -> list[Restaurant]:
        rows = self._conn.execute(
            "SELECT * FROM restaurants ORDER BY id"
        ).fetchall()
        return [_to_restaurant(row) for row in rows]

    def get(self, restaurant_id: int) -> Restaurant | None:
        row = self._conn.execute(
            "SELECT * FROM restaurants WHERE id = ?", (restaurant_id,)
        ).fetchone()
        return _to_restaurant(row) if row else None

    def create(self, payload: RestaurantCreate) -> Restaurant:
        if self._is_duplicate(payload.name, payload.city, payload.country):
            raise ValueError("Restaurant already exists in your visited list")

        cursor = self._conn.execute(
            """
            INSERT INTO restaurants (name, city, country, cuisine, price_level, rating, is_open)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.name,
                payload.city,
                payload.country,
                payload.cuisine,
                payload.price_level,
                payload.rating,
                int(payload.is_open),
            ),
        )
        self._conn.commit()
        row = self._conn.execute(
            "SELECT * FROM restaurants WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        return _to_restaurant(row)

    def update(self, restaurant_id: int, payload: RestaurantCreate) -> Restaurant | None:
        if self.get(restaurant_id) is None:
            return None

        if self._is_duplicate(payload.name, payload.city, payload.country, exclude_id=restaurant_id):
            raise ValueError("Restaurant already exists in your visited list")

        self._conn.execute(
            """
            UPDATE restaurants
               SET name=?, city=?, country=?, cuisine=?, price_level=?, rating=?, is_open=?
             WHERE id=?
            """,
            (
                payload.name,
                payload.city,
                payload.country,
                payload.cuisine,
                payload.price_level,
                payload.rating,
                int(payload.is_open),
                restaurant_id,
            ),
        )
        self._conn.commit()
        return self.get(restaurant_id)

    def delete(self, restaurant_id: int) -> bool:
        cursor = self._conn.execute(
            "DELETE FROM restaurants WHERE id = ?", (restaurant_id,)
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def clear(self) -> None:
        """Delete all rows. Used by tests to reset state between runs."""
        self._conn.execute("DELETE FROM restaurants")
        self._conn.commit()

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _is_duplicate(
        self,
        name: str,
        city: str,
        country: str,
        exclude_id: int | None = None,
    ) -> bool:
        """Return True if a restaurant with the same name/city/country exists."""
        if exclude_id is None:
            row = self._conn.execute(
                """
                SELECT 1 FROM restaurants
                 WHERE LOWER(name)    = LOWER(?)
                   AND LOWER(city)    = LOWER(?)
                   AND LOWER(country) = LOWER(?)
                """,
                (name, city, country),
            ).fetchone()
        else:
            row = self._conn.execute(
                """
                SELECT 1 FROM restaurants
                 WHERE LOWER(name)    = LOWER(?)
                   AND LOWER(city)    = LOWER(?)
                   AND LOWER(country) = LOWER(?)
                   AND id != ?
                """,
                (name, city, country, exclude_id),
            ).fetchone()
        return row is not None


def _to_restaurant(row: sqlite3.Row) -> Restaurant:
    return Restaurant(
        id=row["id"],
        name=row["name"],
        city=row["city"],
        country=row["country"],
        cuisine=row["cuisine"],
        price_level=row["price_level"],
        rating=row["rating"],
        is_open=bool(row["is_open"]),
    )
