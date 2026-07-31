from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import init_db
from routes import events, hazards, facilities, assistant
import os

app = FastAPI(title="Rakshak AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB on startup
init_db()

# Register API routers
app.include_router(events.router, prefix="/api/events", tags=["Events"])
app.include_router(hazards.router, prefix="/api/hazards", tags=["Hazards"])
app.include_router(facilities.router, prefix="/api/facilities", tags=["Facilities"])
app.include_router(assistant.router, prefix="/api/assistant", tags=["Assistant"])

# Serve the frontend from FastAPI — no CORS issues during demo
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
