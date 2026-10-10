"""
Action Planner (Module 3)
Uses trained Multi-Label Random Forest to predict emergency actions and rank by Priority = Confidence * Zone Risk.
"""
import os
import json
import numpy as np
from backend.config import AFFECTED_PLACES_JSON

# Load affected places map
with open(AFFECTED_PLACES_JSON, "r", encoding="utf-8") as f:
    AFFECTED_PLACES = json.load(f)

# Action icons and category badges for command center display
ACTION_META = {
    "Evacuation": {"icon": "🚨", "severity": "critical", "type": "Life Safety"},
    "Open shelters": {"icon": "🏫", "severity": "high", "type": "Relief"},
    "Deploy pumps": {"icon": "🚜", "severity": "medium", "type": "Drainage"},
    "Close roads": {"icon": "🚧", "severity": "high", "type": "Traffic Control"},
    "Alert hospitals": {"icon": "🏥", "severity": "critical", "type": "Healthcare"},
    "Public alert": {"icon": "📢", "severity": "medium", "type": "Warning"}
}

def build_plan(zone_rows, rf, labels, top_k=3):
    """
    Predicts probabilities for each action in each zone,
    computes Priority = Confidence * Risk,
    names specific affected places, and ranks the action plan.
    """
    plan = []

    for z in zone_rows:
        zone_id = z.get("zone_id")
        zone_name = z.get("name")
        risk = float(z.get("risk", 0.5))
        rain = float(z.get("rain_hazard", 0.5))
        river = float(z.get("river_norm", 0.5))
        elev = float(z.get("elev_norm", 0.5))
        road_vuln = float(z.get("road_vuln", 0.5))
        n_hosp = int(z.get("n_hospitals", 3))
        n_school = int(z.get("n_schools", 10))

        # Features matching training/action_X.csv:
        # [risk, rain, river, elev, road_vuln, n_hosp, n_school]
        x = np.array([[risk, rain, river, elev, road_vuln, n_hosp, n_school]])

        proba_list = rf.predict_proba(x)
        # proba_list is a list of arrays (one per label) of shape (1, 2)
        probabilities = [float(p[0, 1]) for p in proba_list]

        # Rank actions for this zone
        ranked = sorted(zip(labels, probabilities), key=lambda t: -t[1])[:top_k]

        places_dict = AFFECTED_PLACES.get(zone_id, {})

        for action_name, prob in ranked:
            # Don't trigger hospital alert if zone has no hospitals
            if action_name == "Alert hospitals" and n_hosp == 0:
                continue

            # Only suggest relevant actions
            if prob >= 0.30 or (risk > 0.60 and prob >= 0.20):
                priority_score = round(prob * risk, 3)
                specific_places = places_dict.get(
                    action_name,
                    f"Low-lying wards and riverbanks in {zone_name}"
                )
                meta = ACTION_META.get(action_name, {"icon": "⚡", "severity": "medium", "type": "Operation"})

                plan.append({
                    "zone": zone_name,
                    "zone_id": zone_id,
                    "action": action_name,
                    "confidence": round(prob, 2),
                    "confidence_pct": int(round(prob * 100)),
                    "priority": priority_score,
                    "places": specific_places,
                    "icon": meta["icon"],
                    "severity": meta["severity"],
                    "type": meta["type"]
                })

    # Global sort: Highest priority (likely actions in critical zones) first!
    plan.sort(key=lambda a: -a["priority"])
    return plan
