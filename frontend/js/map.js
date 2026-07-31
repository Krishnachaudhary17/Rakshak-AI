/**
 * map.js — Leaflet Map Initialization & Layer Management
 * Renders hospitals, shelters, and hazard zones on a dark OSM map.
 */

let map;
let layerState = { hazards: true, hospitals: true, shelters: true, routes: true };
let layers = {
  hazards: L.layerGroup(),
  hospitals: L.layerGroup(),
  shelters: L.layerGroup(),
  routes: L.layerGroup(),
};

// Custom marker icons
const icons = {
  hospital: L.divIcon({
    className: "",
    html: `<div style="background:#10B981;width:12px;height:12px;border-radius:50%;border:2px solid #fff;box-shadow:0 0 8px #10B981"></div>`,
    iconSize: [12, 12],
    iconAnchor: [6, 6],
  }),
  shelter: L.divIcon({
    className: "",
    html: `<div style="background:#ffb95f;width:12px;height:12px;border-radius:50%;border:2px solid #fff;box-shadow:0 0 8px #ffb95f"></div>`,
    iconSize: [12, 12],
    iconAnchor: [6, 6],
  }),
  user: L.divIcon({
    className: "",
    html: `<div style="background:#3B82F6;width:14px;height:14px;border-radius:50%;border:3px solid #fff;box-shadow:0 0 12px #3B82F6"></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  }),
};

function initMap() {
  map = L.map("map", {
    center: [28.6139, 77.209],   // Delhi default
    zoom: 12,
    zoomControl: true,
    attributionControl: false,
  });

  // Dark OpenStreetMap tiles
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap",
    maxZoom: 18,
  }).addTo(map);

  // Add all layer groups to map
  Object.values(layers).forEach(lg => lg.addTo(map));

  // Load facilities onto map
  loadMapFacilities();

  // Handle map click to show hazard prediction
  map.on("click", onMapClick);
}

async function loadMapFacilities() {
  try {
    const data = await getAllFacilities();

    // Hospitals
    (data.hospitals || []).forEach(f => {
      if (!f.lat || !f.lng) return;
      L.marker([f.lat, f.lng], { icon: icons.hospital })
        .bindPopup(buildPopup(f, "hospital"))
        .addTo(layers.hospitals);
    });

    // Shelters
    (data.shelters || []).forEach(f => {
      if (!f.lat || !f.lng) return;
      L.marker([f.lat, f.lng], { icon: icons.shelter })
        .bindPopup(buildPopup(f, "shelter"))
        .addTo(layers.shelters);
    });
  } catch (e) {
    console.warn("Map facilities load failed:", e);
  }
}

async function loadHazardZones() {
  try {
    const zones = await getHazardZones();
    zones.forEach(zone => addHazardZone(zone));
  } catch (e) {
    console.warn("Hazard zones load failed:", e);
    // Add demo zone
    addHazardZone({
      center: { lat: 28.6619, lng: 77.23 },
      radius_m: 5000,
      color: "#3B82F6",
      disaster_type: "flood",
      risk_level: "high",
    });
  }
}

function addHazardZone(zone) {
  const circle = L.circle([zone.center.lat, zone.center.lng], {
    color: zone.color || "#EF4444",
    fillColor: zone.color || "#EF4444",
    fillOpacity: 0.15,
    radius: zone.radius_m,
    weight: 1.5,
    dashArray: "4 4",
  }).bindPopup(`
    <div style="font-family:Inter,sans-serif;font-size:12px">
      <strong>${zone.disaster_type?.toUpperCase() || "HAZARD"} ZONE</strong><br>
      Risk: <strong>${zone.risk_level?.toUpperCase()}</strong><br>
      Radius: ${(zone.radius_m / 1000).toFixed(1)} km
    </div>
  `);
  layers.hazards.addLayer(circle);
}

async function onMapClick(e) {
  const { lat, lng } = e.latlng;
  const popup = L.popup()
    .setLatLng(e.latlng)
    .setContent(`
      <div style="font-family:Inter,sans-serif;font-size:12px;color:#d4e4fa">
        <strong>Predict Hazard Zone</strong><br>
        <div style="display:flex;gap:4px;margin-top:6px;flex-wrap:wrap">
          <button onclick="predictAtPoint(${lat},${lng},'flood')" style="background:#3B82F6;color:#fff;border:none;padding:3px 8px;border-radius:4px;cursor:pointer;font-size:11px">Flood</button>
          <button onclick="predictAtPoint(${lat},${lng},'fire')" style="background:#EF4444;color:#fff;border:none;padding:3px 8px;border-radius:4px;cursor:pointer;font-size:11px">Fire</button>
          <button onclick="predictAtPoint(${lat},${lng},'earthquake')" style="background:#F59E0B;color:#fff;border:none;padding:3px 8px;border-radius:4px;cursor:pointer;font-size:11px">Earthquake</button>
        </div>
      </div>`)
    .openOn(map);
}

window.predictAtPoint = async function(lat, lng, type) {
  map.closePopup();
  try {
    const zone = await predictZone(lat, lng, type);
    addHazardZone({ center: { lat, lng }, ...zone });
  } catch (e) {
    console.warn("Predict failed:", e);
  }
};

function locateMe() {
  if (!navigator.geolocation) return alert("Geolocation not supported.");
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const { latitude: lat, longitude: lng } = pos.coords;
      map.setView([lat, lng], 14);
      L.marker([lat, lng], { icon: icons.user })
        .bindPopup("<strong>Your Location</strong>")
        .addTo(map)
        .openPopup();
      // Reload facilities for user's location
      loadFacilities(window.currentTab || "hospitals");
    },
    () => alert("Unable to get location. Check browser permissions.")
  );
}

function toggleLayer(layerName) {
  layerState[layerName] = !layerState[layerName];
  const cap = layerName.charAt(0).toUpperCase() + layerName.slice(1);
  const track = document.getElementById(`track${cap}`);
  const thumb = document.getElementById(`thumb${cap}`);

  if (layerState[layerName]) {
    layers[layerName].addTo(map);
    if (track) track.classList.add('on');
    if (thumb) { thumb.classList.add('on'); thumb.classList.remove('off'); }
  } else {
    map.removeLayer(layers[layerName]);
    if (track) track.classList.remove('on');
    if (thumb) { thumb.classList.remove('on'); thumb.classList.add('off'); }
  }
}

function buildPopup(f, type) {
  if (type === "hospital") {
    return `
      <div style="font-family:Inter,sans-serif;font-size:12px;color:#d4e4fa;min-width:160px">
        <strong>${f.name}</strong><br>
        <span style="color:#10B981">Beds: ${f.beds_available ?? "?"}</span> · 
        <span style="color:${f.icu_available > 0 ? '#10B981' : '#EF4444'}">ICU: ${f.icu_available ?? "?"}</span><br>
        <button onclick="navigateTo(${f.lat},${f.lng},'${f.name}')" 
          style="margin-top:6px;background:#0f172a;color:#bec6e0;border:1px solid #45464d;padding:4px 10px;border-radius:4px;cursor:pointer;font-size:11px;width:100%">
          ➤ Navigate
        </button>
      </div>`;
  }
  return `
    <div style="font-family:Inter,sans-serif;font-size:12px;color:#d4e4fa;min-width:160px">
      <strong>${f.name}</strong><br>
      <span style="color:${(f.capacity-f.occupied)>0 ? '#10B981' : '#EF4444'}">
        ${f.capacity - f.occupied} / ${f.capacity} spaces
      </span><br>
      <button onclick="navigateTo(${f.lat},${f.lng},'${f.name}')"
        style="margin-top:6px;background:#0f172a;color:#bec6e0;border:1px solid #45464d;padding:4px 10px;border-radius:4px;cursor:pointer;font-size:11px;width:100%">
        ➤ Navigate
      </button>
    </div>`;
}
