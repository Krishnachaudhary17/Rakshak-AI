from fastapi import APIRouter
from database import get_db
import requests
import os

router = APIRouter()
NEWS_KEY = os.getenv("NEWS_API_KEY")

DISASTER_KEYWORDS = [
    "flood", "earthquake", "fire", "cyclone", "landslide",
    "tsunami", "disaster", "emergency", "India"
]


@router.get("/detect")
def detect_events():
    """
    Fetch recent disaster news from NewsAPI.
    Falls back to seeded DB events if no API key is set.
    """
    if NEWS_KEY:
        url = "https://newsapi.org/v2/everything"
        query = " OR ".join(["flood", "earthquake", "fire", "cyclone", "disaster"])
        params = {
            "q": f"({query}) India",
            "apiKey": NEWS_KEY,
            "sortBy": "publishedAt",
            "pageSize": 10,
            "language": "en",
        }
        try:
            resp = requests.get(url, params=params, timeout=8).json()
            articles = resp.get("articles", [])
            return [
                {
                    "title": a["title"],
                    "source": a["source"]["name"],
                    "url": a["url"],
                    "published_at": a["publishedAt"],
                    "description": a.get("description", ""),
                }
                for a in articles
                if a.get("title") and "[Removed]" not in a.get("title", "")
            ]
        except Exception:
            pass  # Fallback below

    # Local DB fallback
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM events ORDER BY timestamp DESC LIMIT 10"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/active")
def active_events():
    """Return all active events from the local DB."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM events ORDER BY timestamp DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("/report")
def report_event(title: str, disaster_type: str, location: str, lat: float, lng: float, severity: str = "moderate"):
    """Allow citizens to report a new disaster event."""
    conn = get_db()
    conn.execute(
        "INSERT INTO events (title, disaster_type, location, lat, lng, severity) VALUES (?,?,?,?,?,?)",
        (title, disaster_type, location, lat, lng, severity),
    )
    conn.commit()
    conn.close()
    return {"status": "reported", "title": title, "location": location}
