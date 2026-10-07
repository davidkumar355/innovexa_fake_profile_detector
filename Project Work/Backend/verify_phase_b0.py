"""
Verification script for Phase B0 — Project Setup & Model Artifact Export
"""

import json
import os
import sys
import numpy as np
import joblib

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACTS_DIR = os.path.join(BASE_DIR, "artifacts")

def run_verification():
    print("=" * 60)
    print("RUNNING VERIFICATION FOR PHASE B0 — ARTIFACT EXPORT & SETUP")
    print("=" * 60)
    
    checks = []
    
    expected_files = [
        ("random_forest.joblib", 500_000),
        ("logistic_regression.joblib", 5_000),
        ("scaler.joblib", 500),
        ("features_full.npy", 1_000_000),
        ("features_scaled.npy", 1_000_000),
        ("labels.npy", 4_000),
        ("thresholds.json", 30),
        ("model_metrics.json", 100),
        ("splits.json", 1_000),
        ("node_metadata.json", 500_000),
        ("community_clusters.json", 10_000),
        ("dashboard_summary.json", 200),
        ("feature_categories.json", 10_000),
        ("graph_adjacency.json", 50_000),
    ]
    
    for filename, min_bytes in expected_files:
        path = os.path.join(ARTIFACTS_DIR, filename)
        if not os.path.exists(path):
            checks.append((f"Artifact {filename} exists", "Exists", "Missing", False))
        else:
            sz = os.path.getsize(path)
            passed = sz >= min_bytes
            checks.append((f"Artifact {filename} size", f">= {min_bytes} B", f"{sz} B", passed))

    # Test clean loading of models
    try:
        rf = joblib.load(os.path.join(ARTIFACTS_DIR, "random_forest.joblib"))
        scaler = joblib.load(os.path.join(ARTIFACTS_DIR, "scaler.joblib"))
        checks.append(("Model and scaler load cleanly via joblib", "Success", "Success", True))
    except Exception as e:
        checks.append(("Model and scaler load cleanly via joblib", "Success", str(e), False))
        rf, scaler = None, None

    # Test data integrity
    try:
        X_full = np.load(os.path.join(ARTIFACTS_DIR, "features_full.npy"))
        X_scaled = np.load(os.path.join(ARTIFACTS_DIR, "features_scaled.npy"))
        y = np.load(os.path.join(ARTIFACTS_DIR, "labels.npy"))
        checks.append(("Feature matrix shape", "(4489, 1411)", str(X_full.shape), X_full.shape == (4489, 1411)))
        checks.append(("No NaN values in features", "0 NaNs", f"{np.isnan(X_scaled).sum()} NaNs", not np.isnan(X_scaled).any()))
    except Exception as e:
        checks.append(("Data files loadable", "Success", str(e), False))

    # Test prediction consistency
    if rf is not None:
        try:
            with open(os.path.join(ARTIFACTS_DIR, "splits.json"), "r") as f:
                splits = json.load(f)
            with open(os.path.join(ARTIFACTS_DIR, "thresholds.json"), "r") as f:
                thresh = json.load(f)["random_forest"]
            with open(os.path.join(ARTIFACTS_DIR, "model_metrics.json"), "r") as f:
                metrics = json.load(f)["random_forest"]

            test_idx = splits["test_idx"]
            X_te = X_scaled[test_idx]
            y_te = y[test_idx]

            probas = rf.predict_proba(X_te)[:, 1]
            preds = (probas >= thresh).astype(int)
            
            from sklearn.metrics import f1_score
            computed_f1 = float(f1_score(y_te, preds))
            expected_f1 = metrics["f1"]

            diff = abs(computed_f1 - expected_f1)
            checks.append(("Inference F1 score consistency", f"{expected_f1:.4f}", f"{computed_f1:.4f}", diff < 1e-4))
        except Exception as e:
            checks.append(("Inference test execution", "Success", str(e), False))

    # Test metadata and cluster structure
    try:
        with open(os.path.join(ARTIFACTS_DIR, "node_metadata.json"), "r") as f:
            meta = json.load(f)
        checks.append(("Node metadata entries count", "4489 entries", f"{len(meta)} entries", len(meta) == 4489))
        
        with open(os.path.join(ARTIFACTS_DIR, "community_clusters.json"), "r") as f:
            clusters = json.load(f)
        checks.append(("Community clusters non-empty", "> 0 clusters", f"{len(clusters)} clusters", len(clusters) > 0))
    except Exception as e:
        checks.append(("JSON metadata validation", "Success", str(e), False))

    print("\nVERIFICATION RESULTS TABLE:")
    print(f"{'Check':<42} | {'Expected':<18} | {'Actual':<20} | {'Status'}")
    print("-" * 92)
    all_passed = True
    for name, exp, act, passed in checks:
        status_str = "✅ PASS" if passed else "❌ FAIL"
        if not passed:
            all_passed = False
        print(f"{name:<42} | {exp:<18} | {act:<20} | {status_str}")

    print("=" * 60)
    if all_passed:
        print("OVERALL STATUS: ✅ ALL CHECKS PASSED")
    else:
        print("OVERALL STATUS: ❌ SOME CHECKS FAILED")
    print("=" * 60)
    return all_passed

if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
