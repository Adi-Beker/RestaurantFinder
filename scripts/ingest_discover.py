"""CLI to ingest restaurant data from the Overpass API into discover_restaurants."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
import typer

from app.database import DB_PATH, get_connection

cli = typer.Typer(add_completion=False)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Bounding boxes: (south, west, north, east)
CITY_BBOXES: dict[str, tuple[float, float, float, float]] = {
    "Tel Aviv":  (32.03, 34.73, 32.12, 34.82),
    "Jerusalem": (31.74, 35.17, 31.83, 35.26),
    "Haifa":     (32.77, 34.96, 32.86, 35.05),
    "Ashdod":    (31.78, 34.62, 31.84, 34.68),
}


def fetch_restaurants(bbox: tuple[float, float, float, float]) -> list[dict]:
    """Query Overpass for restaurant nodes within bbox."""
    s, w, n, e = bbox
    query = f"[out:json][timeout:60];node[amenity=restaurant]({s},{w},{n},{e});out body;"
    resp = httpx.post(OVERPASS_URL, data={"data": query}, timeout=90.0)
    resp.raise_for_status()
    return resp.json().get("elements", [])


def normalize_element(element: dict, city: str) -> dict | None:
    """Convert a raw Overpass element to a discover_restaurants row.

    Returns None if the element has no usable name.
    """
    tags = element.get("tags") or {}

    name = (tags.get("name:en") or tags.get("name") or "").strip()
    if not name:
        return None

    cuisine = tags.get("cuisine", "").replace(";", "/").strip()

    street = tags.get("addr:street", "").strip()
    housenumber = tags.get("addr:housenumber", "").strip()
    if street and housenumber:
        address = f"{housenumber} {street}"
    elif street:
        address = street
    else:
        address = ""

    return {
        "osm_id": str(element["id"]),
        "name": name,
        "city": city,
        "country": "Israel",
        "cuisine": cuisine if cuisine else "Israeli",
        "address": address,
        "lat": float(element.get("lat", 0.0)),
        "lon": float(element.get("lon", 0.0)),
        "price_level": 3,
        "rating": 4.0,
        "is_open": 1,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


def upsert_restaurants(conn: sqlite3.Connection, rows: list[dict]) -> int:
    """Upsert rows into discover_restaurants. Returns the number of rows processed."""
    conn.executemany(
        """
        INSERT INTO discover_restaurants
            (osm_id, name, city, country, cuisine, address, lat, lon,
             price_level, rating, is_open, last_updated)
        VALUES
            (:osm_id, :name, :city, :country, :cuisine, :address, :lat, :lon,
             :price_level, :rating, :is_open, :last_updated)
        ON CONFLICT(osm_id) DO UPDATE SET
            name         = excluded.name,
            city         = excluded.city,
            country      = excluded.country,
            cuisine      = excluded.cuisine,
            address      = excluded.address,
            lat          = excluded.lat,
            lon          = excluded.lon,
            price_level  = excluded.price_level,
            rating       = excluded.rating,
            is_open      = excluded.is_open,
            last_updated = excluded.last_updated
        """,
        rows,
    )
    conn.commit()
    return len(rows)


@cli.command()
def main(
    db: Path = typer.Option(DB_PATH, "--db", help="Path to the SQLite database."),
    cities: Optional[list[str]] = typer.Option(
        None, "--city", help="City to ingest (repeatable). Defaults to all cities."
    ),
) -> None:
    """Ingest OSM restaurant data for Israeli cities into discover_restaurants."""
    targets = cities if cities else list(CITY_BBOXES.keys())

    conn = get_connection(db)
    total = 0

    for city in targets:
        if city not in CITY_BBOXES:
            typer.echo(
                f"[SKIP] Unknown city: '{city}'. Known: {', '.join(CITY_BBOXES)}",
                err=True,
            )
            continue
        try:
            typer.echo(f"[{city}] Fetching from Overpass…")
            elements = fetch_restaurants(CITY_BBOXES[city])
            rows = [r for e in elements if (r := normalize_element(e, city)) is not None]
            count = upsert_restaurants(conn, rows)
            typer.echo(f"[{city}] {len(elements)} elements → {count} upserted")
            total += count
        except Exception as exc:  # noqa: BLE001
            typer.echo(f"[{city}] ERROR: {exc}", err=True)

    typer.echo(f"Done. Total upserted: {total}")


if __name__ == "__main__":
    cli()
