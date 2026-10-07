"""
Verification script for Phase B3 — Dashboard Aggregate Endpoint
"""

import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.services.data_store import DataStore
from app.schemas.dashboard import DashboardSummaryResponse

def run_verification():
    print("=" * 60)
    print("RUNNING VERIFICATION FOR PHASE B3 — DASHBOARD AGGREGATE ENDPOINT")
    print("=" * 60)
    
    checks = []
    
    ds = DataStore.get_instance()
    summary = ds.dashboard_summary
    
    # 1. Pydantic validation
    try:
        validated = DashboardSummaryResponse(**summary)
        checks.append(("Pydantic schema validation", "Valid schema", "Valid schema", True))
    except Exception as e:
        checks.append(("Pydantic schema validation", "Valid schema", str(e), False))
        return False

    # 2. Total test profiles count
    total_test = len(ds.splits["test_idx"])
    checks.append(("Total profiles analyzed", f"{total_test}", f"{summary['total_profiles_analyzed']}", summary["total_profiles_analyzed"] == total_test))

    # 3. Sum of archetypes == true fake count
    arch_dist = summary["archetype_distribution"]
    sum_arch = sum(arch_dist.values())
    expected_fakes = summary["true_fake_count"]
    checks.append(("Sum of archetype breakdown == true fakes", f"{expected_fakes}", f"{sum_arch}", sum_arch == expected_fakes))

    # 4. F1 score matches Phase 6 baseline
    f1 = summary["model_f1_score"]
    checks.append(("Model F1 score consistency", "0.9219", f"{f1:.4f}", abs(f1 - 0.9219) < 1e-3))

    # 5. Detections over time timeline integrity
    timeline = summary["detections_over_time"]
    has_7_days = len(timeline) == 7
    total_timeline_analyzed = sum(d["total_analyzed"] for d in timeline)
    timeline_matches = (total_timeline_analyzed == total_test)
    checks.append(("Timeline 7-day points count", "7 days", f"{len(timeline)} days", has_7_days))
    checks.append(("Timeline total sum matches test count", f"{total_test}", f"{total_timeline_analyzed}", timeline_matches))

    # 6. High risk count positive and non-zero
    hr = summary["high_risk_pending_review"]
    checks.append(("High-risk pending review count sanity", "> 0", f"{hr}", hr > 0))

    print("\nVERIFICATION RESULTS TABLE:")
    print(f"{'Check':<44} | {'Expected':<18} | {'Actual':<22} | {'Status'}")
    print("-" * 94)
    all_passed = True
    for name, exp, act, passed in checks:
        status_str = "✅ PASS" if passed else "❌ FAIL"
        if not passed:
            all_passed = False
        print(f"{name:<44} | {exp:<18} | {act:<22} | {status_str}")

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
