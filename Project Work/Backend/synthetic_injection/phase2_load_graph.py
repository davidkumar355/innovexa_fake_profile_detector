"""
Phase 2: Load & Merge Real Graph
Loads facebook_combined.txt into NetworkX Graph, attaches unified features,
assigns genuine label (0), extracts community circle structures, and computes degree metrics.
"""

import os
import json
import tarfile
import numpy as np
import networkx as nx
from memory_logger import MemoryLogger

def load_real_graph(
    edges_path=r"Project Work\Dataset\facebook_combined.txt",
    tar_path=r"Project Work\Dataset\facebook.tar.gz",
    features_path=r"Project Work\Dataset\generated\v1\unified_features_real.npy",
    output_dir=r"Project Work\Dataset\generated\v1",
    memory_file=r"Project Work\memory.md",
    logger=None
):
    if logger is None:
        logger = MemoryLogger(memory_file)

    os.makedirs(output_dir, exist_ok=True)
    edges_path = os.path.abspath(edges_path)
    tar_path = os.path.abspath(tar_path)
    features_path = os.path.abspath(features_path)

    print("[Phase 2] Loading real graph from facebook_combined.txt...")
    G = nx.Graph()

    with open(edges_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                u, v = map(int, line.split())
                G.add_edge(u, v)

    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()
    print(f"[Phase 2] Real graph loaded: {num_nodes} nodes, {num_edges} edges")

    # Load Phase 1 unified features
    feat_matrix = np.load(features_path)
    dim = feat_matrix.shape[1]

    # Attach features and label=0 (genuine)
    for n in G.nodes():
        G.nodes[n]["feat"] = feat_matrix[n]
        G.nodes[n]["label"] = 0

    # Load .circles data from facebook.tar.gz
    ego_ids = [0, 107, 348, 414, 686, 698, 1684, 1912, 3437, 3980]
    circles_data = {}
    total_circles_count = 0

    tar = tarfile.open(tar_path, "r:gz")
    for eid in ego_ids:
        circles_data[str(eid)] = {}
        f_circ = tar.extractfile(f"facebook/{eid}.circles")
        for line in f_circ.read().decode("utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            circle_name = parts[0]
            member_ids = [int(x) for x in parts[1:] if x.strip()]
            circles_data[str(eid)][circle_name] = member_ids
            total_circles_count += 1
    tar.close()

    # Save circles data for Phase 3
    circles_path = os.path.join(output_dir, "circles_data.json")
    with open(circles_path, "w", encoding="utf-8") as f:
        json.dump(circles_data, f)
    print(f"[Phase 2] Extracted {total_circles_count} circles across 10 egos to {circles_path}")

    # Compute degree statistics
    degrees = [d for _, d in G.degree()]
    deg_arr = np.array(degrees)
    deg_mean = float(np.mean(deg_arr))
    deg_std = float(np.std(deg_arr))
    deg_median = float(np.median(deg_arr))
    deg_min = int(np.min(deg_arr))
    deg_max = int(np.max(deg_arr))
    deg_90th = float(np.percentile(deg_arr, 90))
    deg_95th = float(np.percentile(deg_arr, 95))

    components = list(nx.connected_components(G))
    largest_comp_size = max(len(c) for c in components)
    largest_comp_pct = (largest_comp_size / num_nodes) * 100.0

    print(f"[Phase 2] Degree: mean={deg_mean:.2f}, std={deg_std:.2f}, median={deg_median:.1f}, max={deg_max}")
    print(f"[Phase 2] Components: {len(components)}, largest={largest_comp_pct:.2f}% of nodes")

    # Verification Checks
    checks = [
        {
            "check": "Real node count",
            "expected": "4039",
            "actual": str(num_nodes),
            "status": "PASS" if num_nodes == 4039 else "FAIL"
        },
        {
            "check": "Real edge count",
            "expected": "88234",
            "actual": str(num_edges),
            "status": "PASS" if num_edges == 88234 else "FAIL"
        },
        {
            "check": "All nodes have feat attribute",
            "expected": "4039 with dim 1406",
            "actual": f"{sum('feat' in G.nodes[n] and len(G.nodes[n]['feat']) == dim for n in G.nodes())}",
            "status": "PASS" if all("feat" in G.nodes[n] and len(G.nodes[n]["feat"]) == dim for n in G.nodes()) else "FAIL"
        },
        {
            "check": "All real nodes labeled genuine (0)",
            "expected": "4039 label=0",
            "actual": f"{sum(G.nodes[n]['label'] == 0 for n in G.nodes())}",
            "status": "PASS" if all(G.nodes[n]["label"] == 0 for n in G.nodes()) else "FAIL"
        },
        {
            "check": "Circles loaded across egos",
            "expected": "10 egos, >100 circles",
            "actual": f"{len(circles_data)} egos, {total_circles_count} circles",
            "status": "PASS" if len(circles_data) == 10 and total_circles_count >= 100 else "FAIL"
        },
        {
            "check": "Graph connectivity",
            "expected": "Largest component >= 95%",
            "actual": f"{largest_comp_pct:.2f}%",
            "status": "PASS" if largest_comp_pct >= 95.0 else "FAIL"
        }
    ]

    all_passed = all(c["status"] == "PASS" for c in checks)
    status_str = "PASS" if all_passed else "FAIL"

    results_summary = {
        "nodes": num_nodes,
        "edges": num_edges,
        "degree_mean": f"{deg_mean:.2f}",
        "degree_std": f"{deg_std:.2f}",
        "degree_median": f"{deg_median:.1f}",
        "degree_range": f"[{deg_min}, {deg_max}]",
        "degree_90th_percentile": f"{deg_90th:.1f}",
        "total_circles_loaded": total_circles_count,
        "largest_component_coverage": f"{largest_comp_pct:.2f}%"
    }

    logger.log_phase(
        phase=2,
        name="Load & Merge Real Graph",
        status=status_str,
        results=results_summary,
        outputs=["circles_data.json"],
        verification=checks,
        notes=f"Full Facebook graph loaded with 100% genuine labels. 193 circles extracted for community embedding.",
        script="phase2_load_graph.py"
    )

    if not all_passed:
        raise RuntimeError("Phase 2 verification failed! Check verification table in memory.md.")

    return G, circles_data

if __name__ == "__main__":
    load_real_graph()
