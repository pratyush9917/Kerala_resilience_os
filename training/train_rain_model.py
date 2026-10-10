"""
Train Stage A: Rainfall Hazard Model using 118-year Historical Kerala Rainfall Data
Model: GradientBoostingClassifier (Resilient Engine)
Outputs: models/rain_hazard.joblib
"""
import os
import sys
import joblib
import pandas as pd
import numpy as np

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.ml_models import ResilientGradientBoostingClassifier

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_CSV = os.path.join(BASE_DIR, "data", "raw", "Kerala-Rainfall-Historical.csv")
MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

def train_rainfall_model():
    print("Loading Kerala Historical Rainfall dataset (118 years)...")
    df = pd.read_csv(RAW_CSV)

    documented_flood_years = {1912, 1923, 1924, 1933, 1946, 1959, 1961, 1968, 1974, 1980, 1991, 2007, 2013, 2018}

    if 2018 not in df["YEAR"].values:
        row_2018 = {
            "SUBDIVISION": "Kerala", "YEAR": 2018,
            "JAN": 11.2, "FEB": 6.8, "MAR": 34.0, "APR": 98.5, "MAY": 242.0,
            "JUN": 749.6, "JUL": 798.5, "AUG": 822.4, "SEP": 158.2,
            "OCT": 312.0, "NOV": 110.5, "DEC": 18.0,
            "ANNUAL": 3361.7, "JF": 18.0, "MAM": 374.5, "JJAS": 2528.7, "OND": 440.5
        }
        df = pd.concat([df, pd.DataFrame([row_2018])], ignore_index=True)

    months = ["JUN", "JUL", "AUG", "SEP"]
    df["monsoon"] = df[months].sum(axis=1)
    df["jul_aug"] = df[["JUL", "AUG"]].sum(axis=1)
    df["peak_month"] = df[months].max(axis=1)

    monsoon_threshold = df["monsoon"].quantile(0.85)
    df["y"] = df.apply(
        lambda r: 1 if (r["YEAR"] in documented_flood_years or r["monsoon"] >= monsoon_threshold) else 0,
        axis=1
    )

    X = df[["monsoon", "jul_aug", "peak_month"]].values
    y = df["y"].values

    print(f"Dataset records: {len(df)} years. Flood positive years: {y.sum()}")

    clf = ResilientGradientBoostingClassifier(n_estimators=60, learning_rate=0.08, random_state=42)
    clf.fit(X, y)

    probs = clf.predict_proba(X)[:, 1]
    acc = np.mean((probs >= 0.5).astype(int) == y)
    print(f"Model Training Accuracy: {acc*100:.2f}%")

    # Benchmark against 2018 Great Flood
    x_2018 = np.array([[2528.7, 1620.9, 822.4]])
    prob_2018 = clf.predict_proba(x_2018)[0, 1]
    print(f"Sanity Check: Aug 2018 Hazard Score = {prob_2018:.3f} (Expected high > 0.85)")

    # Benchmark against a dry year (e.g. 1987)
    x_dry = np.array([[1200.0, 700.0, 400.0]])
    prob_dry = clf.predict_proba(x_dry)[0, 1]
    print(f"Sanity Check: Low Rainfall Hazard Score = {prob_dry:.3f} (Expected low < 0.20)")

    model_payload = {
        "model": clf,
        "features": ["monsoon", "jul_aug", "peak_month"],
        "max_monsoon": float(df["monsoon"].max()),
        "max_peak": float(df["peak_month"].max())
    }

    out_path = os.path.join(MODEL_DIR, "rain_hazard.joblib")
    joblib.dump(model_payload, out_path)
    print(f"Model saved to: {out_path}")

if __name__ == "__main__":
    train_rainfall_model()
