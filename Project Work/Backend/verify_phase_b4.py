"""
Verification script for Phase B4 — Network Analysis Endpoint
"""

import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.services.data_store import DataStore
from app.schemas.network import ClusterListResponse, SubgraphResponse

def run_verification():
    print("=" * 60)
    print("RUNNING VERIFICATION FOR PHASE B4 — NETWORK ANALYSIS ENDPOINTS")
    print("=" * 60)
    
    checks = []
    
    ds = DataStore.get_instance()
    
    # 1. Clusters listing validation
    clusters_data = {
        "total_clusters": len(ds.clusters),
        "high_risk_clusters": sum(1 for c in ds.clusters if c["risk_level"] == "High"),
        "clusters": ds.clusters
    }
    try:
        validated_clusters = ClusterListResponse(**clusters_data)
        checks.append(("Pydantic validation for clusters list", "Valid schema", "Valid schema", True))
    except Exception as e:
        checks.append(("Pydantic validation for clusters list", "Valid schema", str(e), False))
        return False

    checks.append(("Total detected community clusters", "16 clusters", f"{len(ds.clusters)} clusters", len(ds.clusters) == 16))
    
    # 2. Ranking check: Top cluster has maximum fake ratio
    top_cluster = ds.clusters[0]
    checks.append(("Top cluster fake ratio", "> 0.30", f"{top_cluster['fake_ratio']:.4f}", top_cluster["fake_ratio"] > 0.30))
    checks.append(("Top cluster risk level", "High", f"{top_cluster['risk_level']}", top_cluster["risk_level"] == "High"))

    # 3. High risk cluster overlaps with Sybil / Archetype D or fakes
    has_archetypes = any("D" in c["archetype_distribution"] or "C" in c["archetype_distribution"] for c in ds.clusters if c["risk_level"] == "High")
    checks.append(("High-risk clusters capture fakes/archetypes", "Contains fakes", "Confirmed", has_archetypes))

    # 4. Cluster subgraph extraction
    c_sub = ds.get_cluster_subgraph(top_cluster["cluster_id"], max_nodes=40)
    try:
        validated_c_sub = SubgraphResponse(**c_sub)
        c_sub_valid = (
            len(c_sub["nodes"]) > 0
            and len(c_sub["edges"]) > 0
            and all(n["community_id"] == top_cluster["cluster_id"] for n in c_sub["nodes"])
        )
        checks.append(("Cluster subgraph extraction", "Valid subgraph with edges", f"{len(c_sub['nodes'])} nodes, {len(c_sub['edges'])} edges", c_sub_valid))
    except Exception as e:
        checks.append(("Cluster subgraph extraction", "Valid subgraph", str(e), False))

    # 5. Node neighborhood subgraph extraction
    target_node = 42
    n_sub = ds.get_subgraph(target_node, max_neighbors=20)
    try:
        validated_n_sub = SubgraphResponse(**n_sub)
        target_nodes = [n for n in n_sub["nodes"] if n["id"] == target_node]
        n_sub_valid = (len(target_nodes) == 1 and target_nodes[0]["is_target"] is True)
        checks.append((f"Node {target_node} local neighborhood subgraph", "Target centered with edges", f"{len(n_sub['nodes'])} nodes, {len(n_sub['edges'])} edges", n_sub_valid))
    except Exception as e:
        checks.append(("Node local neighborhood subgraph", "Valid subgraph", str(e), False))

    # 6. Error handling for non-existent cluster
    bad_cluster_sub = ds.get_cluster_subgraph(99999)
    checks.append(("Non-existent cluster returns None", "None", str(bad_cluster_sub), bad_cluster_sub is None))

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
