from fastapi import APIRouter
import math

router = APIRouter()

# Risk radius (in metres) and color coding per disaster type
DISASTER_CONFIG = {
    "fire":       {"radius": 150,   "risk": "high",     "color": "#EF4444"},   # building fire ~150m
    "flood":      {"radius": 3000,  "risk": "high",     "color": "#3B82F6"},   # flood plain ~3km
    "earthquake": {"radius": 10000, "risk": "moderate", "color": "#F59E0B"},   # felt zone ~10km
    "cyclone":    {"radius": 50000, "risk": "extreme",  "color": "#8B5CF6"},   # cyclone ~50km
    "landslide":  {"radius": 500,   "risk": "high",     "color": "#92400E"},   # slope ~500m
    "tsunami":    {"radius": 20000, "risk": "extreme",  "color": "#1D4ED8"},   # coastal ~20km
    "disaster":   {"radius": 1000,  "risk": "moderate", "color": "#F59E0B"},   # generic
}

DEFAULT_CONFIG = {"radius": 500, "risk": "moderate", "color": "#F59E0B"}


def generate_zone_polygon(lat: float, lng: float, radius_m: float, points: int = 16):
    """Generate a rough circular polygon around a point for map overlay."""
    coords = []
    for i in range(points):
        angle = math.radians(360 / points * i)
        # Convert metres to approximate degrees
        d_lat = (radius_m / 111320) * math.cos(angle)
        d_lng = (radius_m / (111320 * math.cos(math.radians(lat)))) * math.sin(angle)
        coords.append([lat + d_lat, lng + d_lng])
    coords.append(coords[0])  # close the polygon
    return coords


@router.get("/predict")
def predict_zone(lat: float, lng: float, disaster_type: str = "flood"):
    """
    Predict the hazard zone radius for a given disaster type and location.
    Returns GeoJSON-compatible zone data for Leaflet rendering.
    """
    config = DISASTER_CONFIG.get(disaster_type.lower(), DEFAULT_CONFIG)
    radius = config["radius"]
    polygon = generate_zone_polygon(lat, lng, radius)

    return {
        "center": {"lat": lat, "lng": lng},
        "radius_m": radius,
        "risk_level": config["risk"],
        "color": config["color"],
        "disaster_type": disaster_type,
        "polygon": polygon,
        "evacuation_radius_m": int(radius * 1.5),
        "description": f"{disaster_type.capitalize()} hazard zone — {config['risk'].upper()} risk within {radius/1000:.1f} km radius.",
    }


@router.get("/all-zones")
def all_active_zones():
    """
    Return all currently active hazard zones from reported events.
    Reads from events DB and generates zones dynamically.
    """
    from database import get_db
    conn = get_db()
    events = conn.execute(
        "SELECT disaster_type, lat, lng, location, severity FROM events"
    ).fetchall()
    conn.close()

    zones = []
    for e in events:
        if e["lat"] and e["lng"]:
            config = DISASTER_CONFIG.get(e["disaster_type"].lower(), DEFAULT_CONFIG)
            # Scale radius by severity
            severity_mult = {"high": 1.5, "extreme": 2.0, "moderate": 1.0, "low": 0.6}.get(e["severity"], 1.0)
            radius = int(config["radius"] * severity_mult)
            zones.append({
                "location": e["location"],
                "disaster_type": e["disaster_type"],
                "center": {"lat": e["lat"], "lng": e["lng"]},
                "radius_m": radius,
                "risk_level": config["risk"],
                "color": config["color"],
                "polygon": generate_zone_polygon(e["lat"], e["lng"], radius),
            })
    return zones
