/**
 * Kerala Resilience OS - Command Center & Citizen Routing Application
 * Complete Frontend Engine with Dual-Mode (Live FastAPI Engine + Offline Simulation Mock)
 */

// Global App State
let map;
let zoneLayer = null;
let hospitalMarkersLayer = null;
let schoolMarkersLayer = null;
let floodedRoadsLayer = null;
let safestRouteLayer = null;
let shortestRouteLayer = null;
let originMarker = null;
let destMarker = null;

let riskChart = null;
let currentChartMode = 'risk'; // 'risk' | 'factors' | 'dist'

let currentZonesData = [];
let currentImpactData = {};
let currentPlanData = [];
let roadGraphData = null;
let hospitalsData = [];
let schoolsData = [];
let zonesGeoJSON = null;
let isBackendLive = false;
let autoSimActive = false;
let mapPickTarget = null; // 'origin' | 'dest' | null
let selectedRoute = "safe";
let latestRouteData = null;

// Risk Colors Palette
const COLORS = {
  low: "#10b981",
  medium: "#f59e0b",
  high: "#f97316",
  critical: "#ef4444"
};

// 10 Grounded Ernakulam Strategic Zones (used for initial load and offline fallback)
const DEFAULT_ZONES_GEO = {
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": { "zone_id": "Z01", "name": "Aluva", "lat": 10.1076, "lon": 76.3516, "elevation_m": 8.0, "hist_risk": 0.95, "terrain": 0.88, "river_prox": 0.98, "road_vuln": 0.85, "n_hospitals": 6, "n_schools": 16 },
      "geometry": { "type": "Polygon", "coordinates": [[[76.320, 10.135], [76.375, 10.140], [76.390, 10.105], [76.365, 10.075], [76.325, 10.085], [76.320, 10.135]]] }
    },
    {
      "type": "Feature",
      "properties": { "zone_id": "Z02", "name": "North Paravur", "lat": 10.1455, "lon": 76.2301, "elevation_m": 4.0, "hist_risk": 0.90, "terrain": 0.92, "river_prox": 0.88, "road_vuln": 0.82, "n_hospitals": 5, "n_schools": 14 },
      "geometry": { "type": "Polygon", "coordinates": [[[76.195, 10.170], [76.265, 10.175], [76.280, 10.120], [76.220, 10.105], [76.195, 10.170]]] }
    },
    {
      "type": "Feature",
      "properties": { "zone_id": "Z03", "name": "Kanayannur (Ernakulam City)", "lat": 9.9816, "lon": 76.2999, "elevation_m": 5.0, "hist_risk": 0.72, "terrain": 0.75, "river_prox": 0.55, "road_vuln": 0.70, "n_hospitals": 12, "n_schools": 22 },
      "geometry": { "type": "Polygon", "coordinates": [[[76.270, 10.020], [76.335, 10.015], [76.340, 9.945], [76.275, 9.950], [76.270, 10.020]]] }
    },
    {
      "type": "Feature",
      "properties": { "zone_id": "Z04", "name": "Kochi (Fort Kochi)", "lat": 9.9650, "lon": 76.2420, "elevation_m": 2.5, "hist_risk": 0.65, "terrain": 0.85, "river_prox": 0.45, "road_vuln": 0.68, "n_hospitals": 4, "n_schools": 12 },
      "geometry": { "type": "Polygon", "coordinates": [[[76.210, 9.995], [76.265, 9.990], [76.265, 9.930], [76.215, 9.935], [76.210, 9.995]]] }
    },
    {
      "type": "Feature",
      "properties": { "zone_id": "Z05", "name": "Kalamassery", "lat": 10.0530, "lon": 76.3210, "elevation_m": 12.0, "hist_risk": 0.70, "terrain": 0.60, "river_prox": 0.75, "road_vuln": 0.65, "n_hospitals": 7, "n_schools": 15 },
      "geometry": { "type": "Polygon", "coordinates": [[[76.285, 10.080], [76.350, 10.080], [76.355, 10.025], [76.280, 10.030], [76.285, 10.080]]] }
    },
    {
      "type": "Feature",
      "properties": { "zone_id": "Z06", "name": "Kunnathunad (Perumbavoor)", "lat": 10.1115, "lon": 76.4780, "elevation_m": 18.0, "hist_risk": 0.78, "terrain": 0.55, "river_prox": 0.82, "road_vuln": 0.62, "n_hospitals": 5, "n_schools": 18 },
      "geometry": { "type": "Polygon", "coordinates": [[[76.410, 10.160], [76.540, 10.155], [76.535, 10.060], [76.405, 10.070], [76.410, 10.160]]] }
    },
    {
      "type": "Feature",
      "properties": { "zone_id": "Z07", "name": "Muvattupuzha", "lat": 9.9830, "lon": 76.5800, "elevation_m": 22.0, "hist_risk": 0.62, "terrain": 0.50, "river_prox": 0.80, "road_vuln": 0.58, "n_hospitals": 5, "n_schools": 15 },
      "geometry": { "type": "Polygon", "coordinates": [[[76.510, 10.050], [76.650, 10.040], [76.640, 9.920], [76.505, 9.930], [76.510, 10.050]]] }
    },
    {
      "type": "Feature",
      "properties": { "zone_id": "Z08", "name": "Kothamangalam", "lat": 10.0620, "lon": 76.6320, "elevation_m": 55.0, "hist_risk": 0.38, "terrain": 0.35, "river_prox": 0.60, "road_vuln": 0.40, "n_hospitals": 4, "n_schools": 14 },
      "geometry": { "type": "Polygon", "coordinates": [[[76.560, 10.150], [76.750, 10.140], [76.730, 9.980], [76.565, 10.000], [76.560, 10.150]]] }
    },
    {
      "type": "Feature",
      "properties": { "zone_id": "Z09", "name": "Angamaly", "lat": 10.1960, "lon": 76.3860, "elevation_m": 14.0, "hist_risk": 0.80, "terrain": 0.65, "river_prox": 0.80, "road_vuln": 0.78, "n_hospitals": 5, "n_schools": 14 },
      "geometry": { "type": "Polygon", "coordinates": [[[76.340, 10.250], [76.440, 10.245], [76.435, 10.150], [76.330, 10.155], [76.340, 10.250]]] }
    },
    {
      "type": "Feature",
      "properties": { "zone_id": "Z10", "name": "Tripunithura", "lat": 9.9480, "lon": 76.3480, "elevation_m": 7.0, "hist_risk": 0.58, "terrain": 0.70, "river_prox": 0.52, "road_vuln": 0.60, "n_hospitals": 4, "n_schools": 12 },
      "geometry": { "type": "Polygon", "coordinates": [[[76.315, 9.970], [76.395, 9.965], [76.390, 9.900], [76.310, 9.910], [76.315, 9.970]]] }
    }
  ]
};

// Facility datasets for offline fallback
const DEFAULT_HOSPITALS = [
  { name: "Aluva District Hospital", lat: 10.1092, lon: 76.3541, zone_id: "Z01", beds: 420 },
  { name: "Karothukuzhi Hospital Aluva", lat: 10.1130, lon: 76.3570, zone_id: "Z01", beds: 150 },
  { name: "Najath Hospital Aluva", lat: 10.1020, lon: 76.3490, zone_id: "Z01", beds: 180 },
  { name: "Don Bosco Hospital Paravur", lat: 10.1440, lon: 76.2290, zone_id: "Z02", beds: 160 },
  { name: "Paravur Taluk Hospital", lat: 10.1480, lon: 76.2340, zone_id: "Z02", beds: 250 },
  { name: "Ernakulam General Hospital", lat: 9.9765, lon: 76.2825, zone_id: "Z03", beds: 780 },
  { name: "Medical Trust Hospital", lat: 9.9680, lon: 76.2920, zone_id: "Z03", beds: 500 },
  { name: "Lisie Hospital Kaloor", lat: 9.9930, lon: 76.2890, zone_id: "Z03", beds: 650 },
  { name: "Aster Medcity Cheranallur", lat: 10.0460, lon: 76.2750, zone_id: "Z05", beds: 670 },
  { name: "Govt Medical College Kalamassery", lat: 10.0545, lon: 76.3530, zone_id: "Z05", beds: 700 },
  { name: "Fort Kochi Taluk Hospital", lat: 9.9630, lon: 76.2440, zone_id: "Z04", beds: 140 },
  { name: "Sanjo Hospital Perumbavoor", lat: 10.1140, lon: 76.4760, zone_id: "Z06", beds: 220 },
  { name: "Muvattupuzha General Hospital", lat: 9.9820, lon: 76.5780, zone_id: "Z07", beds: 350 },
  { name: "Mar Baselios Hospital Kothamangalam", lat: 10.0590, lon: 76.6340, zone_id: "Z08", beds: 310 },
  { name: "Little Flower Hospital Angamaly", lat: 10.1980, lon: 76.3880, zone_id: "Z09", beds: 610 },
  { name: "Taluk Hospital Tripunithura", lat: 9.9510, lon: 76.3510, zone_id: "Z10", beds: 190 }
];

const DEFAULT_SCHOOLS = [
  { name: "UC College Aluva Camp", lat: 10.1240, lon: 76.3420, zone_id: "Z01", capacity: 1200 },
  { name: "St. Xavier's College Aluva", lat: 10.1120, lon: 76.3550, zone_id: "Z01", capacity: 900 },
  { name: "SNM College Maliankara Paravur", lat: 10.1580, lon: 76.2150, zone_id: "Z02", capacity: 1100 },
  { name: "Govt Boys HSS North Paravur", lat: 10.1460, lon: 76.2320, zone_id: "Z02", capacity: 850 },
  { name: "Maharajas College Ernakulam", lat: 9.9730, lon: 76.2840, zone_id: "Z03", capacity: 2000 },
  { name: "St. Albert's College Ernakulam", lat: 9.9860, lon: 76.2810, zone_id: "Z03", capacity: 1500 },
  { name: "Santa Cruz HSS Fort Kochi", lat: 9.9660, lon: 76.2410, zone_id: "Z04", capacity: 800 },
  { name: "CUSAT Student Amenity Centre", lat: 10.0440, lon: 76.3280, zone_id: "Z05", capacity: 1800 },
  { name: "Sree Sankara College Kalady", lat: 10.1680, lon: 76.4390, zone_id: "Z06", capacity: 1600 },
  { name: "NSS HSS Muvattupuzha", lat: 9.9840, lon: 76.5770, zone_id: "Z07", capacity: 750 },
  { name: "Mar Athanasius College Kothamangalam", lat: 10.0570, lon: 76.6260, zone_id: "Z08", capacity: 1700 },
  { name: "De Paul Institute Angamaly", lat: 10.1920, lon: 76.3810, zone_id: "Z09", capacity: 1300 },
  { name: "Govt Sanskrit College Tripunithura", lat: 9.9460, lon: 76.3490, zone_id: "Z10", capacity: 900 }
];

