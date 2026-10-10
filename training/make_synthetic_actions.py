"""
Generate Synthetic Training Data for Action Planner (Module 3)
Generates:
  - data/processed/action_X.csv
  - data/processed/action_Y.csv
"""
import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "processed")

def make_synthetic_actions():
    print("Generating 15,000 synthetic multi-label emergency action scenarios...")
    rng = np.random.default_rng(7)
    N = 15000

    d = pd.DataFrame({
        "risk": rng.random(N),          # final risk score 0-1
        "rain": rng.random(N),          # normalized rain hazard 0-1
        "river": rng.random(N),         # normalized river level 0-1
        "elev": rng.random(N),          # normalized elevation 0-1 (low is risky)
        "road_vuln": rng.random(N),     # road vulnerability 0-1
        "n_hosp": rng.integers(0, 15, N),
        "n_school": rng.integers(0, 30, N)
    })

    # Domain rule triggers from Kerala SDMA SOPs (Section 9 Page 10)
    A = pd.DataFrame({
        "Evacuation": ((d["risk"] > 0.70) & (d["elev"] < 0.50)) | (d["river"] > 0.88),
        "Open shelters": (d["risk"] > 0.58) | ((d["risk"] > 0.45) & (d["n_school"] > 8)),
        "Deploy pumps": (d["elev"] < 0.35) & (d["rain"] > 0.50) & (d["risk"] > 0.38),
        "Close roads": (d["road_vuln"] > 0.50) & (d["risk"] > 0.55),
        "Alert hospitals": (d["n_hosp"] > 0) & (d["risk"] > 0.42),
        "Public alert": d["risk"] > 0.32
    }).astype(int)

    # Add 5% realistic label noise so model generalizes patterns rather than hardcoded step thresholds
    flip = rng.random(A.shape) < 0.05
    A = A.mask(flip, 1 - A)

    x_path = os.path.join(DATA_DIR, "action_X.csv")
    y_path = os.path.join(DATA_DIR, "action_Y.csv")
    d.to_csv(x_path, index=False)
    A.to_csv(y_path, index=False)
    print(f"Saved: {x_path} and {y_path} ({N} scenarios)")

if __name__ == "__main__":
    make_synthetic_actions()
