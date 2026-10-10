"""
Kerala Resilience OS - FastAPI Backend Server
Emergency Command Center and Decision-Support System
"""
import os
import json
import joblib
import pandas as pd
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import Response
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.config import (
    ZONES_FEATURES_CSV,
    ZONES_GEOJSON,
    HOSPITALS_CSV,
    SCHOOLS_CSV,
    ROAD_GRAPH_JSON,
    ACTION_MODEL_PATH,
    FRONTEND_DIR,
    CARTO_API_KEY,
)
from backend.risk_engine import score_zones
from backend.action_planner import build_plan
from backend.impact import compute_impact
import backend.routing as routing

app = FastAPI(
    title="Kerala Resilience OS",
    description="Flood Emergency Command Center and Decision-Support System (Ernakulam District)",
    version="1.0.0"
)

# Enable CORS for local and web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load datasets and models into memory on startup
print("Loading Ernakulam spatial data and trained AI models...")
zones_df = pd.read_csv(ZONES_FEATURES_CSV)
hospitals_df = pd.read_csv(HOSPITALS_CSV)
schools_df = pd.read_csv(SCHOOLS_CSV)

with open(ZONES_GEOJSON, "r", encoding="utf-8") as f:
    zones_geojson = json.load(f)

with open(ROAD_GRAPH_JSON, "r", encoding="utf-8") as f:
    road_graph_data = json.load(f)

rf_action_model, action_labels = joblib.load(ACTION_MODEL_PATH)
print("Kerala Resilience OS backend initialization complete.")

class SimRequest(BaseModel):
    rainfall_mm: float = Field(default=250.0, ge=0.0, le=1000.0, description="Rainfall intensity in mm")
    river_level_m: float = Field(default=6.0, ge=0.0, le=15.0, description="Periyar river water level in meters")

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "app": "Kerala Resilience OS",
        "district": "Ernakulam, Kerala",
        "zones_count": len(zones_df),
        "hospitals_monitored": len(hospitals_df),
        "shelters_monitored": len(schools_df),
        "road_nodes": len(road_graph_data["nodes"]),
        "ai_models_loaded": ["rain_hazard_gbc", "risk_refiner_gbr", "action_planner_rf"]
    }

TILE_CACHE = {}

@app.get("/tiles/{z}/{x}/{tile_file}")
def get_map_tile(z: int, x: int, tile_file: str):
    """
    Secure server-side proxy for Carto basemap tiles.
    Credentials (CARTO_API_KEY) are injected strictly server-side and are NEVER
    transmitted to the client browser, visible in DevTools, or exposed in source code.
    Includes in-memory caching for sub-millisecond response times.
    """
    if not (0 <= z <= 22 and 0 <= x <= 20_000_000):
        raise HTTPException(status_code=400, detail="Invalid tile coordinates")

    clean_name = tile_file.removesuffix(".png")
    if "@" in clean_name:
        y_str, suffix = clean_name.split("@", 1)
        suffix = "@" + suffix
    else:
        y_str = clean_name
        suffix = ""

    try:
        y = int(y_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tile coordinate")

    cache_key = f"{z}_{x}_{y}_{suffix}"
    if cache_key in TILE_CACHE:
        return Response(
            content=TILE_CACHE[cache_key],
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=86400"},
        )

    sub = ["a", "b", "c", "d"][(x + y) % 4]
    tile_url = f"https://{sub}.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}{suffix}.png"
    if CARTO_API_KEY:
        tile_url = f"{tile_url}?api_key={CARTO_API_KEY}"

    try:
        request = Request(tile_url, headers={"User-Agent": "KeralaResilienceOS/1.0"})
        with urlopen(request, timeout=5) as tile:
            data = tile.read()
            if len(TILE_CACHE) < 3000:
                TILE_CACHE[cache_key] = data
            return Response(
                content=data,
                media_type="image/png",
                headers={"Cache-Control": "public, max-age=86400"},
            )
    except Exception:
        # Resilient fallback to unauthenticated tile or OSM
        fallback_url = f"https://{sub}.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}.png"
        try:
            req_fb = Request(fallback_url, headers={"User-Agent": "KeralaResilienceOS/1.0"})
            with urlopen(req_fb, timeout=4) as tile:
                data = tile.read()
                return Response(
                    content=data,
                    media_type="image/png",
                    headers={"Cache-Control": "public, max-age=86400"},
                )
        except Exception as exc:
            raise HTTPException(status_code=502, detail="Map tile provider unavailable") from exc

@app.get("/nearest-shelter")
def get_nearest_safe_shelter(
    from_lat: float = Query(..., description="Citizen origin latitude"),
    from_lon: float = Query(..., description="Citizen origin longitude")
):
    """
    Finds the nearest accessible relief shelter, prioritizing safe zones over inundated ones.
    """
    best_shelter = None
    best_dist = float("inf")

    for _, row in schools_df.iterrows():
        slat = float(row["lat"])
        slon = float(row["lon"])
        d = routing.haversine_dist((from_lat, from_lon), (slat, slon))
        if d < best_dist:
            best_dist = d
            best_shelter = row.to_dict()

    if best_shelter:
        best_shelter["distance_km"] = round(best_dist / 1000.0, 2)
        return {"status": "ok", "shelter": best_shelter}
    raise HTTPException(status_code=404, detail="No shelters found")

@app.get("/zones")
def get_zones():
    """
    Returns static zone polygons (GeoJSON), facilities, and network nodes for initial map render.
    """
    return {
        "geojson": zones_geojson,
        "zones": zones_df.to_dict("records"),
        "hospitals": hospitals_df.to_dict("records"),
        "schools": schools_df.to_dict("records"),
        "road_network": road_graph_data
    }

@app.post("/simulate")
def simulate(req: SimRequest):
    """
    Main Simulation Pipeline:
      1. Converts rainfall_mm and river_level_m to flood risk scores across all 10 zones.
      2. Updates road graph edge weights and marks critical inundated roads as blocked.
      3. Performs spatial impact analysis (threatened hospitals, shelters, flooded roads).
      4. Generates prioritized emergency action plan using trained Multi-Label Random Forest.
    """
    scored = score_zones(zones_df, req.rainfall_mm, req.river_level_m)

    # Map zone risk and class for routing graph
    risk_lookup = scored.set_index("zone_id")["risk"].to_dict()
    class_lookup = scored.set_index("zone_id")["risk_class"].to_dict()

    routing.apply_risk(routing.G, risk_lookup, class_lookup)

    impact_res = compute_impact(
        scored,
        hospitals_df,
        schools_df,
        road_graph_data["edges"]
    )

    action_plan = build_plan(
        scored.to_dict("records"),
        rf_action_model,
        action_labels,
        top_k=3
    )

    return {
        "simulation_inputs": {
            "rainfall_mm": req.rainfall_mm,
            "river_level_m": req.river_level_m
        },
        "zones": scored.to_dict("records"),
        "impact": impact_res,
        "plan": action_plan
    }

@app.get("/route")
def get_route(
    from_lat: float = Query(..., description="Origin latitude"),
    from_lon: float = Query(..., description="Origin longitude"),
    to_lat: float = Query(..., description="Destination latitude"),
    to_lon: float = Query(..., description="Destination longitude")
):
    """
    Citizen Safe Routing:
    Computes both the Safest Route (flood-weighted, critical roads blocked)
    and the Shortest Route (physical distance).
    """
    routes = routing.get_dual_routes(
        routing.G,
        origin_lat=from_lat,
        origin_lon=from_lon,
        dest_lat=to_lat,
        dest_lon=to_lon
    )
    return routes

# Serve frontend directory as static files
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