// Offline affected places mapping
const DEFAULT_AFFECTED_PLACES = {
  "Z01": {
    "Evacuation": "Aluva Manappuram, Bank Junction, Thottakkattukara, Desom Colony",
    "Open shelters": "UC College Aluva, St. Xavier's College, Govt Girls HSS Aluva",
    "Deploy pumps": "Aluva Private Bus Stand, Railway Station Subway, Market Road",
    "Close roads": "Aluva Marthanda Varma Old Bridge, Aluva-Paravur Road Causeway",
    "Alert hospitals": "Aluva District Hospital, Karothukuzhi Hospital, Najath Hospital",
    "Public alert": "Periyar River Basin wards 1-14, Municipal Colony, Kunnumpuram"
  },
  "Z02": {
    "Evacuation": "Chendamangalam Weavers Colony, Varapuzha Island, Kottuvally Lowlands",
    "Open shelters": "Paravur Govt Boys HSS, SNM College Maliankara, St. Aloysius School",
    "Deploy pumps": "Paravur Municipal Market, Kacheri Thazham, KMK Junction",
    "Close roads": "Varapuzha Bridge Approaches, Paravur-Aluva Coastal Link",
    "Alert hospitals": "Paravur Taluk Headquarters Hospital, Don Bosco Hospital",
    "Public alert": "Chendamangalam, Ezhikkara, Chittattukara coastal settlements"
  },
  "Z03": {
    "Evacuation": "P&T Colony Kadavanthra, Udaya Colony, Thammanam canal belt",
    "Open shelters": "Maharajas College Hostel, St. Albert's College, St. Teresa's",
    "Deploy pumps": "KSRTC Central Bus Stand, South Railway Station Subway, MG Road",
    "Close roads": "Mullassery Canal Road, Kaloor-Kadavanthra Underpass",
    "Alert hospitals": "Ernakulam General Hospital, Medical Trust Hospital, Lisie Hospital",
    "Public alert": "Ernakulam Central, Panampilly Nagar, Ravipuram, Kaloor wards"
  },
  "Z04": {
    "Evacuation": "Veli Lowlands, Fort Kochi Beach Settlement, Mattancherry Bazar edge",
    "Open shelters": "Santa Cruz HSS Fort Kochi, TD High School Mattancherry",
    "Deploy pumps": "Mattancherry Spice Market, Calvathy Canal outlet, Fort Kochi Bus Stand",
    "Close roads": "Calvathy Bridge Approaches, Bazar Road tidal strip",
    "Alert hospitals": "Cochin Port Trust Hospital, Fort Kochi Taluk Hospital",
    "Public alert": "Fort Kochi, Mattancherry, Amaravathi, Pandikudy coastal residents"
  },
  "Z05": {
    "Evacuation": "Eloor Ferry, FACT Township Lowlands, HMT Colony near stream",
    "Open shelters": "CUSAT Student Amenity Centre, Rajagiri College Kalamassery",
    "Deploy pumps": "Container Road Junction, Premier Junction Underpass",
    "Close roads": "Pathalam Bund Road, Eloor Industrial Link Bridge",
    "Alert hospitals": "Govt Medical College Kalamassery, Apollo Adlux Clinic",
    "Public alert": "Eloor Municipality, Kalamassery Ward 10-22, South Kalamassery"
  },
  "Z06": {
    "Evacuation": "Kalady Sringeri Ghats, Okkal Colony, Vallam Rayonpuram flood zone",
    "Open shelters": "Asramam HSS Perumbavoor, Sree Sankara College Kalady",
    "Deploy pumps": "Perumbavoor Private Bus Stand, Kalady Junction Market",
    "Close roads": "Kalady Bridge over Periyar, MC Road Mattoor stretch",
    "Alert hospitals": "Sanjo Hospital Perumbavoor, Taluk Hospital Perumbavoor",
    "Public alert": "Kalady, Okkal, Koovappady, Rayonpuram riverside settlements"
  },
  "Z07": {
    "Evacuation": "Tribeni Sangamam confluence, Kacherithazham riverside, Kadathy",
    "Open shelters": "NSS HSS Muvattupuzha, Nirmala College Muvattupuzha",
    "Deploy pumps": "Kacherithazham Bridge Sub-road, Municipal Market",
    "Close roads": "Velloorkunnam Low Bridge, Thodupuzha Road Riverside link",
    "Alert hospitals": "Muvattupuzha General Hospital, Nirmala Medical Centre",
    "Public alert": "Muvattupuzha riverside wards, Marady, Arakuzha settlements"
  },
  "Z08": {
    "Evacuation": "Bhoothathankettu downstream tribal settlements, Keerampara river edge",
    "Open shelters": "Mar Athanasius College Kothamangalam, St. George HSS",
    "Deploy pumps": "Kothamangalam Town Bus Stand, Post Office Junction",
    "Close roads": "Bhoothathankettu Barrage Access Road, Chelad Bridge",
    "Alert hospitals": "Mar Baselios Medical Mission Hospital, Taluk Hospital Kothamangalam",
    "Public alert": "Kothamangalam, Pothanicad, Varappetty foothill valleys"
  },
  "Z09": {
    "Evacuation": "Airport periphery Chengalthodu basin, Nayathode, Mattoor colony",
    "Open shelters": "De Paul Institute Angamaly, St. Joseph's Girls HSS",
    "Deploy pumps": "Angamaly KSRTC Bus Stand, Airport Runway Drainage Channel",
    "Close roads": "VIP Road towards CIAL, Angamaly Town Underpass",
    "Alert hospitals": "Little Flower Hospital & Research Centre Angamaly",
    "Public alert": "Angamaly Municipality, Nedumbassery, Chengamanad wards"
  },
  "Z10": {
    "Evacuation": "Chitrapuzha canal bank, Irumpanam refinery periphery, Puthiyakavu lowlands",
    "Open shelters": "Govt Sanskrit College Tripunithura, Palace Girls HSS",
    "Deploy pumps": "Statue Junction, Tripunithura Railway Station Road",
    "Close roads": "Chambakkara Bridge approach, Iron Bridge road",
    "Alert hospitals": "Taluk Hospital Tripunithura, Varma Hospital",
    "Public alert": "Tripunithura, Maradu, Udayamperoor canal belt residents"
  }
};

// Road Network Nodes for Routing
const ROAD_NODES = {
  "N_ALUVA_RSTN":   { name: "Aluva Railway Station", lat: 10.1080, lon: 76.3530, zone_id: "Z01" },
  "N_ALUVA_MANAP":  { name: "Aluva Manappuram Ghat", lat: 10.1140, lon: 76.3480, zone_id: "Z01" },
  "N_ALUVA_BANKJN": { name: "Aluva Bank Junction", lat: 10.1050, lon: 76.3570, zone_id: "Z01" },
  "N_PARAVUR_JN":   { name: "North Paravur Town", lat: 10.1450, lon: 76.2300, zone_id: "Z02" },
  "N_VARAPUZHA_BR": { name: "Varapuzha Bridge", lat: 10.0760, lon: 76.2750, zone_id: "Z02" },
  "N_EDAPPALLY_TOLL":{ name: "Edappally Toll / LuLu Junction", lat: 10.0260, lon: 76.3080, zone_id: "Z03" },
  "N_KALOOR_STAD":  { name: "Kaloor Stadium Junction", lat: 9.9980, lon: 76.2970, zone_id: "Z03" },
  "N_EKM_SOUTH":    { name: "Ernakulam South Railway Station", lat: 9.9680, lon: 76.2910, zone_id: "Z03" },
  "N_MG_ROAD":      { name: "MG Road / Shenoys Junction", lat: 9.9780, lon: 76.2820, zone_id: "Z03" },
  "N_FORT_KOCHI":   { name: "Fort Kochi Bus Stand", lat: 9.9650, lon: 76.2420, zone_id: "Z04" },
  "N_MATTANCHERRY": { name: "Mattancherry Market", lat: 9.9570, lon: 76.2550, zone_id: "Z04" },
  "N_KALAMASSERY":  { name: "Kalamassery Metro Junction", lat: 10.0530, lon: 76.3210, zone_id: "Z05" },
  "N_CUSAT_JN":     { name: "CUSAT University Gate", lat: 10.0450, lon: 76.3270, zone_id: "Z05" },
  "N_CONTAINER_RD": { name: "Container Terminal Highway", lat: 10.0400, lon: 76.2680, zone_id: "Z05" },
  "N_PERUMBAVOOR":  { name: "Perumbavoor Town Centre", lat: 10.1110, lon: 76.4780, zone_id: "Z06" },
  "N_KALADY_BR":    { name: "Kalady Bridge (Periyar)", lat: 10.1650, lon: 76.4380, zone_id: "Z06" },
  "N_MUVATTUPUZHA": { name: "Muvattupuzha Kacherithazham", lat: 9.9830, lon: 76.5800, zone_id: "Z07" },
  "N_KOTHAMANGALAM":{ name: "Kothamangalam Town", lat: 10.0620, lon: 76.6320, zone_id: "Z08" },
  "N_ANGAMALY_TOWN":{ name: "Angamaly KSRTC Centre", lat: 10.1960, lon: 76.3860, zone_id: "Z09" },
  "N_CIAL_AIRPORT": { name: "Cochin International Airport (CIAL)", lat: 10.1520, lon: 76.3920, zone_id: "Z09" },
  "N_TRIPUNITHURA": { name: "Tripunithura Statue Junction", lat: 9.9480, lon: 76.3480, zone_id: "Z10" },
  "N_KAKKANAD_INFO": { name: "Infopark Kakkanad Expressway", lat: 10.0120, lon: 76.3630, zone_id: "Z03" }
};

