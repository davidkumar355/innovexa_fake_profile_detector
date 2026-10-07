"""
Verification script for Phase B2 — Prediction Endpoints
"""

import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.services.predictor import PredictorService
from app.services.history_store import HistoryStore
from app.services.data_store import DataStore

def run_verification():
    print("=" * 60)
    print("RUNNING VERIFICATION FOR PHASE B2 — PREDICTION ENDPOINTS")
    print("=" * 60)
    
    checks = []
    
    predictor = PredictorService.get_instance()
    ds = DataStore.get_instance()
    history = HistoryStore.get_instance()
    
    # 1. Option A: Browse prediction on known genuine node
    gen_nodes = [nid for nid in ds.splits["test_idx"] if ds.labels[nid] == 0]
    sample_gen_id = gen_nodes[0]
    res_gen = predictor.predict_browse(sample_gen_id)
    
    gen_ok = (
        res_gen is not None
        and res_gen["node_id"] == sample_gen_id
        and res_gen["true_label"] == 0
        and "risk_score" in res_gen
        and "confidence" in res_gen
        and res_gen["prediction_label"] in ["Genuine", "Fake"]
    )
    checks.append((f"Browse prediction on genuine test node #{sample_gen_id}", "Valid prediction", f"Pred={res_gen['prediction_label']}, Risk={res_gen['risk_score']}", gen_ok))

    # 2. Option A: Browse prediction across all 4 fake archetypes (A, B, C, D)
    for arch in ["A", "B", "C", "D"]:
        arch_candidates = [
            nid for nid in ds.splits["test_idx"]
            if ds.labels[nid] == 1 and ds.node_metadata[str(nid)].get("archetype") == arch
        ]
        if arch_candidates:
            target_id = arch_candidates[0]
            res_arch = predictor.predict_browse(target_id)
            arch_ok = (res_arch is not None and res_arch["archetype"] == arch)
            checks.append((f"Browse fake archetype {arch} node #{target_id}", f"Arch {arch} loaded", f"Arch={res_arch.get('archetype')}, Risk={res_arch.get('risk_score')}", arch_ok))

    # 3. Option B: Simulate inductive profile — Genuine profile test
    # Give it multiple features and 15 connections to genuine nodes
    sample_connections = gen_nodes[1:16]
    sample_feats = [10, 25, 100, 200, 350, 500, 750, 1000] # normal profile attributes
    res_sim_normal = predictor.simulate_profile(
        active_feature_indices=sample_feats,
        connection_node_ids=sample_connections
    )
    normal_ok = (
        res_sim_normal is not None
        and "risk_score" in res_sim_normal
        and "structural_features" in res_sim_normal
        and res_sim_normal["structural_features"]["degree"] == len(sample_connections)
        and res_sim_normal["risk_score"] < 0.60
    )
    checks.append(("Simulate realistic profile (low risk behavior)", "Risk < 0.60", f"Risk={res_sim_normal.get('risk_score')}, Tier={res_sim_normal.get('risk_tier')}", normal_ok))

    # 4. Option B: Simulate sparse profile
    res_sim_sparse = predictor.simulate_profile(
        active_feature_indices=[],
        connection_node_ids=[gen_nodes[2]]
    )
    sparse_ok = (
        res_sim_sparse is not None
        and res_sim_sparse["structural_features"]["degree"] == 1
    )
    checks.append(("Simulate sparse empty profile", "Degree=1 derived", f"Degree={res_sim_sparse['structural_features']['degree']}, Risk={res_sim_sparse['risk_score']}", sparse_ok))

    # 5. Out of bounds check
    res_invalid = predictor.predict_browse(999999)
    checks.append(("Browse invalid node ID returns None", "None", str(res_invalid), res_invalid is None))

    # 6. History persistence check
    initial_count = history.list_history()["total"]
    history.record_prediction(
        mode="test_run",
        prediction=0,
        prediction_label="Genuine",
        risk_score=0.12,
        confidence=0.88,
        model_version="RandomForest-v1.0",
        node_id=123,
        details="Verification record"
    )
    new_count = history.list_history()["total"]
    checks.append(("Prediction logged to SQLite history store", f">= {initial_count + 1}", f"{new_count} records", new_count > initial_count))

    print("\nVERIFICATION RESULTS TABLE:")
    print(f"{'Check':<46} | {'Expected':<18} | {'Actual':<22} | {'Status'}")
    print("-" * 98)
    all_passed = True
    for name, exp, act, passed in checks:
        status_str = "✅ PASS" if passed else "❌ FAIL"
        if not passed:
            all_passed = False
        print(f"{name:<46} | {exp:<18} | {act:<22} | {status_str}")

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
