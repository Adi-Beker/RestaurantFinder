from __future__ import annotations

import sqlite3

SEED_RESTAURANTS: list[dict] = [
    # ── Tel Aviv ──────────────────────────────────────────────────────────────
    {
        "osm_id": "seed-001", "name": "HaBasta", "city": "Tel Aviv",
        "cuisine": "Israeli", "address": "4 HaShomer St, Tel Aviv",
        "lat": 32.0554, "lon": 34.7626, "price_level": 3, "rating": 4.7,
    },
    {
        "osm_id": "seed-002", "name": "Ouzeria", "city": "Tel Aviv",
        "cuisine": "Israeli", "address": "35 Frishman St, Tel Aviv",
        "lat": 32.0803, "lon": 34.7726, "price_level": 2, "rating": 4.5,
    },
    {
        "osm_id": "seed-003", "name": "Toto", "city": "Tel Aviv",
        "cuisine": "Italian", "address": "4 Berkowitz St, Tel Aviv",
        "lat": 32.0795, "lon": 34.7894, "price_level": 4, "rating": 4.6,
    },
    {
        "osm_id": "seed-004", "name": "Taizu", "city": "Tel Aviv",
        "cuisine": "Asian", "address": "23 Menachem Begin Rd, Tel Aviv",
        "lat": 32.0675, "lon": 34.7893, "price_level": 4, "rating": 4.8,
    },
    {
        "osm_id": "seed-005", "name": "Port Said", "city": "Tel Aviv",
        "cuisine": "Israeli", "address": "5 Har Sinai St, Tel Aviv",
        "lat": 32.0636, "lon": 34.7751, "price_level": 2, "rating": 4.5,
    },
    {
        "osm_id": "seed-006", "name": "Mashya", "city": "Tel Aviv",
        "cuisine": "Israeli", "address": "6 Allenby St, Tel Aviv",
        "lat": 32.0673, "lon": 34.7710, "price_level": 4, "rating": 4.6,
    },
    {
        "osm_id": "seed-007", "name": "The Caucasus", "city": "Tel Aviv",
        "cuisine": "Georgian", "address": "30 Ibn Gvirol St, Tel Aviv",
        "lat": 32.0827, "lon": 34.7808, "price_level": 2, "rating": 4.4,
    },
    {
        "osm_id": "seed-008", "name": "Onami", "city": "Tel Aviv",
        "cuisine": "Japanese", "address": "18 Ha-Arba'a St, Tel Aviv",
        "lat": 32.0663, "lon": 34.7896, "price_level": 3, "rating": 4.5,
    },
    # ── Jerusalem ─────────────────────────────────────────────────────────────
    {
        "osm_id": "seed-009", "name": "Machneyuda", "city": "Jerusalem",
        "cuisine": "Israeli", "address": "10 Beit Ya'akov St, Jerusalem",
        "lat": 31.7836, "lon": 35.2122, "price_level": 4, "rating": 4.8,
    },
    {
        "osm_id": "seed-010", "name": "Rooftop", "city": "Jerusalem",
        "cuisine": "Israeli", "address": "1 King David St, Jerusalem",
        "lat": 31.7765, "lon": 35.2210, "price_level": 4, "rating": 4.6,
    },
    {
        "osm_id": "seed-011", "name": "Adom", "city": "Jerusalem",
        "cuisine": "French", "address": "31 Jaffa St, Jerusalem",
        "lat": 31.7845, "lon": 35.2148, "price_level": 4, "rating": 4.5,
    },
    {
        "osm_id": "seed-012", "name": "Chakra", "city": "Jerusalem",
        "cuisine": "Israeli", "address": "41 King George St, Jerusalem",
        "lat": 31.7798, "lon": 35.2181, "price_level": 3, "rating": 4.4,
    },
    {
        "osm_id": "seed-013", "name": "Ima", "city": "Jerusalem",
        "cuisine": "Israeli", "address": "189 Agrippas St, Jerusalem",
        "lat": 31.7851, "lon": 35.2103, "price_level": 2, "rating": 4.5,
    },
    {
        "osm_id": "seed-014", "name": "Satya", "city": "Jerusalem",
        "cuisine": "Israeli", "address": "6 Shimon Ben Shetah St, Jerusalem",
        "lat": 31.7812, "lon": 35.2155, "price_level": 3, "rating": 4.4,
    },
    {
        "osm_id": "seed-015", "name": "Mona", "city": "Jerusalem",
        "cuisine": "Mediterranean", "address": "12 Shmuel HaNagid St, Jerusalem",
        "lat": 31.7796, "lon": 35.2196, "price_level": 4, "rating": 4.6,
    },
    # ── Haifa ─────────────────────────────────────────────────────────────────
    {
        "osm_id": "seed-016", "name": "Fattoush", "city": "Haifa",
        "cuisine": "Arab-Israeli", "address": "38 Ben Gurion Blvd, Haifa",
        "lat": 32.8197, "lon": 34.9885, "price_level": 2, "rating": 4.5,
    },
    {
        "osm_id": "seed-017", "name": "Douzan", "city": "Haifa",
        "cuisine": "Arab", "address": "35 Ben Gurion Blvd, Haifa",
        "lat": 32.8193, "lon": 34.9884, "price_level": 3, "rating": 4.4,
    },
    {
        "osm_id": "seed-018", "name": "Hanamal 24", "city": "Haifa",
        "cuisine": "Israeli", "address": "24 HaNamal St, Haifa",
        "lat": 32.8226, "lon": 35.0012, "price_level": 3, "rating": 4.3,
    },
    {
        "osm_id": "seed-019", "name": "Albi", "city": "Haifa",
        "cuisine": "Israeli", "address": "12 Kikar Paris, Haifa",
        "lat": 32.8234, "lon": 34.9981, "price_level": 3, "rating": 4.4,
    },
    {
        "osm_id": "seed-020", "name": "El Babour", "city": "Haifa",
        "cuisine": "Arab", "address": "1 HaBiluim St, Haifa",
        "lat": 32.8156, "lon": 35.0031, "price_level": 2, "rating": 4.6,
    },
    # ── Ashdod ────────────────────────────────────────────────────────────────
    {
        "osm_id": "seed-021", "name": "Romano Ashdod", "city": "Ashdod",
        "cuisine": "Italian", "address": "7 Rokach Blvd, Ashdod",
        "lat": 31.8038, "lon": 34.6502, "price_level": 3, "rating": 4.3,
    },
    {
        "osm_id": "seed-022", "name": "HaShuk Ashdod", "city": "Ashdod",
        "cuisine": "Israeli", "address": "12 Sderot HaNassi, Ashdod",
        "lat": 31.8073, "lon": 34.6473, "price_level": 2, "rating": 4.2,
    },
    {
        "osm_id": "seed-023", "name": "Brasserie Ashdod", "city": "Ashdod",
        "cuisine": "French", "address": "3 Nordau St, Ashdod",
        "lat": 31.8015, "lon": 34.6516, "price_level": 4, "rating": 4.4,
    },
    {
        "osm_id": "seed-024", "name": "Malabi", "city": "Ashdod",
        "cuisine": "Moroccan", "address": "21 HaAtzmaut St, Ashdod",
        "lat": 31.7999, "lon": 34.6493, "price_level": 2, "rating": 4.3,
    },
    {
        "osm_id": "seed-025", "name": "Azura Ashdod", "city": "Ashdod",
        "cuisine": "Mizrahi", "address": "5 Weizmann Blvd, Ashdod",
        "lat": 31.8055, "lon": 34.6487, "price_level": 2, "rating": 4.5,
    },
]


def seed_discover_restaurants(conn: sqlite3.Connection) -> None:
    conn.executemany(
        """
        INSERT OR IGNORE INTO discover_restaurants
            (osm_id, name, city, country, cuisine, address, lat, lon,
             price_level, rating, is_open, last_updated)
        VALUES
            (:osm_id, :name, :city, 'Israel', :cuisine, :address, :lat, :lon,
             :price_level, :rating, 1, '')
        """,
        SEED_RESTAURANTS,
    )
    conn.commit()