// =====================================================================
// INITIALIZATION
// =====================================================================
document.addEventListener("DOMContentLoaded", async () => {
  initClock();
  initMap();
  initChart();
  document.addEventListener("click", (event) => {
    const leftPanel = document.getElementById("leftControlPanel");
    const simulateButton = document.getElementById("btnToggleSim");

    if (
      leftPanel &&
      leftPanel.classList.contains("drawer-open") &&
      !leftPanel.contains(event.target) &&
      event.target !== simulateButton &&
      !simulateButton?.contains(event.target)
    ) {
      closeDrawer("leftControlPanel");
    }
  });
  await checkBackendAndLoad();
  runSimulation();
});

function initClock() {
  const clockEl = document.getElementById("liveClock");
  const update = () => {
    const now = new Date();
    clockEl.textContent = now.toLocaleTimeString('en-IN', { hour12: false });
  };
  update();
  setInterval(update, 1000);
}

function initMap() {
  // Center of Ernakulam District
  map = L.map("map", {
    zoomControl: false,
    attributionControl: true
  }).setView([10.07, 76.38], 10);

  // Use OpenStreetMap directly so the standalone frontend has a working basemap
  // without depending on the backend tile proxy or a third-party API key.
  const baseTileLayer = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  });

  baseTileLayer.addTo(map);

  // Add customized zoom control to bottom right
  L.control.zoom({ position: 'bottomright' }).addTo(map);

  // Map Click Listener for Citizen Routing Picker
  map.on("click", (e) => {
    if (mapPickTarget) {
      handleMapCoordinatePick(e.latlng.lat, e.latlng.lng);
    }
  });

  // Layer Groups
  hospitalMarkersLayer = L.layerGroup().addTo(map);
  schoolMarkersLayer = L.layerGroup().addTo(map);
  floodedRoadsLayer = L.layerGroup().addTo(map);
  safestRouteLayer = L.layerGroup().addTo(map);
  shortestRouteLayer = L.layerGroup().addTo(map);
}

// =====================================================================
// BACKEND DETECTION & INITIAL DATA FETCH
// =====================================================================
async function checkBackendAndLoad() {
  const badge = document.getElementById("backendStatusBadge");
  const statusText = document.getElementById("statusText");

  try {
    const res = await fetch("/health", { signal: AbortSignal.timeout(1800) });
    if (res.ok) {
      const data = await res.json();
      isBackendLive = true;
      badge.className = "status-badge connected";
      statusText.textContent = "BASEMAP & AI ENGINE ONLINE";
      
      // Load static zones and network data from API
      const zRes = await fetch("/zones");
      const zData = await zRes.json();
      zonesGeoJSON = zData.geojson;
      hospitalsData = zData.hospitals;
      schoolsData = zData.schools;
      roadGraphData = zData.road_network;
      return;
    }
  } catch (err) {
    // Backend offline: Switch seamlessly to local mathematical engine
    console.warn("Backend not reached. Running resilient client-side simulation engine.", err);
  }

  isBackendLive = false;
  badge.className = "status-badge standalone";
  statusText.textContent = "STANDALONE CLIENT ENGINE (OFFLINE)";
  
  zonesGeoJSON = DEFAULT_ZONES_GEO;
  hospitalsData = DEFAULT_HOSPITALS;
  schoolsData = DEFAULT_SCHOOLS;
}

// =====================================================================
// SIMULATION PIPELINE (LIVE OR CLIENT-SIDE MOCK)
// =====================================================================
async function runSimulation() {
  const rainSlider = document.getElementById("rainSlider");
  const riverSlider = document.getElementById("riverSlider");
  const runBtn = document.getElementById("run");
  const runBtnText = document.getElementById("runBtnText");

  const rainVal = parseFloat(rainSlider.value);
  const riverVal = parseFloat(riverSlider.value);

  // Visual feedback
  runBtn.classList.add("loading");
  runBtnText.textContent = "SIMULATING...";

  let simResult = null;

  if (isBackendLive) {
    try {
      const res = await fetch("/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rainfall_mm: rainVal, river_level_m: riverVal })
      });
      if (res.ok) {
        simResult = await res.json();
      }
    } catch (err) {
      console.warn("Live simulation failed, falling back to client engine.", err);
    }
  }

  // If live call didn't happen or failed, execute client-side mathematical simulation
  if (!simResult) {
    simResult = simulateMock(rainVal, riverVal);
  }

  currentZonesData = simResult.zones;
  currentImpactData = simResult.impact;
  currentPlanData = simResult.plan;

  // Render updates to all UI components
  renderMapPolygons(currentZonesData);
  renderFacilityMarkers(currentZonesData);
  renderFloodedRoads(currentZonesData);
  renderImpactKPIs(currentImpactData);
  renderActionPlan(currentPlanData);
  updateChart(currentZonesData);

  runBtn.classList.remove("loading");
  runBtnText.textContent = "RUN SIMULATION";

  // If citizen route card is open, re-compute routes under new flood state
  if (!document.getElementById("citizenRouteCard").classList.contains("hidden")) {
    fetchRoute(false);
  }
}

// =====================================================================
// CLIENT-SIDE MATHEMATICAL SIMULATION ENGINE (OFFLINE MOCK)
// =====================================================================
function simulateMock(rainfall_mm, river_level_m) {
  // Stage A: Sigmoid rainfall hazard probability
  const k = 0.0065;
  const rain_hazard = Math.min(0.99, Math.max(0.02, 1.0 / (1.0 + Math.exp(-k * (rainfall_mm - 280.0)))));
  
  // River normalized
  const river_norm = Math.min(1.0, Math.max(0.0, river_level_m / 14.0));

  const ELEV_MIN = 2.0;
  const ELEV_MAX = 55.0;

  const W = { rain: 0.28, river: 0.20, hist: 0.20, elev: 0.14, terrain: 0.08, road: 0.05, prox: 0.05 };

  const scoredZones = zonesGeoJSON.features.map(f => {
    const p = f.properties;
    const elev_risk = Math.max(0, Math.min(1, 1.0 - (p.elevation_m - ELEV_MIN) / (ELEV_MAX - ELEV_MIN)));
    
    // Formula rule score
    const c_rain = W.rain * rain_hazard;
    const c_river = W.river * river_norm * p.river_prox;
    const c_hist = W.hist * p.hist_risk;
    const c_elev = W.elev * elev_risk;
    const c_terrain = W.terrain * p.terrain;
    const c_road = W.road * p.road_vuln;
    const c_prox = W.prox * p.river_prox;

    const rule_score = c_rain + c_river + c_hist + c_elev + c_terrain + c_road + c_prox;

    // Non-linear synergy: low elevation + river rise + rain
    const interaction = 0.12 * rain_hazard * river_norm * (1.0 - elev_risk);
    const gbr_score = Math.min(1.0, Math.max(0.0, rule_score + interaction));

    const final_risk = Math.min(0.99, Math.max(0.05, 0.5 * rule_score + 0.5 * gbr_score));

    let risk_class = "low";
    if (final_risk >= 0.75) risk_class = "critical";
    else if (final_risk >= 0.55) risk_class = "high";
    else if (final_risk >= 0.35) risk_class = "medium";

    return {
      zone_id: p.zone_id,
      name: p.name,
      lat: p.lat,
      lon: p.lon,
      elevation_m: p.elevation_m,
      hist_risk: p.hist_risk,
      terrain: p.terrain,
      river_prox: p.river_prox,
      road_vuln: p.road_vuln,
      n_hospitals: p.n_hospitals,
      n_schools: p.n_schools,
      risk: parseFloat(final_risk.toFixed(3)),
      risk_class: risk_class,
      rain_hazard: parseFloat(rain_hazard.toFixed(3)),
      river_norm: parseFloat(river_norm.toFixed(3)),
      factors: {
        rainfall: parseFloat(c_rain.toFixed(3)),
        river: parseFloat(c_river.toFixed(3)),
        historical: parseFloat(c_hist.toFixed(3)),
        elevation: parseFloat(c_elev.toFixed(3)),
        terrain: parseFloat(c_terrain.toFixed(3)),
        roads: parseFloat(c_road.toFixed(3)),
        proximity: parseFloat(c_prox.toFixed(3))
      }
    };
  });

  // Impact calculations
  const badZoneIds = new Set(scoredZones.filter(z => z.risk_class === "high" || z.risk_class === "critical").map(z => z.zone_id));
  const threatenedH = hospitalsData.filter(h => badZoneIds.has(h.zone_id));
  const impactedS = schoolsData.filter(s => badZoneIds.has(s.zone_id));
  
  // Estimate affected roads based on bad zones
  const affectedRoadsCount = Math.round(badZoneIds.size * 2.8);

  const impact = {
    counts: {
      threatened_hospitals: threatenedH.length,
      impacted_schools: impactedS.length,
      affected_roads: affectedRoadsCount,
      critical_zones: scoredZones.filter(z => z.risk_class === "critical").length,
      high_zones: scoredZones.filter(z => z.risk_class === "high").length,
      medium_zones: scoredZones.filter(z => z.risk_class === "medium").length,
      low_zones: scoredZones.filter(z => z.risk_class === "low").length,
      total_beds_at_risk: threatenedH.reduce((acc, h) => acc + (h.beds || 150), 0),
      shelter_capacity: impactedS.reduce((acc, s) => acc + (s.capacity || 500), 0)
    },
    threatened_hospitals: threatenedH,
    impacted_schools: impactedS
  };

  // Multi-label Action Planner mock generator
  const plan = [];
  scoredZones.forEach(z => {
    const places = DEFAULT_AFFECTED_PLACES[z.zone_id] || {};
    
    // Evaluate 6 actions with probability
    if (z.risk >= 0.70 || river_norm >= 0.85) {
      const prob = Math.min(0.98, 0.65 + z.risk * 0.3);
      plan.push({
        zone: z.name, zone_id: z.zone_id, action: "Evacuation",
        confidence: parseFloat(prob.toFixed(2)), confidence_pct: Math.round(prob * 100),
        priority: parseFloat((prob * z.risk).toFixed(3)),
        places: places["Evacuation"] || "Riverbank colonies",
        icon: "🚨", severity: "critical", type: "Life Safety"
      });
    }

    if (z.risk >= 0.55 || (z.risk >= 0.45 && z.n_schools > 8)) {
      const prob = Math.min(0.96, 0.55 + z.risk * 0.35);
      plan.push({
        zone: z.name, zone_id: z.zone_id, action: "Open shelters",
        confidence: parseFloat(prob.toFixed(2)), confidence_pct: Math.round(prob * 100),
        priority: parseFloat((prob * z.risk).toFixed(3)),
        places: places["Open shelters"] || "Relief camps & schools",
        icon: "🏫", severity: "high", type: "Relief"
      });
    }

    if (z.elevation_m < 15 && rain_hazard > 0.45 && z.risk > 0.38) {
      const prob = Math.min(0.92, 0.45 + rain_hazard * 0.4);
      plan.push({
        zone: z.name, zone_id: z.zone_id, action: "Deploy pumps",
        confidence: parseFloat(prob.toFixed(2)), confidence_pct: Math.round(prob * 100),
        priority: parseFloat((prob * z.risk).toFixed(3)),
        places: places["Deploy pumps"] || "Subways and bus stand underpasses",
        icon: "🚜", severity: "medium", type: "Drainage"
      });
    }

    if (z.road_vuln > 0.55 && z.risk > 0.55) {
      const prob = Math.min(0.95, 0.50 + z.risk * 0.4);
      plan.push({
        zone: z.name, zone_id: z.zone_id, action: "Close roads",
        confidence: parseFloat(prob.toFixed(2)), confidence_pct: Math.round(prob * 100),
        priority: parseFloat((prob * z.risk).toFixed(3)),
        places: places["Close roads"] || "Inundated bridge approaches",
        icon: "🚧", severity: "high", type: "Traffic Control"
      });
    }

    if (z.n_hospitals > 0 && z.risk > 0.42) {
      const prob = Math.min(0.95, 0.40 + z.risk * 0.45);
      plan.push({
        zone: z.name, zone_id: z.zone_id, action: "Alert hospitals",
        confidence: parseFloat(prob.toFixed(2)), confidence_pct: Math.round(prob * 100),
        priority: parseFloat((prob * z.risk).toFixed(3)),
        places: places["Alert hospitals"] || "District Hospitals",
        icon: "🏥", severity: "critical", type: "Healthcare"
      });
    }

    if (z.risk > 0.32) {
      const prob = Math.min(0.99, 0.50 + z.risk * 0.45);
      plan.push({
        zone: z.name, zone_id: z.zone_id, action: "Public alert",
        confidence: parseFloat(prob.toFixed(2)), confidence_pct: Math.round(prob * 100),
        priority: parseFloat((prob * z.risk).toFixed(3)),
        places: places["Public alert"] || "Municipal ward broadcast system",
        icon: "📢", severity: "medium", type: "Warning"
      });
    }
  });

  plan.sort((a, b) => b.priority - a.priority);

  return {
    zones: scoredZones,
    impact: impact,
    plan: plan
  };
}

