"""
Train Module 3: Action Planner (Random Forest Multi-Label Classifier)
Outputs: models/action_rf.joblib
"""
import os
import sys
import joblib
import pandas as pd
import numpy as np

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.ml_models import ResilientRandomForestMultiLabel

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "processed")
MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

def train_action_planner():
    print("Loading synthetic action datasets...")
    X_df = pd.read_csv(os.path.join(DATA_DIR, "action_X.csv"))
    Y_df = pd.read_csv(os.path.join(DATA_DIR, "action_Y.csv"))

    labels = list(Y_df.columns)
    print(f"Target emergency actions ({len(labels)}): {labels}")

    # 80/20 train/test split
    n = len(X_df)
    indices = np.arange(n)
    np.random.seed(42)
    np.random.shuffle(indices)

    split = int(n * 0.8)
    tr_idx, te_idx = indices[:split], indices[split:]

    Xtr, Ytr = X_df.iloc[tr_idx].values, Y_df.iloc[tr_idx].values
    Xte, Yte = X_df.iloc[te_idx].values, Y_df.iloc[te_idx].values

    print(f"Training Multi-Label Random Forest on {len(Xtr)} samples...")
    rf = ResilientRandomForestMultiLabel(n_estimators=45, max_features=4, random_state=42)
    rf.fit(Xtr, Ytr, labels=labels)

    # Evaluate on test set
    preds = rf.predict(Xte)

    # Hamming loss: fraction of wrong labels
    hamming_loss = float(np.mean(preds != Yte))
    print(f"Hamming Loss on hold-out set: {hamming_loss:.4f} (accuracy per label ~ {(1-hamming_loss)*100:.1f}%)")

    # Per-label metrics
    for j, lab in enumerate(labels):
        true_pos = np.sum((preds[:, j] == 1) & (Yte[:, j] == 1))
        pred_pos = np.sum(preds[:, j] == 1)
        act_pos = np.sum(Yte[:, j] == 1)
        prec = true_pos / pred_pos if pred_pos > 0 else 0
        rec = true_pos / act_pos if act_pos > 0 else 0
        f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0
        print(f"  - {lab:15s}: Precision={prec:.3f}, Recall={rec:.3f}, F1={f1:.3f}")

    # Save tuple (model, labels) exactly as specified in Section 9 / Section 12
    out_path = os.path.join(MODEL_DIR, "action_rf.joblib")
    joblib.dump((rf, labels), out_path)
    print(f"Model saved to: {out_path}")

if __name__ == "__main__":
    train_action_planner()
