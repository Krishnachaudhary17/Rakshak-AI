from fastapi import APIRouter
from pydantic import BaseModel
from database import get_db
import requests
import os

router = APIRouter()
NEWS_KEY = os.getenv("NEWS_API_KEY")


class EventReport(BaseModel):
    title: str
    disaster_type: str
    location: str
    lat: float
    lng: float
    severity: str = "moderate"


# ---- Classification helpers (used to turn messy headlines into structured events) ----

DISASTER_TYPE_KEYWORDS = {
    "flood": ["flood", "flooding", "waterlogging", "inundat"],
    "earthquake": ["earthquake", "tremor", "quake", "seismic"],
    "fire": ["fire", "blaze", "inferno", "burnt", "burning"],
    "cyclone": ["cyclone", "hurricane", "storm surge", "typhoon"],
    "landslide": ["landslide", "mudslide", "rockslide"],
    "tsunami": ["tsunami", "tidal wave"],
}

HIGH_SEVERITY_WORDS = ["kill", "dead", "death", "devastat", "severe", "major", "destroy", "collapse"]
MODERATE_SEVERITY_WORDS = ["warning", "alert", "evacuat", "injur"]

# Small lookup table of major Indian cities/regions for quick keyword-based geocoding.
# Good enough for a hackathon demo; swap for a real geocoding API later if needed.
CITY_COORDS = {
    "delhi": (28.6139, 77.2090), "new delhi": (28.6139, 77.2090),
    "mumbai": (19.0760, 72.8777), "chennai": (13.0827, 80.2707),
    "kolkata": (22.5726, 88.3639), "bengaluru": (12.9716, 77.5946),
    "bangalore": (12.9716, 77.5946), "hyderabad": (17.3850, 78.4867),
    "ahmedabad": (23.0225, 72.5714), "pune": (18.5204, 73.8567),
    "guwahati": (26.1445, 91.7362), "assam": (26.2006, 92.9376),
    "patna": (25.5941, 85.1376), "bihar": (25.0961, 85.3131),
    "bhubaneswar": (20.2961, 85.8245), "odisha": (20.9517, 85.0985),
    "kochi": (9.9312, 76.2673), "kerala": (10.8505, 76.2711),
    "jaipur": (26.9124, 75.7873), "rajasthan": (27.0238, 74.2179),
    "lucknow": (26.8467, 80.9462), "uttar pradesh": (26.8467, 80.9462),
    "chandigarh": (30.7333, 76.7794), "dehradun": (30.3165, 78.0322),
    "uttarakhand": (30.0668, 79.0193), "shimla": (31.1048, 77.1734),
    "himachal": (31.1048, 77.1734), "srinagar": (34.0837, 74.7973),
    "kashmir": (34.0837, 74.7973), "amritsar": (31.6340, 74.8723),
    "punjab": (31.1471, 75.3412), "surat": (21.1702, 72.8311),
    "nagpur": (21.1458, 79.0882), "indore": (22.7196, 75.8577),
    "bhopal": (23.2599, 77.4126), "madhya pradesh": (23.2599, 77.4126),
    "ranchi": (23.3441, 85.3096), "jharkhand": (23.3441, 85.3096),
    "raipur": (21.2514, 81.6296), "chhattisgarh": (21.2514, 81.6296),
    "goa": (15.2993, 74.1240), "andhra pradesh": (16.5062, 80.6480),
    "vizag": (17.6868, 83.2185), "visakhapatnam": (17.6868, 83.2185),
    "ghaziabad": (28.6692, 77.4538), "noida": (28.5355, 77.3910),
}


def classify_disaster_type(text: str) -> str:
    text = text.lower()
    for dtype, keywords in DISASTER_TYPE_KEYWORDS.items():
        if any(k in text for k in keywords):
            return dtype
    return "disaster"


def classify_severity(text: str) -> str:
    text = text.lower()
    if any(w in text for w in HIGH_SEVERITY_WORDS):
        return "high"
    if any(w in text for w in MODERATE_SEVERITY_WORDS):
        return "moderate"
    return "low"


def geocode_from_text(text: str):
    text = text.lower()
    for city, coords in CITY_COORDS.items():
        if city in text:
            return city.title(), coords
    return None, None


@router.get("/detect")
def detect_events():
    """
    Fetch recent disaster news from NewsAPI, classify each headline into a
    disaster type + severity, geocode it against known Indian cities, and
    insert it into the events table so it shows up on the live map.
    Falls back to seeded/local DB events if no API key is set or the call fails.
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
            conn = get_db()
            inserted = []
            for a in articles:
                title = a.get("title", "")
                if not title or "[Removed]" in title:
                    continue
                desc = a.get("description", "") or ""
                combined = f"{title} {desc}"
                location, coords = geocode_from_text(combined)
                if not coords:
                    continue  # skip articles we can't place on the map
                existing = conn.execute(
                    "SELECT id FROM events WHERE title = ?", (title,)
                ).fetchone()
                if existing:
                    continue
                disaster_type = classify_disaster_type(combined)
                severity = classify_severity(combined)
                lat, lng = coords
                conn.execute(
                    "INSERT INTO events (title, disaster_type, location, lat, lng, severity) VALUES (?,?,?,?,?,?)",
                    (title, disaster_type, location, lat, lng, severity),
                )
                inserted.append({
                    "title": title, "disaster_type": disaster_type,
                    "location": location, "lat": lat, "lng": lng,
                    "severity": severity, "source": a.get("source", {}).get("name"),
                    "url": a.get("url"),
                })
            conn.commit()
            conn.close()
            return inserted
        except Exception:
            pass  # Fallback below

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
def report_event(payload: EventReport):
    """Allow citizens to report a new disaster event."""
    conn = get_db()
    conn.execute(
        "INSERT INTO events (title, disaster_type, location, lat, lng, severity) VALUES (?,?,?,?,?,?)",
        (payload.title, payload.disaster_type, payload.location, payload.lat, payload.lng, payload.severity),
    )
    conn.commit()
    conn.close()
    return {"status": "reported", "title": payload.title, "location": payload.location}
