"""
Train Stage C: Hybrid Flood Risk Engine (Gradient Boosting Regressor)
Learns non-linear interactions (e.g. low elevation + high river + heavy rain synergy)
Outputs: models/risk_gbr.joblib
"""
import os
import sys
import joblib
import pandas as pd
import numpy as np

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.ml_models import ResilientGradientBoostingRegressor

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_ZONES = os.path.join(BASE_DIR, "data", "processed", "zones_features.csv")
MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

# Documented formula weights from Section 8 Stage B
WEIGHTS = {
    "rain": 0.28,
    "river": 0.20,
    "hist": 0.20,
    "elev": 0.14,
    "terrain": 0.08,
    "road": 0.05,
    "prox": 0.05
}

def rule_score(rain_hazard, river_norm, z):
    elev_risk = 1.0 - float(z["elev_norm"]) # low elevation = higher flood risk
    score = (
        WEIGHTS["rain"] * rain_hazard
        + WEIGHTS["river"] * river_norm * float(z["river_prox"])
        + WEIGHTS["hist"] * float(z["hist_risk"])
        + WEIGHTS["elev"] * elev_risk
        + WEIGHTS["terrain"] * float(z["terrain"])
        + WEIGHTS["road"] * float(z["road_vuln"])
        + WEIGHTS["prox"] * float(z["river_prox"])
    )
    return score

def train_risk_refiner():
    print("Loading zone feature table...")
    zones = pd.read_csv(PROCESSED_ZONES)
    rng = np.random.default_rng(42)

    rows = []
    print("Simulating 3,000 hydrological disaster scenarios...")
    for _ in range(3000):
        rain_h = rng.random()      # 0 to 1 normalized rain hazard
        river = rng.random()       # 0 to 1 normalized river level
        for _, z in zones.iterrows():
            base = rule_score(rain_h, river, z)
            # Non-linear interaction: low elevation + river overflow + torrential rain
            interaction = 0.12 * rain_h * river * (1.0 - float(z["elev_norm"]))
            target = np.clip(base + interaction + rng.normal(0, 0.015), 0.0, 1.0)
            rows.append([
                rain_h,
                river,
                float(z["hist_risk"]),
                float(z["elev_norm"]),
                float(z["terrain"]),
                float(z["road_vuln"]),
                float(z["river_prox"]),
                target
            ])

    cols = ["rain_h", "river", "hist", "elev", "terrain", "road", "prox", "target"]
    df = pd.DataFrame(rows, columns=cols)

    # Train / test split (80/20)
    split_idx = int(len(df) * 0.8)
    shuffled = df.sample(frac=1.0, random_state=42)
    train_df = shuffled.iloc[:split_idx]
    test_df = shuffled.iloc[split_idx:]

    Xtr, ytr = train_df[cols[:-1]].values, train_df["target"].values
    Xte, yte = test_df[cols[:-1]].values, test_df["target"].values

    print(f"Training Resilient Gradient Boosting Regressor on {len(Xtr)} samples...")
    gbr = ResilientGradientBoostingRegressor(
        n_estimators=80,
        learning_rate=0.08,
        max_depth=3,
        random_state=42
    )
    gbr.fit(Xtr, ytr)

    preds = gbr.predict(Xte)
    mae = float(np.mean(np.abs(yte - preds)))
    ss_tot = np.sum((yte - np.mean(yte)) ** 2)
    ss_res = np.sum((yte - preds) ** 2)
    r2 = 1.0 - (ss_res / ss_tot)

    print(f"Evaluation: MAE = {mae:.4f}, R2 Score = {r2:.4f}")
    print("Feature Importances:")
    feat_names = cols[:-1]
    for name, imp in zip(feat_names, gbr.feature_importances_):
        print(f"  - {name:8s}: {imp:.3f}")

    # Save model and weights
    out_payload = {
        "model": gbr,
        "feature_names": feat_names,
        "weights": WEIGHTS,
        "mae": round(mae, 4),
        "r2": round(r2, 4)
    }
    out_path = os.path.join(MODEL_DIR, "risk_gbr.joblib")
    joblib.dump(out_payload, out_path)
    print(f"Model saved to: {out_path}")

if __name__ == "__main__":
    train_risk_refiner()
