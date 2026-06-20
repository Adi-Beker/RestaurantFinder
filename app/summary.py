from __future__ import annotations


def build_summary(rows: list) -> dict:
    """Compute a personalized dining summary from a list of restaurant rows.

    Each row must support dict-style access: row["name"], row["cuisine"], row["rating"].
    Compatible with sqlite3.Row and plain dicts.
    """
    if not rows:
        return {
            "total_visited": 0,
            "top_cuisine": None,
            "avg_rating": None,
            "highest_rated": None,
            "by_cuisine": {},
        }

    by_cuisine: dict[str, list[float]] = {}
    for row in rows:
        by_cuisine.setdefault(row["cuisine"], []).append(float(row["rating"]))

    cuisine_stats = {
        cuisine: {
            "count": len(ratings),
            "avg_rating": round(sum(ratings) / len(ratings), 2),
        }
        for cuisine, ratings in by_cuisine.items()
    }

    top_cuisine = max(cuisine_stats, key=lambda c: cuisine_stats[c]["count"])
    highest_row = max(rows, key=lambda r: r["rating"])
    all_ratings = [float(r["rating"]) for r in rows]

    return {
        "total_visited": len(rows),
        "top_cuisine": top_cuisine,
        "avg_rating": round(sum(all_ratings) / len(all_ratings), 2),
        "highest_rated": {
            "name": highest_row["name"],
            "rating": float(highest_row["rating"]),
            "cuisine": highest_row["cuisine"],
        },
        "by_cuisine": cuisine_stats,
    }
