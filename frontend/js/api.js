/**
 * api.js — Rakshak AI API Client
 * All fetch calls to the FastAPI backend are centralized here.
 * API_BASE is empty so requests go to same origin (FastAPI serves frontend).
 */

const API_BASE = ""; // same-origin: FastAPI serves both API + frontend

// ---- Facilities ----

async function getNearbyFacilities(lat, lng, facilityType = "hospital") {
  const res = await fetch(
    `${API_BASE}/api/facilities/nearby?lat=${lat}&lng=${lng}&facility_type=${facilityType}`
  );
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function getAllFacilities() {
  const res = await fetch(`${API_BASE}/api/facilities/all`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function updateBeds(name, beds, icu = 0) {
  const res = await fetch(
    `${API_BASE}/api/facilities/update-beds?name=${encodeURIComponent(name)}&beds=${beds}&icu=${icu}`,
    { method: "POST" }
  );
  return res.json();
}

// ---- AI Assistant ----

async function askAssistant(text) {
  const lang = document.getElementById("langSelect")?.value || "en-IN";
  const res = await fetch(`${API_BASE}/api/assistant/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, lang }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  return data.reply;
}

// ---- Events ----

async function getActiveEvents() {
  const res = await fetch(`${API_BASE}/api/events/active`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function detectDisasters() {
  const res = await fetch(`${API_BASE}/api/events/detect`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// ---- Hazards ----

async function getHazardZones() {
  const res = await fetch(`${API_BASE}/api/hazards/all-zones`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function predictZone(lat, lng, disasterType = "flood") {
  const res = await fetch(
    `${API_BASE}/api/hazards/predict?lat=${lat}&lng=${lng}&disaster_type=${disasterType}`
  );
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
