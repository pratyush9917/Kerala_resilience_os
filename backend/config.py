"""
Configuration and Parameters for Kerala Resilience OS
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "processed")
MODELS_DIR = os.path.join(BASE_DIR, "models")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# File paths
ZONES_FEATURES_CSV = os.path.join(DATA_DIR, "zones_features.csv")
ZONES_GEOJSON = os.path.join(DATA_DIR, "zones.geojson")
HOSPITALS_CSV = os.path.join(DATA_DIR, "hospitals.csv")
SCHOOLS_CSV = os.path.join(DATA_DIR, "schools.csv")
ROAD_GRAPH_GRAPHML = os.path.join(DATA_DIR, "road_graph.graphml")
ROAD_GRAPH_JSON = os.path.join(DATA_DIR, "road_graph.json")
AFFECTED_PLACES_JSON = os.path.join(DATA_DIR, "affected_places.json")

RAIN_MODEL_PATH = os.path.join(MODELS_DIR, "rain_hazard.joblib")
RISK_MODEL_PATH = os.path.join(MODELS_DIR, "risk_gbr.joblib")
ACTION_MODEL_PATH = os.path.join(MODELS_DIR, "action_rf.joblib")

# Formula Weights (Section 8 Stage B)
WEIGHTS = {
    "rain": 0.28,
    "river": 0.20,
    "hist": 0.20,
    "elev": 0.14,
    "terrain": 0.08,
    "road": 0.05,
    "prox": 0.05
}

# Elevation bounds in Ernakulam
ELEV_MIN = 2.0   # Coastal Fort Kochi / North Paravur
ELEV_MAX = 55.0  # Kothamangalam foothills

# Classification thresholds
RISK_THRESHOLDS = {
    "critical": 0.75,
    "high": 0.55,
    "medium": 0.35
}

# Routing risk multiplier penalty
ROUTING_PENALTY_K = 4.0