// =====================================================================
// MAP RENDERING: POLYGONS, MARKERS, FLOODED ROADS
// =====================================================================
function renderMapPolygons(zones) {
  if (zoneLayer) {
    map.removeLayer(zoneLayer);
  }

  const zoneMap = new Map(zones.map(z => [z.zone_id, z]));

  zoneLayer = L.geoJSON(zonesGeoJSON, {
    style: (feature) => {
      const z = zoneMap.get(feature.properties.zone_id);
      const riskClass = z ? z.risk_class : "low";
      const color = COLORS[riskClass] || "#10b981";

      return {
        color: color,
        weight: 2,
        opacity: 0.9,
        fillColor: color,
        fillOpacity: riskClass === "critical" ? 0.65 : (riskClass === "high" ? 0.50 : 0.35)
      };
    },
    onEachFeature: (feature, layer) => {
      const z = zoneMap.get(feature.properties.zone_id);
      if (!z) return;

      const riskClass = z.risk_class.toUpperCase();
      const color = COLORS[z.risk_class];

      // Custom Dark Popup Content
      const popupHtml = `
        <div class="custom-popup-box">
          <h4>${z.name} (${z.zone_id})</h4>
          <span class="popup-risk-badge" style="background:${color}22; color:${color}; border:1px solid ${color}66;">
            RISK: ${z.risk} (${riskClass})
          </span>
          <div class="popup-row"><span>Mean Elevation:</span> <b>${z.elevation_m} m</b></div>
          <div class="popup-row"><span>River Proximity:</span> <b>${Math.round(z.river_prox * 100)}%</b></div>
          <div class="popup-row"><span>Historical 2018 Risk:</span> <b>${z.hist_risk}</b></div>
          <div class="popup-row"><span>Critical Facilities:</span> <b>${z.n_hospitals} Hosps · ${z.n_schools} Camps</b></div>
        </div>
      `;
      layer.bindPopup(popupHtml);

      // Hover and Click interactions
      layer.on({
        mouseover: (e) => {
          const l = e.target;
          l.setStyle({ weight: 4, fillOpacity: 0.75 });
          showInspector(z);
        },
        mouseout: (e) => {
          zoneLayer.resetStyle(e.target);
        },
        click: () => {
          showInspector(z);
        }
      });
    }
  }).addTo(map);
}

function escapeQuotes(str) {
  return String(str).replace(/'/g, "\\'").replace(/"/g, "&quot;");
}

function renderFacilityMarkers(zones) {
  hospitalMarkersLayer.clearLayers();
  schoolMarkersLayer.clearLayers();

  const zoneMap = new Map(zones.map(z => [z.zone_id, z]));

  // Hospitals
  hospitalsData.forEach(h => {
    const z = zoneMap.get(h.zone_id);
    const isAtRisk = z && (z.risk_class === "high" || z.risk_class === "critical");
    const pulsingClass = isAtRisk ? "pulsing" : "";

    const customIcon = L.divIcon({
      className: `custom-map-icon hospital-icon ${pulsingClass}`,
      html: `✚`,
      iconSize: [22, 22],
      iconAnchor: [11, 11]
    });

    const marker = L.marker([h.lat, h.lon], { icon: customIcon });
    marker.bindPopup(`
      <div class="custom-popup-box hospital-popup">
        <h4>🏥 ${h.name}</h4>
        <div class="popup-row"><span>Taluk Zone:</span> <b>${z ? z.name : h.zone_id}</b></div>
        <div class="popup-row"><span>Inpatient Beds:</span> <b>${h.beds || 200} Beds</b></div>
        <div class="popup-row"><span>Vulnerability:</span> <b style="color:${isAtRisk ? '#ef4444' : '#10b981'}">${isAtRisk ? 'THREATENED BY FLOOD' : 'SECURE / OPERATIONAL'}</b></div>
        <button class="btn-popup-nav" onclick="routeToFacility('${escapeQuotes(h.name)}', ${h.lat}, ${h.lon})">
          🚑 Route Emergency Transport Here
        </button>
      </div>
    `);
    hospitalMarkersLayer.addLayer(marker);
  });

  // Schools / Shelters
  schoolsData.forEach((s, idx) => {
    const z = zoneMap.get(s.zone_id);
    const isCritical = z && z.risk_class === "critical";
    const isHigh = z && z.risk_class === "high";
    const statusText = isCritical ? "CRITICAL HAZARD - SEVERED" : (isHigh ? "HIGH RISK - APPROACH CAUTIOUSLY" : "SAFE HAVEN - OPEN & ACCESSIBLE");
    const statusColor = isCritical ? "#ef4444" : (isHigh ? "#f97316" : "#10b981");

    const customIcon = L.divIcon({
      className: `custom-map-icon school-icon ${isCritical ? "danger-pulse" : ""}`,
      html: `🏫`,
      iconSize: [22, 22],
      iconAnchor: [11, 11]
    });

    const marker = L.marker([s.lat, s.lon], { icon: customIcon });
    marker.bindPopup(`
      <div class="custom-popup-box shelter-popup">
        <h4>🏫 ${s.name}</h4>
        <div class="popup-row"><span>Taluk Zone:</span> <b>${z ? z.name : s.zone_id}</b></div>
        <div class="popup-row"><span>Relief Capacity:</span> <b>${s.capacity || 800} Persons</b></div>
        <div class="popup-row"><span>Zone Risk:</span> <b style="color:${statusColor}">${z ? z.risk_class.toUpperCase() : 'NORMAL'} (${z ? z.risk.toFixed(2) : '0.20'})</b></div>
        <div class="popup-row"><span>Status:</span> <b style="color:${statusColor}">${statusText}</b></div>
        <button class="btn-popup-nav" onclick="routeToShelter('${escapeQuotes(s.name)}', ${s.lat}, ${s.lon}, '${s.zone_id}', ${idx})">
          🧭 Navigate Here (Safest & Shortest Route)
        </button>
      </div>
    `);
    schoolMarkersLayer.addLayer(marker);
  });
}

function renderFloodedRoads(zones) {
  floodedRoadsLayer.clearLayers();

  const criticalZoneIds = new Set(zones.filter(z => z.risk_class === "critical").map(z => z.zone_id));
  const highZoneIds = new Set(zones.filter(z => z.risk_class === "high").map(z => z.zone_id));

  // Strategic road corridors in Ernakulam
  const roadLinks = [
    { name: "Aluva Marthanda Varma Bridge", coords: [[10.1080, 76.3530], [10.1140, 76.3480]], zone: "Z01" },
    { name: "Aluva-Paravur Coastal Link", coords: [[10.1140, 76.3480], [10.1450, 76.2300]], zone: "Z01" },
    { name: "Varapuzha Bridge Causeway", coords: [[10.1450, 76.2300], [10.0760, 76.2750]], zone: "Z02" },
    { name: "Pathalam Bund & Eloor Bridge", coords: [[10.0760, 76.2750], [10.0530, 76.3210]], zone: "Z05" },
    { name: "Kalady Bridge (Periyar)", coords: [[10.1960, 76.3860], [10.1650, 76.4380]], zone: "Z06" },
    { name: "Muvattupuzha Kacherithazham Bridge", coords: [[9.9830, 76.5800], [10.0620, 76.6320]], zone: "Z07" }
  ];

  roadLinks.forEach(rd => {
    let isBlocked = criticalZoneIds.has(rd.zone);
    let isAtRisk = highZoneIds.has(rd.zone);

    if (isBlocked || isAtRisk) {
      const color = isBlocked ? "#ef4444" : "#f97316";
      const line = L.polyline(rd.coords, {
        color: color,
        weight: isBlocked ? 5 : 3.5,
        dashArray: isBlocked ? "6, 6" : "2, 4",
        opacity: 0.95
      });

      line.bindPopup(`
        <div class="custom-popup-box">
          <h4 style="color:${color}">⚠️ ${rd.name}</h4>
          <div class="popup-row"><span>Status:</span> <b style="color:${color}">${isBlocked ? 'CLOSED / SUBMERGED' : 'HAZARDOUS WATERLOGGING'}</b></div>
          <div class="popup-row"><span>Zone:</span> <b>${rd.zone}</b></div>
        </div>
      `);
      floodedRoadsLayer.addLayer(line);
    }
  });
}

