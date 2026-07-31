from fastapi import APIRouter
from database import get_db
import requests
import os

router = APIRouter()
GOOGLE_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


@router.get("/nearby")
def nearby_facilities(lat: float, lng: float, radius: int = 5000, facility_type: str = "hospital"):
    """
    Get nearby hospitals or shelters.
    If GOOGLE_MAPS_API_KEY is set, enriches with live Google Places data.
    Falls back to seeded SQLite data if no key is set.
    """
    conn = get_db()

    if GOOGLE_KEY and facility_type == "hospital":
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            "location": f"{lat},{lng}",
            "radius": radius,
            "type": "hospital",
            "key": GOOGLE_KEY,
        }
        try:
            resp = requests.get(url, params=params, timeout=5).json()
            results = []
            for place in resp.get("results", []):
                row = conn.execute(
                    "SELECT beds_available, icu_available, is_open FROM facilities WHERE name = ?",
                    (place["name"],),
                ).fetchone()
                results.append({
                    "name": place["name"],
                    "lat": place["geometry"]["location"]["lat"],
                    "lng": place["geometry"]["location"]["lng"],
                    "address": place.get("vicinity", ""),
                    "beds_available": row["beds_available"] if row else "Unknown",
                    "icu_available": row["icu_available"] if row else "Unknown",
                    "is_open": place.get("opening_hours", {}).get("open_now", True),
                    "rating": place.get("rating", None),
                })
            conn.close()
            return results
        except Exception:
            pass  # Fall through to local data

    # --- Local SQLite fallback ---
    if facility_type == "shelter":
        rows = conn.execute(
            "SELECT * FROM shelters ORDER BY is_open DESC"
        ).fetchall()
        conn.close()
        return [
            {
                "name": r["name"],
                "lat": r["lat"],
                "lng": r["lng"],
                "address": r["address"],
                "capacity": r["capacity"],
                "occupied": r["occupied"],
                "available_space": r["capacity"] - r["occupied"],
                "is_open": bool(r["is_open"]),
                "type": "shelter",
            }
            for r in rows
        ]
    else:
        rows = conn.execute(
            "SELECT * FROM facilities WHERE type='hospital' ORDER BY beds_available DESC"
        ).fetchall()
        conn.close()
        return [
            {
                "name": r["name"],
                "lat": r["lat"],
                "lng": r["lng"],
                "address": r["address"],
                "beds_available": r["beds_available"],
                "icu_available": r["icu_available"],
                "is_open": bool(r["is_open"]),
                "type": "hospital",
            }
            for r in rows
        ]


@router.get("/all")
def all_facilities():
    """Return all facilities from local DB (used for offline caching)."""
    conn = get_db()
    hospitals = conn.execute("SELECT * FROM facilities WHERE type='hospital'").fetchall()
    shelters = conn.execute("SELECT * FROM shelters").fetchall()
    conn.close()
    return {
        "hospitals": [dict(r) for r in hospitals],
        "shelters": [dict(r) for r in shelters],
    }


@router.post("/update-beds")
def update_beds(name: str, beds: int, icu: int = 0):
    """Update bed availability for a hospital (admin endpoint)."""
    conn = get_db()
    existing = conn.execute("SELECT id FROM facilities WHERE name=?", (name,)).fetchone()
    if existing:
        conn.execute(
            "UPDATE facilities SET beds_available=?, icu_available=? WHERE name=?",
            (beds, icu, name),
        )
    else:
        conn.execute(
            "INSERT INTO facilities (name, type, beds_available, icu_available) VALUES (?,?,?,?)",
            (name, "hospital", beds, icu),
        )
    conn.commit()
    conn.close()
    return {"status": "updated", "name": name, "beds": beds, "icu": icu}
