"""
Kerala Resilience OS - FastAPI Backend Server
Emergency Command Center and Decision-Support System
"""
import os
import json
import joblib
import pandas as pd
from fastapi import FastAPI, Query, HTTPException
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
    FRONTEND_DIR
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
