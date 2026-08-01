from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
import jwt
import bcrypt
import os
from datetime import datetime, timedelta, timezone
from database import get_db

router = APIRouter()

JWT_SECRET = os.getenv("JWT_SECRET", "rakshak-dev-secret-change-in-prod")
JWT_ALGO = "HS256"
TOKEN_EXPIRE_HOURS = 12


# ── Models ──────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class HospitalUpdate(BaseModel):
    beds_available: Optional[int] = None
    icu_available: Optional[int] = None
    ventilators: Optional[int] = None
    oxygen_cylinders: Optional[int] = None
    staff_on_duty: Optional[int] = None
    incoming_patients: Optional[int] = None
    incoming_severity: Optional[str] = None      # minor | moderate | critical
    blood_bank_status: Optional[str] = None      # stocked | low | critical
    generator_status: Optional[str] = None       # on | off
    infrastructure_status: Optional[str] = None  # stable | damaged | critical
    is_open: Optional[int] = None
    situation_note: Optional[str] = None


class ShelterUpdate(BaseModel):
    occupied: Optional[int] = None
    is_open: Optional[int] = None
    water_supply_days: Optional[int] = None
    food_supply_days: Optional[int] = None
    bedding_status: Optional[str] = None         # ok | low | out
    medical_needs_count: Optional[int] = None
    medical_needs_tags: Optional[str] = None     # comma-separated tags
    hazard_note: Optional[str] = None
    next_supply_eta: Optional[str] = None
    skills_medical: Optional[int] = None
    skills_engineering: Optional[int] = None
    skills_translation: Optional[int] = None


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_token(user_id: int, username: str, role: str, facility: str) -> str:
    payload = {
        "sub": username,
        "uid": user_id,
        "role": role,
        "facility": facility,
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def _verify_token(authorization: str) -> dict:
    """Extract and verify the JWT from the Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token.")
    token = authorization.split(" ", 1)[1]
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token.")


# ── Routes ──────────────────────────────────────────────────────────────────

@router.post("/login")
def login(req: LoginRequest):
    """Authenticate an admin user and return a JWT."""
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM admin_users WHERE username=?", (req.username,)
    ).fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    if not bcrypt.checkpw(req.password.encode(), user["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    token = _make_token(user["id"], user["username"], user["role"], user["facility_name"])
    return {
        "token": token,
        "role": user["role"],
        "facility": user["facility_name"],
        "username": user["username"],
    }


@router.get("/status")
def get_status(authorization: str = Header(None)):
    """Return current status for the logged-in facility."""
    claims = _verify_token(authorization)
    facility = claims["facility"]
    role = claims["role"]
    conn = get_db()

    if role == "hospital":
        row = conn.execute(
            "SELECT * FROM facilities WHERE name=?", (facility,)
        ).fetchone()
        conn.close()
        if not row:
            raise HTTPException(status_code=404, detail="Facility not found.")
        return {"role": "hospital", "data": dict(row)}
    else:
        row = conn.execute(
            "SELECT * FROM shelters WHERE name=?", (facility,)
        ).fetchone()
        conn.close()
        if not row:
            raise HTTPException(status_code=404, detail="Shelter not found.")
        return {"role": "shelter", "data": dict(row)}


@router.post("/hospital/update")
def update_hospital(update: HospitalUpdate, authorization: str = Header(None)):
    """Update hospital status fields. Only updates provided (non-None) fields."""
    claims = _verify_token(authorization)
    if claims["role"] != "hospital":
        raise HTTPException(status_code=403, detail="Not a hospital account.")

    facility = claims["facility"]
    fields = {k: v for k, v in update.model_dump().items() if v is not None}
    if not fields:
        return {"status": "no_change"}

    fields["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    set_clause = ", ".join(f"{k}=?" for k in fields)
    values = list(fields.values()) + [facility]

    conn = get_db()
    conn.execute(
        f"UPDATE facilities SET {set_clause} WHERE name=?", values
    )
    conn.commit()
    conn.close()
    return {"status": "updated", "facility": facility, "fields": list(fields.keys())}


@router.post("/shelter/update")
def update_shelter(update: ShelterUpdate, authorization: str = Header(None)):
    """Update shelter status fields. Only updates provided (non-None) fields."""
    claims = _verify_token(authorization)
    if claims["role"] != "shelter":
        raise HTTPException(status_code=403, detail="Not a shelter account.")

    facility = claims["facility"]
    fields = {k: v for k, v in update.model_dump().items() if v is not None}
    if not fields:
        return {"status": "no_change"}

    fields["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    set_clause = ", ".join(f"{k}=?" for k in fields)
    values = list(fields.values()) + [facility]

    conn = get_db()
    conn.execute(
        f"UPDATE shelters SET {set_clause} WHERE name=?", values
    )
    conn.commit()
    conn.close()
    return {"status": "updated", "facility": facility, "fields": list(fields.keys())}


@router.post("/logout")
def logout():
    """Client should discard the token. No server state to clear."""
    return {"status": "logged_out"}