// =====================================================================
// RIGHT PANEL RENDERING: IMPACT KPIS & ACTION PLAN
// =====================================================================
function renderImpactKPIs(impact) {
  const c = impact.counts || {};
  document.getElementById("threatenedHospCount").textContent = c.threatened_hospitals || 0;
  document.getElementById("threatenedBedsText").textContent = `${c.total_beds_at_risk || 0} Beds Monitored`;

  document.getElementById("impactedSchoolsCount").textContent = c.impacted_schools || 0;
  document.getElementById("shelterCapacityText").textContent = `Capacity: ${(c.shelter_capacity || 0).toLocaleString()} Pax`;

  document.getElementById("affectedRoadsCount").textContent = c.affected_roads || 0;
  document.getElementById("criticalRoadsText").textContent = `${c.critical_zones || 0} Critical Zones Inundated`;

  document.getElementById("criticalZonesCount").textContent = c.critical_zones || 0;
  document.getElementById("highZonesCountText").textContent = `${c.high_zones || 0} High Risk Zones`;
}

function renderActionPlan(plan) {
  const container = document.getElementById("actionPlanList");
  const badge = document.getElementById("actionCountBadge");

  badge.textContent = `${plan.length} ACTIONS`;

  if (!plan || plan.length === 0) {
    container.innerHTML = `
      <div class="plan-placeholder">
        <span class="placeholder-icon">✅</span>
        <p>No immediate emergency alerts triggered for current flood parameters.</p>
      </div>
    `;
    return;
  }

  // Display top prioritized actions
  const html = plan.slice(0, 8).map((a, idx) => {
    const sevClass = a.severity ? `severity-${a.severity}` : 'severity-medium';
    return `
      <div class="action-card ${sevClass}">
        <div class="action-card-top">
          <div class="action-name-wrap">
            <span class="action-icon">${a.icon || '⚡'}</span>
            <div>
              <div class="action-name">${a.action}</div>
              <div class="action-target-zone">📍 ${a.zone}</div>
            </div>
          </div>
          <div class="action-metrics-wrap">
            <span class="priority-pill">PRIORITY: ${a.priority}</span>
            <span class="confidence-rate">${a.confidence_pct}% confidence</span>
          </div>
        </div>

        <div class="action-places-box">
          <span class="places-label">TARGET SITES & BOTTLENECKS:</span>
          <span class="places-text">${a.places}</span>
        </div>

        <div class="action-card-footer">
          <span class="action-rank-tag">RANK #${idx + 1} (${a.type || 'SOP'})</span>
          <button class="btn-dispatch" onclick="dispatchAction('${a.action}', '${a.zone}')">
            DISPATCH ORDER
          </button>
        </div>
      </div>
    `;
  }).join("");

  container.innerHTML = html;
}

function dispatchAction(actionName, zoneName) {
  showToast(`🚨 DISPATCHED: [${actionName}] order sent to ${zoneName} Disaster Response Unit.`);
}

function showToast(message) {
  const toast = document.getElementById("toastNotification");
  const msgEl = document.getElementById("toastMessage");
  msgEl.textContent = message;
  toast.classList.remove("hidden");
  setTimeout(() => {
    toast.classList.add("hidden");
  }, 4000);
}

// =====================================================================
// BOTTOM PANEL: CHART.JS DATA VISUALIZATION
// =====================================================================
function initChart() {
  const ctx = document.getElementById("riskChart").getContext("2d");
  riskChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: [],
      datasets: [{
        label: "Risk Score (0 - 1.0)",
        data: [],
        backgroundColor: [],
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "rgba(15, 23, 42, 0.95)",
          titleColor: "#38bdf8",
          bodyColor: "#f8fafc",
          borderColor: "rgba(56, 189, 248, 0.3)",
          borderWidth: 1,
          padding: 10
        }
      },
      scales: {
        y: {
          min: 0,
          max: 1.0,
          grid: { color: "rgba(255, 255, 255, 0.06)" },
          ticks: { color: "#94a3b8", font: { family: "JetBrains Mono" } }
        },
        x: {
          grid: { display: false },
          ticks: { color: "#cbd5e1", font: { family: "Inter", weight: 600 } }
        }
      },
      onClick: (e, elements) => {
        if (elements.length > 0) {
          const idx = elements[0].index;
          const z = currentZonesData[idx];
          if (z) {
            map.flyTo([z.lat, z.lon], 12);
            showInspector(z);
          }
        }
      }
    }
  });
}

function updateChart(zones) {
  if (!riskChart) return;

  if (currentChartMode === 'risk') {
    riskChart.config.type = 'bar';
    riskChart.data = {
      labels: zones.map(z => z.name),
      datasets: [{
        label: "Hybrid Flood Risk Score",
        data: zones.map(z => z.risk),
        backgroundColor: zones.map(z => COLORS[z.risk_class]),
        borderRadius: 4
      }]
    };
    riskChart.options.scales.x.display = true;
    riskChart.options.scales.y.display = true;
    riskChart.options.scales.y.max = 1.0;
    riskChart.options.plugins.legend.display = false;
  } else if (currentChartMode === 'factors') {
    // Stacked factor breakdown
    riskChart.config.type = 'bar';
    const factorKeys = [
      { key: "rainfall", label: "Rainfall (28%)", color: "#38bdf8" },
      { key: "river", label: "River Level (20%)", color: "#0284c7" },
      { key: "historical", label: "2018 History (20%)", color: "#f97316" },
      { key: "elevation", label: "Low Elev (14%)", color: "#ef4444" },
      { key: "terrain", label: "Terrain (8%)", color: "#a855f7" },
      { key: "roads", label: "Roads (5%)", color: "#eab308" }
    ];

    riskChart.data = {
      labels: zones.map(z => z.name),
      datasets: factorKeys.map(fk => ({
        label: fk.label,
        data: zones.map(z => (z.factors ? z.factors[fk.key] : 0.05)),
        backgroundColor: fk.color
      }))
    };
    riskChart.options.scales.x.stacked = true;
    riskChart.options.scales.y.stacked = true;
    riskChart.options.scales.y.max = 1.0;
    riskChart.options.plugins.legend.display = true;
    riskChart.options.plugins.legend.labels = { color: "#cbd5e1", font: { size: 10 } };
  } else if (currentChartMode === 'dist') {
    // Doughnut distribution
    riskChart.config.type = 'doughnut';
    const counts = {
      Low: zones.filter(z => z.risk_class === "low").length,
      Medium: zones.filter(z => z.risk_class === "medium").length,
      High: zones.filter(z => z.risk_class === "high").length,
      Critical: zones.filter(z => z.risk_class === "critical").length
    };

    riskChart.data = {
      labels: ["Low Risk", "Medium Risk", "High Risk", "Critical Risk"],
      datasets: [{
        data: [counts.Low, counts.Medium, counts.High, counts.Critical],
        backgroundColor: [COLORS.low, COLORS.medium, COLORS.high, COLORS.critical]
      }]
    };
    riskChart.options.scales.x.display = false;
    riskChart.options.scales.y.display = false;
    riskChart.options.plugins.legend.display = true;
  }

  riskChart.update();
}

function switchChartTab(mode) {
  currentChartMode = mode;
  document.getElementById("chartTabZoneRisk").classList.toggle("active", mode === 'risk');
  document.getElementById("chartTabFactor").classList.toggle("active", mode === 'factors');
  document.getElementById("chartTabDistribution").classList.toggle("active", mode === 'dist');
  updateChart(currentZonesData);
}

function toggleDrawer(panelId) {
  const panel = document.getElementById(panelId);
  if (!panel) return;
  const shouldOpen = !panel.classList.contains("drawer-open");
  panel.classList.toggle("drawer-open", shouldOpen);

  if (panelId === "leftControlPanel") {
    document.body.classList.toggle("simulation-drawer-open", shouldOpen);
  }

  if (map) {
    window.setTimeout(() => map.invalidateSize(), 350);
  }
}

function closeDrawer(panelId) {
  const panel = document.getElementById(panelId);
  if (!panel) return;

  panel.classList.remove("drawer-open");
  if (panelId === "leftControlPanel") {
    document.body.classList.remove("simulation-drawer-open");
  }

  if (map) {
    window.setTimeout(() => map.invalidateSize(), 350);
  }
}

// =====================================================================
// CITIZEN ROUTING INTERFACE & A* SEARCH EXECUTION
// =====================================================================
function switchView(viewName) {
  const isCitizen = (viewName === 'citizen');
  document.body.classList.toggle("citizen-view", isCitizen);
  if (isCitizen) {
    document.body.classList.remove("route-results-mode");
  }
  document.getElementById("tabCommandBtn").classList.toggle("active", !isCitizen);
  document.getElementById("tabCitizenBtn").classList.toggle("active", isCitizen);
  document.getElementById("tabCommandBtn").setAttribute("aria-selected", String(!isCitizen));
  document.getElementById("tabCitizenBtn").setAttribute("aria-selected", String(isCitizen));

  const citizenCard = document.getElementById("citizenRouteCard");
  if (isCitizen) {
    citizenCard.classList.remove("hidden");
    fetchRoute();
  } else {
    citizenCard.classList.add("hidden");
    document.body.classList.remove("route-results-mode");
    document.getElementById("citizenAlertsCard").classList.add("hidden");
    clearRouteDisplays();
  }
}

