"""
Train All Models Pipeline for Kerala Resilience OS
Runs the full training workflow end-to-end:
  1. Build Features & Spatial Datasets (Module 1)
  2. Train 118-year Rainfall Hazard Model (Module 2 Stage A)
  3. Train Hybrid Risk Gradient Boosting Regressor (Module 2 Stage C)
  4. Generate Synthetic Action Scenarios (Module 3 Step 1)
  5. Train Multi-Label Action Planner Random Forest (Module 3 Step 2)
"""
import sys
import subprocess

def run_step(step_name, script_path):
    print("=" * 65)
    print(f">> STEP: {step_name}")
    print(f"   Running: {script_path}")
    print("=" * 65)
    result = subprocess.run([sys.executable, script_path])
    if result.returncode != 0:
        print(f"[FAIL] Error during: {step_name}")
        sys.exit(result.returncode)
    print(f"[OK] Completed: {step_name}\n")

if __name__ == "__main__":
    print("\n--- STARTING COMPLETE MODEL TRAINING PIPELINE: KERALA RESILIENCE OS ---\n")
    run_step("1/5: Build Features & Processed Data", "training/build_features.py")
    run_step("2/5: Train Rainfall Hazard Model (118-year data)", "training/train_rain_model.py")
    run_step("3/5: Train Risk Gradient Boosting Regressor", "training/train_risk_model.py")
    run_step("4/5: Generate Synthetic Disaster Scenarios", "training/make_synthetic_actions.py")
    run_step("5/5: Train Multi-Label Action Planner", "training/train_action_model.py")
    print("=" * 65)
    print("SUCCESS: ALL MODELS TRAINED & SAVED TO /models DIRECTORY!")
    print("=" * 65)
