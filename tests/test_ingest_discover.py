"""Unit tests for scripts/ingest_discover.py — no live Overpass calls."""
import sqlite3

import pytest

from scripts.ingest_discover import normalize_element, upsert_restaurants


# ── Helpers ───────────────────────────────────────────────────────────────────

def _el(osm_id: int = 123, lat: float = 32.0, lon: float = 34.7, **tags) -> dict:
    base = {"id": osm_id, "lat": lat, "lon": lon}
    if tags:
        base["tags"] = tags
    return base


# ── normalize_element ─────────────────────────────────────────────────────────

def test_name_en_preferred_over_name():
    result = normalize_element(_el(name="שם עברי", **{"name:en": "English Name"}), "Tel Aviv")
    assert result["name"] == "English Name"


def test_falls_back_to_name_when_no_name_en():
    result = normalize_element(_el(name="HaBasta"), "Tel Aviv")
    assert result["name"] == "HaBasta"


def test_returns_none_when_no_name():
    result = normalize_element(_el(cuisine="Italian"), "Tel Aviv")
    assert result is None


def test_returns_none_when_tags_missing_entirely():
    result = normalize_element({"id": 1, "lat": 32.0, "lon": 34.7}, "Tel Aviv")
    assert result is None


def test_returns_none_when_name_is_whitespace_only():
    result = normalize_element(_el(name="   "), "Tel Aviv")
    assert result is None


def test_address_built_from_street_and_housenumber():
    result = normalize_element(
        _el(name="Test", **{"addr:street": "Dizengoff St", "addr:housenumber": "50"}),
        "Tel Aviv",
    )
    assert result["address"] == "50 Dizengoff St"


def test_address_street_only_when_no_housenumber():
    result = normalize_element(_el(name="Test", **{"addr:street": "Allenby St"}), "Tel Aviv")
    assert result["address"] == "Allenby St"


def test_address_empty_when_no_addr_tags():
    result = normalize_element(_el(name="Test"), "Tel Aviv")
    assert result["address"] == ""


def test_cuisine_semicolons_replaced_with_slash():
    result = normalize_element(_el(name="Test", cuisine="italian;pizza"), "Tel Aviv")
    assert result["cuisine"] == "italian/pizza"


def test_cuisine_defaults_to_israeli_when_absent():
    result = normalize_element(_el(name="Test"), "Tel Aviv")
    assert result["cuisine"] == "Israeli"


def test_cuisine_defaults_to_israeli_when_empty_string():
    result = normalize_element(_el(name="Test", cuisine=""), "Tel Aviv")
    assert result["cuisine"] == "Israeli"


def test_city_comes_from_argument_not_tags():
    result = normalize_element(_el(name="Test", **{"addr:city": "Ignore This"}), "Jerusalem")
    assert result["city"] == "Jerusalem"


def test_country_is_always_israel():
    result = normalize_element(_el(name="Test"), "Haifa")
    assert result["country"] == "Israel"


def test_osm_id_is_string():
    result = normalize_element(_el(osm_id=987654, name="Test"), "Tel Aviv")
    assert result["osm_id"] == "987654"


def test_lat_lon_preserved():
    result = normalize_element(_el(osm_id=1, lat=31.78, lon=35.22, name="Test"), "Jerusalem")
    assert result["lat"] == 31.78
    assert result["lon"] == 35.22


def test_defaults_for_price_level_rating_is_open():
    result = normalize_element(_el(name="Test"), "Tel Aviv")
    assert result["price_level"] == 3
    assert result["rating"] == 4.0
    assert result["is_open"] == 1


def test_last_updated_is_iso_string():
    result = normalize_element(_el(name="Test"), "Tel Aviv")
    # Should parse as a valid ISO datetime
    from datetime import datetime
    datetime.fromisoformat(result["last_updated"])


# ── upsert_restaurants ────────────────────────────────────────────────────────

@pytest.fixture()
def mem_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE discover_restaurants (
            id INTEGER PRIMARY KEY, osm_id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL, city TEXT NOT NULL,
            country TEXT NOT NULL DEFAULT 'Israel', cuisine TEXT NOT NULL,
            address TEXT NOT NULL DEFAULT '', lat REAL NOT NULL DEFAULT 0.0,
            lon REAL NOT NULL DEFAULT 0.0, price_level INTEGER NOT NULL DEFAULT 3,
            rating REAL NOT NULL DEFAULT 4.0, is_open INTEGER NOT NULL DEFAULT 1,
            last_updated TEXT NOT NULL DEFAULT ''
        )
        """
    )
    conn.commit()
    yield conn
    conn.close()


def _row(osm_id: str = "osm-1", name: str = "Test") -> dict:
    return {
        "osm_id": osm_id, "name": name, "city": "Tel Aviv", "country": "Israel",
        "cuisine": "Israeli", "address": "", "lat": 32.0, "lon": 34.7,
        "price_level": 3, "rating": 4.0, "is_open": 1, "last_updated": "",
    }


def test_upsert_inserts_new_row(mem_conn):
    count = upsert_restaurants(mem_conn, [_row()])
    assert count == 1
    assert mem_conn.execute("SELECT COUNT(*) FROM discover_restaurants").fetchone()[0] == 1


def test_upsert_updates_existing_row_on_conflict(mem_conn):
    upsert_restaurants(mem_conn, [_row(name="Original")])
    upsert_restaurants(mem_conn, [_row(name="Updated")])
    assert mem_conn.execute("SELECT COUNT(*) FROM discover_restaurants").fetchone()[0] == 1
    assert mem_conn.execute("SELECT name FROM discover_restaurants").fetchone()[0] == "Updated"


def test_upsert_returns_row_count(mem_conn):
    rows = [_row(osm_id=f"osm-{i}") for i in range(5)]
    assert upsert_restaurants(mem_conn, rows) == 5
