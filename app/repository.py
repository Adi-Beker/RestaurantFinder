from __future__ import annotations

import sqlite3

from app.models import Restaurant, RestaurantCreate


class RestaurantRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    # ── Queries ──────────────────────────────────────────────────────────────

    def list(self, user_id: int) -> list[Restaurant]:
        rows = self._conn.execute(
            "SELECT * FROM restaurants WHERE user_id = ? ORDER BY id",
            (user_id,),
        ).fetchall()
        return [_to_restaurant(row) for row in rows]

    def get(self, restaurant_id: int, user_id: int) -> Restaurant | None:
        row = self._conn.execute(
            "SELECT * FROM restaurants WHERE id = ? AND user_id = ?",
            (restaurant_id, user_id),
        ).fetchone()
        return _to_restaurant(row) if row else None

    def create(self, payload: RestaurantCreate, user_id: int) -> Restaurant:
        if self._is_duplicate(payload.name, payload.city, payload.country, user_id):
            raise ValueError("Restaurant already exists in your visited list")

        cursor = self._conn.execute(
            """
            INSERT INTO restaurants
                (name, city, country, cuisine, price_level, rating, is_open, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.name,
                payload.city,
                payload.country,
                payload.cuisine,
                payload.price_level,
                payload.rating,
                int(payload.is_open),
                user_id,
            ),
        )
        self._conn.commit()
        row = self._conn.execute(
            "SELECT * FROM restaurants WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        return _to_restaurant(row)

    def update(
        self, restaurant_id: int, payload: RestaurantCreate, user_id: int
    ) -> Restaurant | None:
        if self.get(restaurant_id, user_id) is None:
            return None

        if self._is_duplicate(
            payload.name, payload.city, payload.country, user_id, exclude_id=restaurant_id
        ):
            raise ValueError("Restaurant already exists in your visited list")

        self._conn.execute(
            """
            UPDATE restaurants
               SET name=?, city=?, country=?, cuisine=?, price_level=?, rating=?, is_open=?
             WHERE id=? AND user_id=?
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
                user_id,
            ),
        )
        self._conn.commit()
        return self.get(restaurant_id, user_id)

    def delete(self, restaurant_id: int, user_id: int) -> bool:
        cursor = self._conn.execute(
            "DELETE FROM restaurants WHERE id = ? AND user_id = ?",
            (restaurant_id, user_id),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def clear(self) -> None:
        self._conn.execute("DELETE FROM restaurants")
        self._conn.commit()

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _is_duplicate(
        self,
        name: str,
        city: str,
        country: str,
        user_id: int,
        exclude_id: int | None = None,
    ) -> bool:
        if exclude_id is None:
            row = self._conn.execute(
                """
                SELECT 1 FROM restaurants
                 WHERE LOWER(name)    = LOWER(?)
                   AND LOWER(city)    = LOWER(?)
                   AND LOWER(country) = LOWER(?)
                   AND user_id = ?
                """,
                (name, city, country, user_id),
            ).fetchone()
        else:
            row = self._conn.execute(
                """
                SELECT 1 FROM restaurants
                 WHERE LOWER(name)    = LOWER(?)
                   AND LOWER(city)    = LOWER(?)
                   AND LOWER(country) = LOWER(?)
                   AND user_id = ?
                   AND id != ?
                """,
                (name, city, country, user_id, exclude_id),
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