let customMapOriginCoords = null;
let customMapDestCoords = null;
let currentGpsCoords = null;

function useGpsOrigin() {
  if (!navigator.geolocation) {
    showToast("⚠️ Geolocation is not supported by your browser.");
    return;
  }
  showToast("📡 Requesting device location...");
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const lat = pos.coords.latitude;
      const lon = pos.coords.longitude;
      currentGpsCoords = { lat, lon, name: "Your Current Location (GPS)" };
      const origSelect = document.getElementById("routeOriginSelect");
      origSelect.value = "GPS_CURRENT";
      showToast(`📍 GPS Location detected (${lat.toFixed(4)}, ${lon.toFixed(4)})`);
      fetchRoute();
    },
    (err) => {
      console.warn("GPS error:", err);
      showToast("⚠️ Could not retrieve GPS location. Using default origin.");
      document.getElementById("routeOriginSelect").value = "N_EKM_SOUTH";
      fetchRoute();
    },
    { timeout: 8000, enableHighAccuracy: true }
  );
}

function routeToShelter(name, lat, lon, zoneId, idx) {
  switchView('citizen');
  const destSelect = document.getElementById("routeDestSelect");
  const targetKey = `SHELTER_${idx}`;
  
  if (destSelect.querySelector(`option[value="${targetKey}"]`)) {
    destSelect.value = targetKey;
  } else {
    customMapDestCoords = { lat, lon, name: `Relief Shelter: ${name}`, isShelter: true };
    const customOpt = destSelect.querySelector('option[value="CUSTOM_MAP_DEST"]');
    if (customOpt) {
      customOpt.hidden = false;
      customOpt.disabled = false;
      customOpt.textContent = `🏫 ${name}`;
      destSelect.value = "CUSTOM_MAP_DEST";
    }
  }

  showToast(`🧭 Planned evacuation route to designated shelter: ${name}`);
  fetchRoute();
}

function routeToFacility(name, lat, lon) {
  switchView('citizen');
  const destSelect = document.getElementById("routeDestSelect");
  customMapDestCoords = { lat, lon, name: `Hospital: ${name}`, isFacility: true };
  const customOpt = destSelect.querySelector('option[value="CUSTOM_MAP_DEST"]');
  if (customOpt) {
    customOpt.hidden = false;
    customOpt.disabled = false;
    customOpt.textContent = `🏥 ${name}`;
    destSelect.value = "CUSTOM_MAP_DEST";
  }
  showToast(`🚑 Emergency transport route planned to: ${name}`);
  fetchRoute();
}

function resolveLocation(key, type) {
  if (key === "GPS_CURRENT") {
    if (currentGpsCoords) return currentGpsCoords;
    return { lat: 9.9680, lon: 76.2910, name: "Current Location (Ernakulam Central)" };
  }
  if (key === "CUSTOM_MAP_ORIGIN" && customMapOriginCoords) {
    return customMapOriginCoords;
  }
  if (key === "CUSTOM_MAP_DEST" && customMapDestCoords) {
    return customMapDestCoords;
  }
  if (key === "AUTO_NEAREST_SAFE") {
    const origKey = document.getElementById("routeOriginSelect").value;
    const origin = resolveLocation(origKey, "origin");
    return findNearestSafeShelterClient(origin.lat, origin.lon);
  }
  if (key && key.startsWith("SHELTER_")) {
    const idx = parseInt(key.replace("SHELTER_", ""), 10);
    const s = schoolsData[idx];
    if (s) {
      return { lat: s.lat, lon: s.lon, name: s.name, zone_id: s.zone_id, capacity: s.capacity, isShelter: true };
    }
  }
  if (ROAD_NODES[key]) {
    return ROAD_NODES[key];
  }
  return type === "origin" ? ROAD_NODES["N_EKM_SOUTH"] : (schoolsData[0] || ROAD_NODES["N_ALUVA_RSTN"]);
}

function findNearestSafeShelterClient(fromLat, fromLon) {
  let best = null;
  let minD = Infinity;
  const criticalZoneIds = new Set(currentZonesData.filter(z => z.risk_class === "critical").map(z => z.zone_id));

  // First priority: shelters NOT in critical zones
  schoolsData.forEach(s => {
    if (!criticalZoneIds.has(s.zone_id)) {
      const d = (s.lat - fromLat) ** 2 + (s.lon - fromLon) ** 2;
      if (d < minD) {
        minD = d;
        best = s;
      }
    }
  });

  // Fallback if all are critical: nearest shelter overall
  if (!best && schoolsData.length > 0) {
    schoolsData.forEach(s => {
      const d = (s.lat - fromLat) ** 2 + (s.lon - fromLon) ** 2;
      if (d < minD) {
        minD = d;
        best = s;
      }
    });
  }

  if (best) {
    return { lat: best.lat, lon: best.lon, name: `Nearest Safe: ${best.name}`, zone_id: best.zone_id, capacity: best.capacity, isShelter: true };
  }
  return { lat: 10.1240, lon: 76.3420, name: "UC College Aluva Relief Camp", isShelter: true };
}

function swapRouteEndpoints() {
  const orig = document.getElementById("routeOriginSelect");
  const dest = document.getElementById("routeDestSelect");
  const temp = orig.value;
  orig.value = dest.value;
  dest.value = temp;
  fetchRoute();
}

function onOriginSelectChange() {
  const val = document.getElementById("routeOriginSelect").value;
  if (val === "GPS_CURRENT" && !currentGpsCoords) {
    useGpsOrigin();
    return;
  }
  fetchRoute(false);
}

function onDestSelectChange() {
  fetchRoute(false);
}

function enableMapPick(targetType) {
  mapPickTarget = targetType;
  showToast(`📌 Click any location on the map to set Route ${targetType.toUpperCase()}.`);
}

function handleMapCoordinatePick(lat, lon) {
  if (mapPickTarget === 'origin') {
    customMapOriginCoords = { lat, lon, name: `Map Location (${lat.toFixed(4)}, ${lon.toFixed(4)})` };
    const origSelect = document.getElementById("routeOriginSelect");
    const opt = origSelect.querySelector('option[value="CUSTOM_MAP_ORIGIN"]');
    if (opt) {
      opt.hidden = false;
      opt.disabled = false;
      opt.textContent = `📌 Picked: ${lat.toFixed(4)}, ${lon.toFixed(4)}`;
      origSelect.value = "CUSTOM_MAP_ORIGIN";
    }
  } else if (mapPickTarget === 'dest') {
    customMapDestCoords = { lat, lon, name: `Map Target (${lat.toFixed(4)}, ${lon.toFixed(4)})` };
    const destSelect = document.getElementById("routeDestSelect");
    const opt = destSelect.querySelector('option[value="CUSTOM_MAP_DEST"]');
    if (opt) {
      opt.hidden = false;
      opt.disabled = false;
      opt.textContent = `📌 Picked: ${lat.toFixed(4)}, ${lon.toFixed(4)}`;
      destSelect.value = "CUSTOM_MAP_DEST";
    }
  }

  mapPickTarget = null;
  fetchRoute();
}

function generateClientCurvedGeometry(waypoints) {
  if (!waypoints || waypoints.length < 2) return waypoints || [];
  const out = [waypoints[0]];
  for (let i = 0; i < waypoints.length - 1; i++) {
    const [lat1, lon1] = waypoints[i];
    const [lat2, lon2] = waypoints[i + 1];
    const dlat = lat2 - lat1;
    const dlon = lon2 - lon1;
    const dist = Math.sqrt(dlat * dlat + dlon * dlon);
    if (dist < 1e-6) continue;

    const nlat = -dlon / dist;
    const nlon = dlat / dist;
    const curveAmp = Math.min(0.0028, dist * 0.08);
    const steps = 7;

    for (let s = 1; s < steps; s++) {
      const t = s / steps;
      const offset = Math.sin(t * Math.PI) * curveAmp;
      out.push([Number((lat1 + t * dlat + offset * nlat).toFixed(6)), Number((lon1 + t * dlon + offset * nlon).toFixed(6))]);
    }
    out.push([lat2, lon2]);
  }
  return out;
}

async function fetchRoute(hideFinder = false) {
  const origKey = document.getElementById("routeOriginSelect").value;
  const destKey = document.getElementById("routeDestSelect").value;

  const origNode = resolveLocation(origKey, "origin");
  const destNode = resolveLocation(destKey, "dest");

  if (!origNode || !destNode) return;

  const computeBtn = document.getElementById("computeRouteBtn");
  if (computeBtn) computeBtn.classList.add("loading");

  let routeResult = null;

  if (isBackendLive) {
    try {
      const url = `/route?from_lat=${origNode.lat}&from_lon=${origNode.lon}&to_lat=${destNode.lat}&to_lon=${destNode.lon}`;
      const res = await fetch(url);
      if (res.ok) {
        routeResult = await res.json();
      }
    } catch (err) {
      console.warn("Backend route fetch failed, running client A* routing with road geometry.", err);
    }
  }

  if (!routeResult) {
    routeResult = routeMock(origNode, destNode);
  }

  if (computeBtn) computeBtn.classList.remove("loading");
  renderRouteOnMap(routeResult, origNode, destNode);
  if (hideFinder) {
    document.body.classList.add("route-results-mode");
  }
}

function showRouteFinder() {
  document.body.classList.remove("route-results-mode");
  document.getElementById("citizenRouteCard").classList.remove("hidden");
  if (map) {
    window.setTimeout(() => map.invalidateSize(), 200);
  }
}

function hideRouteFinder() {
  if (!document.body.classList.contains("citizen-view")) return;
  document.body.classList.add("route-results-mode");
  if (map) {
    window.setTimeout(() => map.invalidateSize(), 200);
  }
}

