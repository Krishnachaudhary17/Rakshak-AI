/**
 * offline.js — Offline Detection & Local Caching
 * Uses localStorage for facility caching so the app works
 * in low/no-network environments (IndexedDB can be added later).
 */

const CACHE_TTL_MS = 30 * 60 * 1000; // 30 minutes

function setupOfflineHandlers() {
  window.addEventListener("offline", onOffline);
  window.addEventListener("online", onOnline);

  // Set initial status
  if (!navigator.onLine) onOffline();

  // Pre-cache all data while online
  if (navigator.onLine) {
    prefetchAndCache();
  }
}

function onOffline() {
  document.getElementById("offlineBanner").classList.remove("hidden");
  updateStatusBadge(false);
  console.log("Rakshak AI: offline mode activated");
}

function onOnline() {
  document.getElementById("offlineBanner").classList.add("hidden");
  updateStatusBadge(true);
  console.log("Rakshak AI: back online — refreshing data");
  prefetchAndCache();
  loadFacilities(window.currentTab || "hospitals");
  loadEvents();
  loadHazardZones();
}

function updateStatusBadge(online) {
  const badge = document.getElementById("statusBadge");
  const icon  = document.getElementById("statusIcon");
  const wifi  = document.getElementById("wifiStatusBtn")?.querySelector(".material-symbols-outlined");

  if (badge) {
    badge.textContent = online ? "ONLINE" : "OFFLINE";
    badge.className = online
      ? "bg-[#10B981]/20 text-[#10B981] px-3 py-1 rounded-full text-xs border border-[#10B981]/30 font-mono font-bold"
      : "bg-yellow-600/20 text-yellow-400 px-3 py-1 rounded-full text-xs border border-yellow-600/30 font-mono font-bold";
  }
  if (icon) {
    icon.textContent = online ? "cloud_done" : "cloud_off";
    icon.style.color = online ? "#10B981" : "#F59E0B";
  }
  if (wifi) {
    wifi.textContent = online ? "wifi" : "wifi_off";
    wifi.style.color = online ? "#10B981" : "#F59E0B";
  }
}

// ---- Caching ----

function cacheFacilities(type, data) {
  try {
    localStorage.setItem(`rakshak_${type}`, JSON.stringify({
      data,
      ts: Date.now(),
    }));
  } catch (e) {
    console.warn("Cache write failed:", e);
  }
}

function loadCachedFacilities(type) {
  try {
    const raw = localStorage.getItem(`rakshak_${type}`);
    if (!raw) return [];
    const { data, ts } = JSON.parse(raw);
    if (Date.now() - ts > CACHE_TTL_MS) return []; // stale
    return data || [];
  } catch {
    return [];
  }
}

async function prefetchAndCache() {
  try {
    const all = await getAllFacilities();
    cacheFacilities("hospitals", all.hospitals || []);
    cacheFacilities("shelters", all.shelters || []);
  } catch (e) {
    console.warn("Prefetch failed:", e);
  }
}
