# Kerala Resilience OS 🛡️🌊
### Flood Emergency Command Center and Decision-Support System
**Study Area:** Ernakulam District, Kerala, India  
**Stack:** Python 3.13+, FastAPI, NetworkX, Leaflet.js, Chart.js, HTML5, Vanilla CSS  
**Machine Learning:** Gradient Boosting Regressor (Risk Refinement), Random Forest Multi-label Classifier (Action Planner), A* Search (Risk-Weighted Routing)

---

## 🌟 Overview & Key Capabilities

Kerala Resilience OS converts two simple flood parameters—**Rainfall (mm/24h)** and **River Water Level (m)**—into immediate, explainable, actionable disaster command intelligence.

1. **Hybrid Flood Risk Engine**:
   - **Stage A**: Gradient Boosting Classifier trained on 118 years of historical Kerala rainfall data (1901–2018).
   - **Stage B**: Transparent, explainable hydrological formula combining rainfall, river level, 2018 historical severity, low-elevation vulnerability, terrain, road network exposure, and river proximity.
   - **Stage C**: Gradient Boosting Regressor modeling non-linear interactions (e.g. synergistic hazard when low elevation, high river level, and torrential rainfall coincide).
   - **Risk Classes**: `Low` (<0.35), `Medium` (0.35–0.54), `High` (0.55–0.74), `Critical` (≥0.75).

2. **Action Planner (Multi-Label Random Forest)**:
   - Self-trained multi-label classifier producing probabilities for 6 key SOP actions:
     - `🚨 Evacuation`
     - `🏫 Open shelters`
     - `🚜 Deploy pumps`
     - `🚧 Close roads`
     - `🏥 Alert hospitals`
     - `📢 Public alert`
   - Dynamically ranks actions by **$\text{Priority} = \text{Action Confidence} \times \text{Zone Risk}$** and binds specific local place names and bottlenecks (e.g., Aluva Manappuram, UC College Aluva, Varapuzha Bridge, MG Road, etc.).

3. **Spatial Facility Impact Analysis**:
   - Tracks 18+ major hospitals and 20+ designated relief shelter institutions across Ernakulam district.
   - Dynamically flags threatened hospitals (with bed counts) and impacted schools/camps in high or critical zones.

4. **Citizen Safe Evacuation Routing with A* Search**:
   - Compares **Safest Route** (risk-weighted edges with critical inundated road segments blocked) vs. **Shortest Route** (raw physical distance).
   - Quantifies trade-offs in real time: distance delta (+km), flood risk reduction percentage, and blocked chokepoints avoided.
   - Includes emergency warnings when destinations are severed by flood waters.

5. **Dual Architecture (Live API + Standalone Offline Engine)**:
   - Live mode connects to the high-performance Python FastAPI backend (`/simulate`, `/route`, `/zones`).
   - If offline or backend is stopped, `app.js` runs a complete client-side simulation engine so the dashboard functions seamlessly anywhere.

---

## 📁 Project Structure

```
Hackverse'26/
├── backend/
│   ├── __init__.py
│   ├── config.py              # Formula weights, thresholds, paths
│   ├── ml_models.py           # Pure-NumPy resilient GBR, GBC & Multi-Label RF engines
│   ├── risk_engine.py         # Hybrid formula + GBR risk engine
│   ├── action_planner.py      # Random Forest multi-label action prioritization
│   ├── impact.py              # Facility impact & road link analyzer
│   ├── routing.py             # NetworkX A* routing with risk penalties
│   └── main.py                # FastAPI endpoints & static file serving
├── data/
│   ├── raw/                   # Historical Kerala rainfall, water levels, DEM
│   └── processed/
│       ├── zones_features.csv # 10 Ernakulam strategic zones table
│       ├── zones.geojson      # Ernakulam taluk boundaries
│       ├── hospitals.csv      # Critical emergency hospitals
│       ├── schools.csv        # Relief shelter schools & colleges
│       ├── road_graph.json    # Road network nodes & edges
│       └── road_graph.graphml # NetworkX graph file
├── models/
│   ├── rain_hazard.joblib     # Stage A rainfall hazard model
│   ├── risk_gbr.joblib        # Stage C risk refinement model
│   └── action_rf.joblib       # Module 3 action planner model
├── training/
│   ├── build_features.py      # Generates processed spatial datasets
│   ├── train_rain_model.py    # Trains Stage A rainfall model
│   ├── train_risk_model.py    # Trains Stage C GBR refiner
│   ├── make_synthetic_actions.py # Generates synthetic SOP scenarios
│   └── train_action_model.py  # Trains Module 3 action planner
├── frontend/
│   ├── index.html             # Tactical dark-mode command center UI
│   ├── style.css              # Glassmorphic CSS design system
│   └── app.js                 # Leaflet, Chart.js & simulation client logic
├── tests/
│   ├── test_api.py            # Automated test suite (all 7 checklist tests)
└── README.md
```

---

## 🚀 Running the Project

### First-time setup (Windows)

1. Install **Python 3.13 or newer** and make sure the Python launcher (`py`) is available.
2. Clone or download this repository, then open PowerShell in the project folder:

```powershell
cd D:\Coding\Kerala_resilience_os
```

3. Create a virtual environment:

```powershell
py -3.13 -m venv .venv
```

If your installed Python version is different, replace `3.13` with that version.

4. Activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, either run the commands below using the explicit
`.venv\Scripts\python.exe` path or allow local scripts for your user:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

5. Install the project dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

6. Create the local environment file:

```powershell
Copy-Item .env.example .env
```

The default configuration is sufficient for local use. Keep `.env` private; it
is ignored by Git. A `CARTO_API_KEY` is optional because the map has a fallback
tile provider.

### 1. Run the FastAPI Backend Server
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
Open your browser and navigate to:
- **Interactive Command Center**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **FastAPI Interactive API Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. Standalone Frontend Preview
Double-click `frontend/index.html` to open directly in any browser. The built-in client engine automatically provides full simulation and routing capabilities even without the backend.

When served by FastAPI, map tiles are requested through the `/tiles/{z}/{x}/{y}.png`
backend proxy. The configured `CARTO_API_KEY` is used only on the server and is never
returned by an API endpoint or embedded in browser JavaScript/network URLs.

### 3. Run the Automated Test Suite
```bash
python tests/test_api.py
```

To run the application without activating the environment, use:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 🔌 API Reference

| Endpoint | Method | Parameters | Description |
|---|---|---|---|
| `/health` | `GET` | - | Health status, monitored zones count, and loaded AI models |
| `/zones` | `GET` | - | GeoJSON polygons, zone table, facilities, and road network graph |
| `/simulate` | `POST` | `{"rainfall_mm": float, "river_level_m": float}` | Runs hybrid risk model, impact analysis, and generates prioritized action plan |
| `/route` | `GET` | `from_lat`, `from_lon`, `to_lat`, `to_lon` | Computes safest and shortest A* routes with trade-off metrics |
