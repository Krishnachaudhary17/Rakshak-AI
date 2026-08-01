/**
 * admin.js — Rakshak AI Admin Portal
 * Handles authentication, auto-save, counter logic, and API calls.
 */

const ADMIN_API = "";  // same-origin

// ── Auth ─────────────────────────────────────────────────────────────────────

function getToken() { return localStorage.getItem("rakshak_token"); }
function getRole()  { return localStorage.getItem("rakshak_role"); }
function getFacility() { return localStorage.getItem("rakshak_facility"); }

function saveSession(token, role, facility, username) {
  localStorage.setItem("rakshak_token", token);
  localStorage.setItem("rakshak_role", role);
  localStorage.setItem("rakshak_facility", facility);
  localStorage.setItem("rakshak_username", username);
}

function clearSession() {
  ["rakshak_token","rakshak_role","rakshak_facility","rakshak_username"]
    .forEach(k => localStorage.removeItem(k));
}

/** Called on admin-login.html submit */
async function adminLogin(event) {
  event.preventDefault();
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;
  const btn = document.getElementById("loginBtn");
  const errEl = document.getElementById("loginError");

  errEl.classList.add("hidden");
  btn.disabled = true;
  btn.textContent = "Signing in…";

  try {
    const res = await fetch(`${ADMIN_API}/api/admin/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    const data = await res.json();

    if (!res.ok) {
      errEl.textContent = data.detail || "Login failed.";
      errEl.classList.remove("hidden");
      return;
    }

    saveSession(data.token, data.role, data.facility, data.username);
    window.location.href = data.role === "hospital" ? "admin-hospital.html" : "admin-shelter.html";
  } catch {
    errEl.textContent = "Network error — please try again.";
    errEl.classList.remove("hidden");
  } finally {
    btn.disabled = false;
    btn.textContent = "Sign In";
  }
}

/** Guard pages — redirect to login if no valid token */
function requireAuth(expectedRole) {
  const token = getToken();
  const role = getRole();
  if (!token || (expectedRole && role !== expectedRole)) {
    window.location.href = "admin-login.html";
    return false;
  }
  return true;
}

async function adminLogout() {
  try {
    await fetch(`${ADMIN_API}/api/admin/logout`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${getToken()}` }
    });
  } catch { /* ignore */ }
  clearSession();
  window.location.href = "admin-login.html";
}

// ── API helpers ───────────────────────────────────────────────────────────────

async function fetchStatus() {
  const res = await fetch(`${ADMIN_API}/api/admin/status`, {
    headers: { "Authorization": `Bearer ${getToken()}` }
  });
  if (res.status === 401) { clearSession(); window.location.href = "admin-login.html"; }
  return res.json();
}

async function pushUpdate(role, payload) {
  const endpoint = role === "hospital" ? "/api/admin/hospital/update" : "/api/admin/shelter/update";
  const res = await fetch(`${ADMIN_API}${endpoint}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${getToken()}`,
    },
    body: JSON.stringify(payload),
  });
  if (res.status === 401) { clearSession(); window.location.href = "admin-login.html"; }
  return res.json();
}

// ── Auto-save ─────────────────────────────────────────────────────────────────

let _saveQueue = {};
let _saveTimer = null;

/**
 * Queue a field update — debounced 1.5s, then flushes to server.
 * @param {string} role — 'hospital' | 'shelter'
 * @param {string} field — API field name
 * @param {any}    value
 */
function queueSave(role, field, value) {
  _saveQueue[field] = value;
  clearTimeout(_saveTimer);
  showSaving();
  _saveTimer = setTimeout(() => flushSave(role), 1500);
}

async function flushSave(role) {
  if (!Object.keys(_saveQueue).length) return;
  const payload = { ..._saveQueue };
  _saveQueue = {};
  try {
    await pushUpdate(role, payload);
    showSaved();
  } catch {
    showSaveError();
  }
}

function showSaving() {
  const el = document.getElementById("saveStatus");
  if (!el) return;
  el.textContent = "Saving…";
  el.className = "save-status saving";
}
function showSaved() {
  const el = document.getElementById("saveStatus");
  if (!el) return;
  const now = new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
  el.textContent = `✓ Saved at ${now}`;
  el.className = "save-status saved";
}
function showSaveError() {
  const el = document.getElementById("saveStatus");
  if (!el) return;
  el.textContent = "⚠ Save failed — retrying…";
  el.className = "save-status error";
}

