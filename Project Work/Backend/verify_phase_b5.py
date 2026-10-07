"""
Verification script for Phase B5 — Detection History Store
"""

import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.services.history_store import HistoryStore
from app.schemas.history import HistoryListResponse

def run_verification():
    print("=" * 60)
    print("RUNNING VERIFICATION FOR PHASE B5 — DETECTION HISTORY STORE")
    print("=" * 60)
    
    checks = []
    
    history = HistoryStore.get_instance()
    
    # 1. SQLite file existence
    db_exists = os.path.exists(history.db_path)
    checks.append(("SQLite database file exists on disk", "Exists", str(db_exists), db_exists))

    # 2. Insert 5 known test predictions
    test_entries = [
        ("browse", 0, "Genuine", 0.05, 0.95, "RandomForest-v1.0", 101, None, "Test entry 1"),
        ("browse", 1, "Fake", 0.88, 0.88, "RandomForest-v1.0", 3807, "A", "Test entry 2"),
        ("simulate", 1, "Fake", 0.76, 0.76, "RandomForest-v1.0", None, None, "Test entry 3"),
        ("browse", 1, "Fake", 0.69, 0.69, "RandomForest-v1.0", 3242, "C", "Test entry 4"),
        ("simulate", 0, "Genuine", 0.18, 0.82, "RandomForest-v1.0", None, None, "Test entry 5"),
    ]
    
    inserted_ids = []
    for mode, pred, label, risk, conf, m_ver, nid, arch, details in test_entries:
        i_id = history.record_prediction(
            mode=mode,
            prediction=pred,
            prediction_label=label,
            risk_score=risk,
            confidence=conf,
            model_version=m_ver,
            node_id=nid,
            archetype=arch,
            details=details
        )
        inserted_ids.append(i_id)

    checks.append(("Inserted 5 test predictions", "5 records", f"{len(inserted_ids)} records", len(inserted_ids) == 5))

    # 3. Retrieve all history
    res_all = history.list_history(page=1, page_size=20)
    try:
        validated_all = HistoryListResponse(**res_all)
        checks.append(("Pydantic validation for history response", "Valid schema", "Valid schema", True))
    except Exception as e:
        checks.append(("Pydantic validation for history response", "Valid schema", str(e), False))
        return False

    checks.append(("Total records in store", ">= 5", f"{res_all['total']} records", res_all["total"] >= 5))

    # 4. Check descending order (newest first)
    items = res_all["items"]
    is_desc = all(items[i]["id"] >= items[i+1]["id"] for i in range(len(items) - 1))
    checks.append(("Records ordered descending by ID (newest first)", "True", str(is_desc), is_desc))

    # 5. Filter by mode == 'simulate'
    res_sim = history.list_history(mode="simulate")
    sim_ok = (res_sim["total"] >= 2 and all(item["mode"] == "simulate" for item in res_sim["items"]))
    checks.append(("Filter by mode='simulate'", "All simulate records", f"Total {res_sim['total']}", sim_ok))

    # 6. Filter by mode == 'browse'
    res_browse = history.list_history(mode="browse")
    browse_ok = (res_browse["total"] >= 3 and all(item["mode"] == "browse" for item in res_browse["items"]))
    checks.append(("Filter by mode='browse'", "All browse records", f"Total {res_browse['total']}", browse_ok))

    # 7. Pagination test
    res_page = history.list_history(page=1, page_size=2)
    pag_ok = (len(res_page["items"]) == 2 and res_page["total_pages"] >= 3)
    checks.append(("Pagination page_size=2", "2 items per page", f"{len(res_page['items'])} items, {res_page['total_pages']} pages", pag_ok))

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
