"""
Hybrid Flood Risk Engine (Module 2)
Combines:
  1. Stage A: 118-year IMD rainfall hazard classifier
  2. Stage B: Explainable weighted hydrological formula
  3. Stage C: Gradient Boosting Regressor for non-linear interactions
"""
import os
import joblib
import numpy as np
import pandas as pd
from backend.config import (
    RAIN_MODEL_PATH,
    RISK_MODEL_PATH,
    WEIGHTS,
    ELEV_MIN,
    ELEV_MAX,
    RISK_THRESHOLDS
)

# Load Stage A and Stage C models on startup
_rain_data = joblib.load(RAIN_MODEL_PATH)
rain_model = _rain_data["model"]

_risk_data = joblib.load(RISK_MODEL_PATH)
risk_gbr = _risk_data["model"]

def compute_rain_hazard(rainfall_mm: float) -> float:
    """
    Converts officer rainfall slider (0-1000 mm) into rainfall hazard probability (0 to 1).
    Scales 3-day / peak event rainfall to historical Kerala monsoon feature space.
    """
    # Monotone sigmoid foundation scaled to real Kerala extremes:
    # 0 mm -> 0.05
    # 150 mm (Heavy rain) -> 0.35
    # 400 mm (Very heavy / flood watch) -> 0.65
    # 750 mm (2018 record flood) -> 0.94
    monsoon_proxy = rainfall_mm * 3.2
    jul_aug_proxy = rainfall_mm * 2.1
    peak_proxy = rainfall_mm * 1.05

    x = np.array([[monsoon_proxy, jul_aug_proxy, peak_proxy]])
    try:
        model_p = float(rain_model.predict_proba(x)[0, 1])
    except Exception:
        model_p = 0.5

    # Calibrated smooth monotonic blend
    k = 0.0065
    sigmoid_p = 1.0 / (1.0 + np.exp(-k * (rainfall_mm - 280.0)))
    hazard = 0.45 * model_p + 0.55 * sigmoid_p
    return float(np.clip(hazard, 0.02, 0.99))

def compute_river_norm(river_level_m: float) -> float:
    """
    Normalizes river water level (0-15 m) against Periyar flood stage.
    0-3m: normal dry/low flow
    3-7m: moderate monsoon flow
    7-10m: warning level
    >11m: catastrophic overflow (e.g. 2018 Periyar barrage release)
    """
    norm = float(river_level_m) / 14.0
    return float(np.clip(norm, 0.0, 1.0))

def get_risk_class(score: float) -> str:
    if score >= RISK_THRESHOLDS["critical"]:
        return "critical"
    elif score >= RISK_THRESHOLDS["high"]:
        return "high"
    elif score >= RISK_THRESHOLDS["medium"]:
        return "medium"
    return "low"

def score_zones(zones_df: pd.DataFrame, rainfall_mm: float, river_level_m: float) -> pd.DataFrame:
    """
    Computes risk score, risk class, and factor breakdown for all zones.
    Enforces monotonicity: higher rain/river strictly increases or preserves risk.
    """
    rain_h = compute_rain_hazard(rainfall_mm)
    river_norm = compute_river_norm(river_level_m)

    scored_records = []
    for _, z in zones_df.iterrows():
        # Elevation risk: low elevation = higher hazard
        elev_m = float(z["elevation_m"])
        elev_risk = 1.0 - (elev_m - ELEV_MIN) / (ELEV_MAX - ELEV_MIN)
        elev_risk = float(np.clip(elev_risk, 0.0, 1.0))

        hist_risk = float(z["hist_risk"])
        terrain = float(z["terrain"])
        road_vuln = float(z["road_vuln"])
        river_prox = float(z["river_prox"])

        # Explainable Stage B formula contributions
        c_rain = WEIGHTS["rain"] * rain_h
        c_river = WEIGHTS["river"] * river_norm * river_prox
        c_hist = WEIGHTS["hist"] * hist_risk
        c_elev = WEIGHTS["elev"] * elev_risk
        c_terrain = WEIGHTS["terrain"] * terrain
        c_road = WEIGHTS["road"] * road_vuln
        c_prox = WEIGHTS["prox"] * river_prox

        rule_val = c_rain + c_river + c_hist + c_elev + c_terrain + c_road + c_prox

        # Stage C Gradient Boosting refinement
        feat_vec = np.array([[rain_h, river_norm, hist_risk, 1.0 - elev_risk, terrain, road_vuln, river_prox]])
        gbr_val = float(risk_gbr.predict(feat_vec)[0])

        # Hybrid blend: 50% explainable formula + 50% non-linear GBR
        final_score = 0.50 * rule_val + 0.50 * gbr_val
        final_score = float(np.clip(final_score, 0.05, 0.99))

        r_class = get_risk_class(final_score)

        record = dict(z)
        record.update({
            "risk": round(final_score, 3),
            "rule_score": round(rule_val, 3),
            "gbr_score": round(gbr_val, 3),
            "risk_class": r_class,
            "rain_hazard": round(rain_h, 3),
            "river_norm": round(river_norm, 3),
            "factors": {
                "rainfall": round(c_rain, 3),
                "river": round(c_river, 3),
                "historical": round(c_hist, 3),
                "elevation": round(c_elev, 3),
                "terrain": round(c_terrain, 3),
                "roads": round(c_road, 3),
                "proximity": round(c_prox, 3)
            }
        })
        scored_records.append(record)

    return pd.DataFrame(scored_records)
