from fastapi import APIRouter
from pydantic import BaseModel
import requests
import os

router = APIRouter()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

SYSTEM_PROMPT = (
    "You are Rakshak, an AI emergency response assistant for India. "
    "Your role is to provide calm, clear, and actionable safety guidance during disasters. "
    "Always reply in the SAME language as the user (Hindi, English, or regional Indian languages). "
    "Keep responses to 2-3 short, actionable sentences. "
    "Prioritize life safety information. Never panic the user."
)


class Query(BaseModel):
    text: str
    lang: str = "en-IN"


@router.post("/chat")
def chat(query: Query):
    """
    Send a message to the Gemini AI emergency assistant.
    Returns a short, actionable response in the user's language.
    """
    if not GEMINI_KEY:
        # Demo fallback when no API key is set
        return _demo_response(query.text)

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    )
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"{SYSTEM_PROMPT}\n\nUser: {query.text}"
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 200,
        },
    }
    try:
        resp = requests.post(url, json=payload, timeout=10).json()
        reply = resp["candidates"][0]["content"]["parts"][0]["text"]
        return {"reply": reply, "lang": query.lang}
    except Exception as e:
        return {"reply": "I'm having trouble connecting right now. Please call 112 for immediate emergency help.", "error": str(e)}


def _demo_response(text: str) -> dict:
    """Canned responses for demo mode when no Gemini key is available."""
    text_lower = text.lower()
    if any(w in text_lower for w in ["flood", "baarish", "pani", "water"]):
        reply = "Move to higher ground immediately. Avoid walking through floodwater. Call 112 for evacuation assistance."
    elif any(w in text_lower for w in ["fire", "aag", "burn"]):
        reply = "Evacuate the building immediately using stairs, not elevators. Call 101 for fire emergency. Meet at the designated assembly point."
    elif any(w in text_lower for w in ["earthquake", "bhukamp", "tremor"]):
        reply = "Drop, Cover, and Hold On. Stay away from windows. Once shaking stops, evacuate carefully and check for injuries."
    elif any(w in text_lower for w in ["hospital", "doctor", "injured", "hurt", "chot"]):
        reply = "The nearest open hospital is City General Hospital with 45 beds available. Tap Navigate on the dashboard for directions."
    elif any(w in text_lower for w in ["shelter", "sharana", "camp"]):
        reply = "Nehru Stadium Shelter is open with 380 spaces available. It is 3.2 km from your location. Tap Map to see the route."
    else:
        reply = "I am Rakshak AI, your emergency assistant. Tell me your situation and I will guide you to safety. You can also call 112 for immediate help."
    return {"reply": reply, "lang": "en-IN", "mode": "demo"}
