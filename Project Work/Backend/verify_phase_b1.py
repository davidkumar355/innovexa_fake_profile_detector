"""
Verification script for Phase B1 — Core Data Access Layer
"""

import os
import sys
import numpy as np

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Add backend directory to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.services.data_store import DataStore

def run_verification():
    print("=" * 60)
    print("RUNNING VERIFICATION FOR PHASE B1 — DATA ACCESS LAYER")
    print("=" * 60)
    
    checks = []
    
    # 1. Initialize DataStore
    try:
        ds = DataStore.get_instance()
        checks.append(("DataStore initialization", "Success", "Success", True))
        checks.append(("DataStore total nodes", "4489 nodes", f"{ds.total_nodes} nodes", ds.total_nodes == 4489))
    except Exception as e:
        checks.append(("DataStore initialization", "Success", str(e), False))
        return False

    # 2. Query known nodes (e.g. Node 0, Node 100, Node 4483)
    sample_nodes = [0, 42, 100, 2449, 4483]
    for nid in sample_nodes:
        meta = ds.get_node(nid)
        passed = (meta is not None and meta["node_id"] == nid)
        checks.append((f"Query node {nid} metadata lookup", f"id={nid}", f"id={meta.get('node_id') if meta else None}", passed))

    # 3. Cross-check neighbor count against degree attribute
    degree_mismatch = 0
    for nid in [10, 50, 100, 500, 1000]:
        meta = ds.get_node(nid)
        neighbors = ds.get_neighbors(nid)
        if len(neighbors) != meta["degree"]:
            degree_mismatch += 1
    checks.append(("Degree matches neighbor count across sample", "0 mismatches", f"{degree_mismatch} mismatches", degree_mismatch == 0))

    # 4. Feature vector cross-check
    features_raw = np.load(os.path.join(ds.artifacts_dir, "features_full.npy"))
    feat_mismatch = 0
    for nid in [0, 150, 2449]:
        store_feat = ds.get_node_features(nid, scaled=False)
        if not np.array_equal(store_feat, features_raw[nid]):
            feat_mismatch += 1
    checks.append(("Features array exact match vs raw .npy", "0 mismatches", f"{feat_mismatch} mismatches", feat_mismatch == 0))

    # 5. Category summary check
    summary_node = ds.get_category_summary(0)
    has_cats = len(summary_node.get("category_counts", {})) > 0
    checks.append(("Profile category summary extraction", "Has categories", f"{len(summary_node.get('category_counts', {}))} categories", has_cats))

    # 6. Subgraph extraction check
    sub = ds.get_subgraph(42, max_neighbors=15)
    sub_ok = (sub is not None and sub["center_node_id"] == 42 and len(sub["nodes"]) > 1 and len(sub["edges"]) > 0)
    checks.append(("Local subgraph extraction (node 42)", "Valid graph structure", f"{len(sub.get('nodes', []))} nodes, {len(sub.get('edges', []))} edges", sub_ok))

    # 7. Node list & filtering check
    test_list = ds.list_nodes(split="test", page=1, page_size=20)
    checks.append(("List nodes test split count", "674 nodes", f"{test_list['total']} nodes", test_list["total"] == 674))
    checks.append(("List nodes pagination page size", "20 items", f"{len(test_list['items'])} items", len(test_list["items"]) == 20))

    # 8. Archetype filtering check
    arch_c_list = ds.list_nodes(archetype="C", page=1, page_size=10)
    c_passed = (arch_c_list["total"] > 0 and all(item["archetype"] == "C" for item in arch_c_list["items"]))
    checks.append(("Archetype C filter precision", "100% Arch C", f"Total {arch_c_list['total']} (all Arch C)", c_passed))

    print("\nVERIFICATION RESULTS TABLE:")
    print(f"{'Check':<44} | {'Expected':<18} | {'Actual':<20} | {'Status'}")
    print("-" * 94)
    all_passed = True
    for name, exp, act, passed in checks:
        status_str = "✅ PASS" if passed else "❌ FAIL"
        if not passed:
            all_passed = False
        print(f"{name:<44} | {exp:<18} | {act:<20} | {status_str}")

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