// Client-side road-network fallback used when the API is unavailable.
function routeMock(orig, dest) {
  // Critical zones from current simulation
  const criticalZones = new Set(currentZonesData.filter(z => z.risk_class === "critical").map(z => z.zone_id));

  const shortest = findClientRoadPath(orig, dest, false, criticalZones);
  const safest = findClientRoadPath(orig, dest, true, criticalZones);
  const shortestDistKm = shortest.distanceKm;
  const safeDistKm = safest.distanceKm;
  const safestStatus = safest.path.length > 0 ? "success" : "no_safe_path";
  const chokepointsAvoided = shortest.blockedEdges;

  return {
    safest: {
      status: safestStatus,
      coordinates: safest.coordinates,
      distance_km: safeDistKm,
      duration_minutes: Math.round((safeDistKm / 35.0) * 60),
      message: safestStatus === "success" ? "Safe evacuation corridor active." : "Destination cut off by critical flood waters.",
      road_names: safest.roadNames
    },
    shortest: {
      status: "success",
      coordinates: shortest.coordinates,
      distance_km: shortestDistKm,
      duration_minutes: Math.round((shortestDistKm / 35.0) * 60),
      road_names: shortest.roadNames,
      blocked_chokepoints_crossed: chokepointsAvoided,
      is_submerged: chokepointsAvoided > 0
    },
    tradeoff: {
      extra_distance_km: Math.max(0, parseFloat((safeDistKm - shortestDistKm).toFixed(1))),
      risk_reduction_pct: shortest.avgRisk > 0
        ? Math.max(0, Math.round((1 - safest.avgRisk / shortest.avgRisk) * 100))
        : 65,
      critical_chokepoints_avoided: chokepointsAvoided
    }
  };
}

function findClientRoadPath(orig, dest, safe, criticalZones) {
  if (!roadGraphData || !roadGraphData.nodes || !roadGraphData.edges) {
    const rawWaypoints = [[orig.lat, orig.lon], [dest.lat, dest.lon]];
    const curved = generateClientCurvedGeometry(rawWaypoints);
    const dKm = Number((Math.sqrt((orig.lat - dest.lat)**2 + (orig.lon - dest.lon)**2) * 111).toFixed(2));
    return {
      path: ["START", "TARGET"],
      coordinates: curved,
      distanceKm: dKm,
      avgRisk: safe ? 0.15 : 0.45,
      roadNames: ["District Evacuation Corridor"],
      blockedEdges: 0
    };
  }

  const nodes = roadGraphData.nodes;
  const adjacency = Object.fromEntries(Object.keys(nodes).map(id => [id, []]));
  roadGraphData.edges.forEach(edge => {
    const risk = currentZonesData.find(z => z.zone_id === edge.zone_id)?.risk || 0.2;
    const blocked = criticalZones.has(edge.zone_id);
    const weight = Number(edge.length) * (safe ? 1 + 4 * risk : 1);
    adjacency[edge.u]?.push({ node: edge.v, length: Number(edge.length), weight, blocked, name: edge.name });
    adjacency[edge.v]?.push({ node: edge.u, length: Number(edge.length), weight, blocked, name: edge.name });
  });

  const start = nearestClientRoadNode(orig);
  const end = nearestClientRoadNode(dest);
  const distances = { [start]: 0 };
  const previous = {};
  const pending = new Set(Object.keys(nodes));

  while (pending.size) {
    let current = null;
    let best = Infinity;
    pending.forEach(node => {
      if ((distances[node] ?? Infinity) < best) {
        best = distances[node];
        current = node;
      }
    });
    if (!current || current === end) break;
    pending.delete(current);

    (adjacency[current] || []).forEach(edge => {
      if (safe && edge.blocked) return;
      const nextDistance = distances[current] + edge.weight;
      if (nextDistance < (distances[edge.node] ?? Infinity)) {
        distances[edge.node] = nextDistance;
        previous[edge.node] = { node: current, edge };
      }
    });
  }

  if (!(end in distances)) {
    return { path: [], coordinates: [], distanceKm: 0, avgRisk: 0, roadNames: [], blockedEdges: 0 };
  }

  const path = [];
  const edges = [];
  let cursor = end;
  while (cursor) {
    path.unshift(cursor);
    if (previous[cursor]) {
      edges.unshift(previous[cursor].edge);
      cursor = previous[cursor].node;
    } else {
      cursor = null;
    }
  }

  const length = edges.reduce((sum, edge) => sum + edge.length, 0);
  const avgRisk = edges.length
    ? edges.reduce((sum, edge) => sum + (edge.blocked ? 1 : edge.weight / edge.length - 1) / 4, 0) / edges.length
    : 0;

  // Build full waypoint chain: Origin -> path nodes -> Destination
  const waypoints = [[orig.lat, orig.lon]];
  path.forEach(n => {
    if (nodes[n]) waypoints.push([nodes[n].lat, nodes[n].lon]);
  });
  waypoints.push([dest.lat, dest.lon]);

  const curvedCoords = generateClientCurvedGeometry(waypoints);

  return {
    path,
    coordinates: curvedCoords,
    distanceKm: Number(((length + 1500) / 1000).toFixed(2)),
    avgRisk,
    roadNames: [...new Set(edges.map(edge => edge.name).filter(Boolean))],
    blockedEdges: edges.filter(edge => edge.blocked).length
  };
}

function nearestClientRoadNode(point) {
  if (!roadGraphData || !roadGraphData.nodes) return "N_EKM_SOUTH";
  return Object.entries(roadGraphData.nodes).reduce((nearest, [id, node]) => {
    const distance = (node.lat - point.lat) ** 2 + (node.lon - point.lon) ** 2;
    return distance < nearest.distance ? { id, distance } : nearest;
  }, { id: "N_EKM_SOUTH", distance: Infinity }).id;
}

function renderRouteOnMap(routeData, origNode, destNode) {
  clearRouteDisplays();
  latestRouteData = routeData;

  const tradeoffBox = document.getElementById("routeTradeoffCard");
  tradeoffBox.classList.remove("hidden");

  const safeDistEl = document.getElementById("safeDistText");
  const safeDurationEl = document.getElementById("safeDurationText");
  const safeStatusTag = document.getElementById("safeStatusTag");

  const shortDistEl = document.getElementById("shortDistText");
  const shortDurationEl = document.getElementById("shortDurationText");
  const shortStatusTag = document.getElementById("shortStatusTag");
  const shortHazardLabel = document.getElementById("shortHazardLabel");

  const diffKmEl = document.getElementById("diffKmText");
  const riskReductionEl = document.getElementById("riskReductionText");
  const avoidedEl = document.getElementById("avoidedChokepointsText");
  const noticeEl = document.getElementById("routeNoticeText");

  const safest = routeData.safest || {};
  const shortest = routeData.shortest || {};
  const tradeoff = routeData.tradeoff || {};
  const shortIsHazardous = tradeoff.critical_chokepoints_avoided > 0 || shortest.is_submerged;
  selectRoute(selectedRoute, false);

  const safeDuration = safest.duration_minutes || (safest.distance_km ? Math.round((safest.distance_km / 35) * 60) : 0);
  const shortDuration = shortest.duration_minutes || (shortest.distance_km ? Math.round((shortest.distance_km / 35) * 60) : 0);

  safeDistEl.textContent = `${safest.distance_km || 0} km`;
  if (safeDurationEl) safeDurationEl.textContent = `~${safeDuration} mins`;

  shortDistEl.textContent = `${shortest.distance_km || 0} km`;
  if (shortDurationEl) shortDurationEl.textContent = `~${shortDuration} mins`;

  diffKmEl.textContent = `+${tradeoff.extra_distance_km || 0} km`;
  if (riskReductionEl) riskReductionEl.textContent = `${tradeoff.risk_reduction_pct || 65}% Safer`;
  avoidedEl.textContent = `${tradeoff.critical_chokepoints_avoided || 0} Chokepoints`;

  // Draw Origin Marker
  originMarker = L.marker([origNode.lat, origNode.lon], {
    icon: L.divIcon({
      className: "custom-map-icon origin-marker-pulse",
      html: `📍`,
      iconSize: [26, 26],
      iconAnchor: [13, 26]
    })
  }).bindPopup(`
    <div class="custom-popup-box">
      <h4>📍 TRIP ORIGIN</h4>
      <b>${origNode.name}</b>
    </div>
  `).addTo(map);

  // Draw Destination Marker
  const isShelter = destNode.isShelter || destNode.name.toLowerCase().includes("camp") || destNode.name.toLowerCase().includes("college") || destNode.name.toLowerCase().includes("shelter") || destNode.name.toLowerCase().includes("school");
  destMarker = L.marker([destNode.lat, destNode.lon], {
    icon: L.divIcon({
      className: "custom-map-icon dest-marker-glow",
      html: isShelter ? `🏫` : `🏁`,
      iconSize: [26, 26],
      iconAnchor: [13, 26]
    })
  }).bindPopup(`
    <div class="custom-popup-box">
      <h4>${isShelter ? '🏫 DESIGNATED RELIEF SHELTER' : '🏁 EVACUATION DESTINATION'}</h4>
      <b>${destNode.name}</b>
      ${destNode.capacity ? `<div>Capacity: <b>${destNode.capacity} evacuees</b></div>` : ''}
    </div>
  `).addTo(map);

  const shortestIsAvailable = shortest.coordinates && shortest.coordinates.length > 0;
  const safestIsAvailable = safest.status === "success" && safest.coordinates && safest.coordinates.length > 0;

  // Keep both alternatives visible, like a directions map. The selected route
  // is emphasized while the other route remains available for comparison.
  if (shortestIsAvailable) {
    const shortLine = L.polyline(shortest.coordinates, {
      color: shortIsHazardous ? "#ef4444" : "#38bdf8",
      weight: selectedRoute === "short" ? 6 : 4,
      dashArray: "8, 8",
      opacity: selectedRoute === "short" ? 0.98 : 0.58
    });
    shortLine.on("click", () => selectRoute("short"));
    shortestRouteLayer.addLayer(shortLine);
    shortestRouteLayer.addLayer(createRouteLabel(shortest.coordinates, "SHORTEST", "short", shortIsHazardous));
  }

  if (safestIsAvailable) {
    safeDistEl.textContent = `${safest.distance_km} km`;
    const safeLine = L.polyline(safest.coordinates, {
      color: "#38bdf8",
      weight: selectedRoute === "safe" ? 7 : 5,
      opacity: selectedRoute === "safe" ? 1 : 0.62
    });
    safeLine.on("click", () => selectRoute("safe"));
    safestRouteLayer.addLayer(safeLine);
    safestRouteLayer.addLayer(createRouteLabel(safest.coordinates, "SAFEST", "safe"));
  }

  // Report each route's actual state independently of which route is selected.
  if (safeStatusTag) {
    safeStatusTag.className = safestIsAvailable ? "route-status-tag safe-tag" : "route-status-tag warning-tag";
    safeStatusTag.textContent = safestIsAvailable ? "PASSABLE VIA BYPASS" : "SEVERED BY FLOOD";
  }
  if (shortStatusTag) {
    shortStatusTag.className = shortIsHazardous ? "route-status-tag warning-tag" : "route-status-tag safe-tag";
    shortStatusTag.textContent = shortIsHazardous ? "SUBMERGED / HAZARDOUS" : "PASSABLE";
    if (shortHazardLabel) {
      shortHazardLabel.textContent = shortIsHazardous
        ? `Crosses ${tradeoff.critical_chokepoints_avoided || 1} inundated corridor(s)`
        : "Direct path clear of flooding";
    }
  }

  const activeLayer = selectedRoute === "short" ? shortestRouteLayer : safestRouteLayer;
  const activeLine = activeLayer.getLayers().find(layer => typeof layer.getBounds === "function");
  if (activeLine) {
    map.fitBounds(activeLine.getBounds(), { padding: [50, 50] });
  }

  if (selectedRoute === "short") {
    noticeEl.innerHTML = `
      ${shortest.is_submerged ? "⚠️" : "✅"} <b>Shortest Route selected to ${destNode.name}:</b>
      ${shortest.is_submerged ? "Crosses flood-affected corridors. Use only if conditions permit." : "Direct path with no critical flood chokepoints."}
      Estimated travel time: <b>${shortDuration} minutes</b>.
    `;
  } else if (safestIsAvailable) {
    noticeEl.innerHTML = `
      ✅ <b>Safest Route selected to ${destNode.name}:</b> Circumvents ${tradeoff.critical_chokepoints_avoided || 1} inundated road link(s)
      via higher elevation arterial bypasses. Flood hazard reduction: <b>${tradeoff.risk_reduction_pct || 65}%</b>.
      Estimated travel time: <b>${safeDuration} minutes</b>. Passable for civilian vehicles.
    `;
  } else {
    safeDistEl.textContent = "CUT OFF";
    noticeEl.innerHTML = `
      🚨 <b style="color:#ef4444">EVACUATION HAZARD:</b> All direct overland corridors to <b>${destNode.name}</b>
      are severed by severe flood inundation. Divert to another designated relief shelter or request rescue boats.
    `;
  }

  renderCitizenAlerts(destNode);
}

