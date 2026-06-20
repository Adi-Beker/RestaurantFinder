from __future__ import annotations

import sqlite3

from app.models import DiscoverRestaurant


def get_cities(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT DISTINCT city FROM discover_restaurants ORDER BY city ASC"
    ).fetchall()
    return [row["city"] for row in rows]


def get_discover_restaurants(
    conn: sqlite3.Connection, city: str | None = None
) -> list[DiscoverRestaurant]:
    if city is not None:
        rows = conn.execute(
            "SELECT * FROM discover_restaurants WHERE city = ? ORDER BY name ASC",
            (city,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM discover_restaurants ORDER BY city ASC, name ASC"
        ).fetchall()
    return [
        DiscoverRestaurant(
            id=row["id"],
            osm_id=row["osm_id"],
            name=row["name"],
            city=row["city"],
            country=row["country"],
            cuisine=row["cuisine"],
            address=row["address"],
            lat=row["lat"],
            lon=row["lon"],
            price_level=row["price_level"],
            rating=row["rating"],
            is_open=bool(row["is_open"]),
        )
        for row in rows
    ]