// ── Counter helpers ───────────────────────────────────────────────────────────

/**
 * Initialize a tap-counter widget.
 * @param {string} displayId — element showing the number
 * @param {string} decId     — decrement button id
 * @param {string} incId     — increment button id
 * @param {number} initVal   — starting value
 * @param {string} role      — 'hospital' | 'shelter'
 * @param {string} field     — API field name
 * @param {number} min       — minimum allowed value (default 0)
 * @param {number} step      — increment step (default 1)
 */
function initCounter(displayId, decId, incId, initVal, role, field, min = 0, step = 1) {
  let val = initVal ?? 0;
  const display = document.getElementById(displayId);
  const decBtn  = document.getElementById(decId);
  const incBtn  = document.getElementById(incId);
  if (!display || !decBtn || !incBtn) return;

  display.textContent = val;

  decBtn.addEventListener("click", () => {
    if (val - step < min) return;
    val -= step;
    display.textContent = val;
    queueSave(role, field, val);
    updateCounterColor(display, val, min);
  });

  incBtn.addEventListener("click", () => {
    val += step;
    display.textContent = val;
    queueSave(role, field, val);
    updateCounterColor(display, val, min);
  });

  updateCounterColor(display, val, min);
}

function updateCounterColor(el, val, min) {
  el.classList.remove("text-green-400","text-yellow-400","text-red-400");
  if (val > min + 5) el.classList.add("text-green-400");
  else if (val > min) el.classList.add("text-yellow-400");
  else el.classList.add("text-red-400");
}

// ── Toggle chip helpers ───────────────────────────────────────────────────────

/**
 * Set up a group of toggle chip buttons (radio-style).
 * @param {string[]} ids    — button element ids
 * @param {string}   active — current active value
 * @param {string}   role
 * @param {string}   field
 * @param {Object}   colorMap — { value: 'css-class-for-active' }
 */
function initChipGroup(ids, active, role, field, colorMap) {
  ids.forEach(id => {
    const btn = document.getElementById(id);
    if (!btn) return;
    const val = btn.dataset.value;

    // Set initial state
    if (val === active) activateChip(btn, colorMap[val] || "chip-active-default");

    btn.addEventListener("click", () => {
      // Deactivate all siblings
      ids.forEach(otherId => {
        const other = document.getElementById(otherId);
        if (other) deactivateChip(other);
      });
      activateChip(btn, colorMap[val] || "chip-active-default");
      queueSave(role, field, val);
    });
  });
}

function activateChip(btn, colorClass) {
  btn.dataset.active = "true";
  btn.classList.add("chip-active", colorClass);
  btn.classList.remove("chip-inactive");
}
function deactivateChip(btn) {
  const colorMap = { "chip-green": true, "chip-yellow": true, "chip-red": true, "chip-blue": true, "chip-active-default": true };
  btn.dataset.active = "false";
  btn.classList.remove("chip-active");
  Object.keys(colorMap).forEach(c => btn.classList.remove(c));
  btn.classList.add("chip-inactive");
}

// ── Medical needs tags (multi-select chips) ───────────────────────────────────

let _activeTags = new Set();

function initTagChips(tagIds, currentTagsStr, role) {
  const tags = currentTagsStr ? currentTagsStr.split(",").map(t => t.trim()).filter(Boolean) : [];
  _activeTags = new Set(tags);

  tagIds.forEach(id => {
    const btn = document.getElementById(id);
    if (!btn) return;
    const tag = btn.dataset.tag;

    if (_activeTags.has(tag)) btn.classList.add("tag-active");
    else btn.classList.add("tag-inactive");

    btn.addEventListener("click", () => {
      if (_activeTags.has(tag)) {
        _activeTags.delete(tag);
        btn.classList.remove("tag-active");
        btn.classList.add("tag-inactive");
      } else {
        _activeTags.add(tag);
        btn.classList.add("tag-active");
        btn.classList.remove("tag-inactive");
      }
      queueSave(role, "medical_needs_tags", [..._activeTags].join(","));
    });
  });
}