function createRouteLabel(coordinates, label, routeType, isHazardous = false) {
  const midpoint = coordinates[Math.floor(coordinates.length / 2)];
  return L.marker(midpoint, {
    interactive: true,
    icon: L.divIcon({
      className: `route-map-label ${routeType}-route-label${isHazardous ? " hazard-route-label" : ""}`,
      html: `<span>${label}</span>`,
      iconSize: [92, 28],
      iconAnchor: [46, 14]
    })
  }).on("click", () => selectRoute(routeType));
}

function selectRoute(routeType, redraw = true) {
  selectedRoute = routeType === "short" ? "short" : "safe";
  document.getElementById("safeRouteOption").classList.toggle("selected", selectedRoute === "safe");
  document.getElementById("shortRouteOption").classList.toggle("selected", selectedRoute === "short");

  if (redraw && latestRouteData) {
    const origin = resolveLocation(document.getElementById("routeOriginSelect").value, "origin");
    const destination = resolveLocation(document.getElementById("routeDestSelect").value, "destination");
    renderRouteOnMap(latestRouteData, origin, destination);
  }
}

function renderCitizenAlerts(destNode) {
  const card = document.getElementById("citizenAlertsCard");
  const list = document.getElementById("citizenAlertsList");
  const destinationZone = destNode.zone_id;
  const nearbyAlerts = currentPlanData
    .filter(action => !destinationZone || action.zone_id === destinationZone)
    .slice(0, 3);

  card.classList.remove("hidden");
  if (!nearbyAlerts.length) {
    list.innerHTML = `<p class="citizen-alert-empty">No active flood alerts reported near this destination.</p>`;
    return;
  }

  list.innerHTML = nearbyAlerts.map(action => `
    <div class="citizen-alert-item">
      <span class="citizen-alert-icon">${action.icon || "⚠️"}</span>
      <div>
        <strong>${action.action}</strong>
        <span>${action.zone}: ${action.places}</span>
      </div>
    </div>
  `).join("");
}

function toggleFloodedRoadsLayer() {
  const btn = document.getElementById("filterFloodedBtn");
  const isVisible = map.hasLayer(floodedRoadsLayer);
  if (isVisible) {
    map.removeLayer(floodedRoadsLayer);
    if (btn) btn.classList.remove("active-filter");
  } else {
    map.addLayer(floodedRoadsLayer);
    if (btn) btn.classList.add("active-filter");
  }
}

function clearRouteDisplays() {
  safestRouteLayer.clearLayers();
  shortestRouteLayer.clearLayers();
  if (originMarker) map.removeLayer(originMarker);
  if (destMarker) map.removeLayer(destMarker);
}

// =====================================================================
// UI HELPERS, PRESETS & SLIDER HANDLERS
// =====================================================================
function updateRainDisplay(val) {
  document.getElementById("rainValDisplay").textContent = `${val} mm`;
  const pill = document.getElementById("rainIntensityPill");

  if (val >= 600) {
    pill.innerHTML = `<span class="intensity-label" style="color:#ef4444">🚨 Catastrophic Inundation (2018 Level)</span>`;
  } else if (val >= 350) {
    pill.innerHTML = `<span class="intensity-label" style="color:#f97316">⚠️ Extremely Heavy Monsoon Deluge</span>`;
  } else if (val >= 150) {
    pill.innerHTML = `<span class="intensity-label" style="color:#f59e0b">🌧️ Heavy Monsoon Showers</span>`;
  } else {
    pill.innerHTML = `<span class="intensity-label" style="color:#10b981">🌤️ Moderate / Normal Rainfall</span>`;
  }

  if (autoSimActive) runSimulation();
}

function updateRiverDisplay(val) {
  document.getElementById("riverValDisplay").textContent = `${parseFloat(val).toFixed(1)} m`;
  const pill = document.getElementById("riverIntensityPill");

  if (val >= 10.0) {
    pill.innerHTML = `<span class="intensity-label" style="color:#ef4444">🚨 Severe Barrage Overflow / Dam Breach</span>`;
  } else if (val >= 7.0) {
    pill.innerHTML = `<span class="intensity-label" style="color:#f97316">⚠️ Flood Warning Level Surpassed</span>`;
  } else if (val >= 4.0) {
    pill.innerHTML = `<span class="intensity-label" style="color:#f59e0b">🌊 Alert Flow Stage</span>`;
  } else {
    pill.innerHTML = `<span class="intensity-label" style="color:#10b981">💧 Normal Controlled Baseflow</span>`;
  }

  if (autoSimActive) runSimulation();
}

function applyPreset(presetType) {
  const rainSlider = document.getElementById("rainSlider");
  const riverSlider = document.getElementById("riverSlider");

  if (presetType === '2018') {
    rainSlider.value = 750;
    riverSlider.value = 12.0;
  } else if (presetType === 'flash') {
    rainSlider.value = 450;
    riverSlider.value = 8.5;
  } else if (presetType === 'monsoon') {
    rainSlider.value = 120;
    riverSlider.value = 3.5;
  } else if (presetType === 'dry') {
    rainSlider.value = 15;
    riverSlider.value = 1.2;
  }

  updateRainDisplay(rainSlider.value);
  updateRiverDisplay(riverSlider.value);
  runSimulation();
}

function toggleAutoSim(isChecked) {
  autoSimActive = isChecked;
}

function toggleMapLayer(layerName, isVisible) {
  if (layerName === 'zones' && zoneLayer) {
    if (isVisible) map.addLayer(zoneLayer); else map.removeLayer(zoneLayer);
  } else if (layerName === 'hospitals' && hospitalMarkersLayer) {
    if (isVisible) map.addLayer(hospitalMarkersLayer); else map.removeLayer(hospitalMarkersLayer);
  } else if (layerName === 'schools' && schoolMarkersLayer) {
    if (isVisible) map.addLayer(schoolMarkersLayer); else map.removeLayer(schoolMarkersLayer);
  } else if (layerName === 'roads' && floodedRoadsLayer) {
    if (isVisible) map.addLayer(floodedRoadsLayer); else map.removeLayer(floodedRoadsLayer);
  }
}

function toggleHospitalLayers() {
  const toggle = document.getElementById("layerHospitalsToggle");
  toggle.checked = !toggle.checked;
  toggleMapLayer('hospitals', toggle.checked);
}

function toggleShelterLayers() {
  const toggle = document.getElementById("layerSchoolsToggle");
  toggle.checked = !toggle.checked;
  toggleMapLayer('schools', toggle.checked);
}

function resetMapCenter() {
  map.flyTo([10.07, 76.38], 10);
}

function toggleWeightsInfo() {
  const content = document.getElementById("weightsContent");
  const chevron = document.getElementById("weightsChevron");
  content.classList.toggle("hidden");
  chevron.textContent = content.classList.contains("hidden") ? "▼" : "▲";
}

function showInspector(zone) {
  const bar = document.getElementById("zoneInspectorBar");
  document.getElementById("inspectorZoneName").textContent = `${zone.name} (${zone.zone_id})`;
  
  const riskPill = document.getElementById("inspectorRiskPill");
  const color = COLORS[zone.risk_class];
  riskPill.style.background = `${color}22`;
  riskPill.style.color = color;
  riskPill.style.borderColor = `${color}66`;
  riskPill.textContent = `${zone.risk_class.toUpperCase()} (${zone.risk})`;

  document.getElementById("inspectorElev").textContent = `${zone.elevation_m}m`;
  document.getElementById("inspectorProx").textContent = `${Math.round(zone.river_prox * 100)}%`;
  document.getElementById("inspectorHosps").textContent = zone.n_hospitals;
  document.getElementById("inspectorSchools").textContent = zone.n_schools;

  bar.classList.remove("hidden");
}

function closeInspector() {
  document.getElementById("zoneInspectorBar").classList.add("hidden");
}
