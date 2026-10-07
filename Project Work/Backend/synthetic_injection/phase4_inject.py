"""
Phase 4: Inject Into Graph
Injects 450 fake nodes and their generated edges (external targets + Sybil ring cliques)
into the real Facebook graph. Attaches features and fake labels (1).
"""

import os
import json
import numpy as np
import networkx as nx
from memory_logger import MemoryLogger

def inject_fakes(
    edges_path=r"Project Work\Dataset\facebook_combined.txt",
    real_feats_path=r"Project Work\Dataset\generated\v1\unified_features_real.npy",
    fake_bundle_path=r"Project Work\Dataset\generated\v1\fake_bundle.json",
    fake_feats_path=r"Project Work\Dataset\generated\v1\fake_features.npy",
    output_dir=r"Project Work\Dataset\generated\v1",
    memory_file=r"Project Work\memory.md",
    logger=None
):
    if logger is None:
        logger = MemoryLogger(memory_file)

    os.makedirs(output_dir, exist_ok=True)
    print("[Phase 4] Injecting fake nodes and edges into the Facebook graph...")

    # Load real graph
    G = nx.Graph()
    with open(edges_path, "r", encoding="utf-8") as f:
        for l in f:
            if l.strip():
                u, v = map(int, l.strip().split())
                G.add_edge(u, v)

    num_real_nodes = G.number_of_nodes()
    real_edges_count = G.number_of_edges()

    # Load features
    real_feats = np.load(real_feats_path)
    fake_feats = np.load(fake_feats_path)
    total_fakes = fake_feats.shape[0]

    # Load fake bundle
    with open(fake_bundle_path, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    fake_profiles = bundle["fake_profiles"]
    ring_inter_edges = bundle["ring_inter_edges"]

    # Assign real nodes label=0 and features
    for n in range(num_real_nodes):
        G.nodes[n]["label"] = 0
        G.nodes[n]["feat"] = real_feats[n]

    # Inject fakes
    fake_edges_to_real = 0
    fake_real_degrees = {}

    for str_fid, p in fake_profiles.items():
        fid = int(str_fid)
        local_idx = fid - num_real_nodes
        G.add_node(fid, label=1, feat=fake_feats[local_idx], archetype=p["archetype"])

        targets = [int(t) for t in p["targets"]]
        # External edges to real graph
        edges_into_real = 0
        for tgt in targets:
            if tgt < num_real_nodes:
                G.add_edge(fid, tgt)
                edges_into_real += 1
                fake_edges_to_real += 1
            else:
                G.add_edge(fid, tgt)
        fake_real_degrees[fid] = edges_into_real

    # Add Sybil ring clique edges
    for u, v in ring_inter_edges:
        G.add_edge(u, v)

    total_nodes = G.number_of_nodes()
    total_edges = G.number_of_edges()
    injected_edges_count = total_edges - real_edges_count

    # Build stacked feature matrix and label vector (pre-shuffle)
    augmented_feats = np.vstack([real_feats, fake_feats])
    augmented_labels = np.zeros(total_nodes, dtype=np.uint8)
    augmented_labels[num_real_nodes:] = 1

    # Save pre-shuffle graph artifacts
    np.save(os.path.join(output_dir, "augmented_features_preshuffle.npy"), augmented_feats)
    np.save(os.path.join(output_dir, "augmented_labels_preshuffle.npy"), augmented_labels)
    
    # Save edge list pre-shuffle
    with open(os.path.join(output_dir, "augmented_edges_preshuffle.txt"), "w", encoding="utf-8") as f:
        for u, v in G.edges():
            f.write(f"{u} {v}\n")

    print(f"[Phase 4] Graph augmented: {total_nodes} nodes, {total_edges} edges ({injected_edges_count} new edges)")

    # Connectivity checks
    components = list(nx.connected_components(G))
    largest_comp = max(len(c) for c in components)
    comp_pct = (largest_comp / total_nodes) * 100.0

    isolated_fakes = sum(fake_real_degrees[fid] == 0 for fid in fake_real_degrees)

    # Verification Checks
    checks = [
        {
            "check": "Total node count",
            "expected": "4489",
            "actual": str(total_nodes),
            "status": "PASS" if total_nodes == 4489 else "FAIL"
        },
        {
            "check": "Total fake labels count",
            "expected": "450 label=1",
            "actual": str(int((augmented_labels == 1).sum())),
            "status": "PASS" if (augmented_labels == 1).sum() == 450 else "FAIL"
        },
        {
            "check": "No isolated fake nodes (edges to real graph)",
            "expected": "0 isolated",
            "actual": f"{isolated_fakes} isolated",
            "status": "PASS" if isolated_fakes == 0 else "FAIL"
        },
        {
            "check": "Feature matrix shape",
            "expected": "(4489, 1406)",
            "actual": str(augmented_feats.shape),
            "status": "PASS" if augmented_feats.shape == (4489, real_feats.shape[1]) else "FAIL"
        },
        {
            "check": "No NaN values in feature matrix",
            "expected": "0 NaN",
            "actual": "0 NaN" if not np.isnan(augmented_feats).any() else "Found NaN",
            "status": "PASS" if not np.isnan(augmented_feats).any() else "FAIL"
        },
        {
            "check": "Graph connectivity post-injection",
            "expected": "Largest component >= 99%",
            "actual": f"{comp_pct:.2f}%",
            "status": "PASS" if comp_pct >= 99.0 else "FAIL"
        }
    ]

    all_passed = all(c["status"] == "PASS" for c in checks)
    status_str = "PASS" if all_passed else "FAIL"

    results_summary = {
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "real_edges": real_edges_count,
        "injected_edges": injected_edges_count,
        "fake_to_real_edges": fake_edges_to_real,
        "sybil_ring_internal_edges": len(ring_inter_edges),
        "isolated_fakes_count": isolated_fakes,
        "largest_component_coverage": f"{comp_pct:.2f}%"
    }

    logger.log_phase(
        phase=4,
        name="Inject Into Graph",
        status=status_str,
        results=results_summary,
        outputs=["augmented_features_preshuffle.npy", "augmented_labels_preshuffle.npy", "augmented_edges_preshuffle.txt"],
        verification=checks,
        notes=f"Successfully injected 450 fake profiles and {injected_edges_count} edges into Facebook graph. Zero isolated fakes.",
        script="phase4_inject.py"
    )

    if not all_passed:
        raise RuntimeError("Phase 4 verification failed! Check verification table in memory.md.")

    return G, augmented_feats, augmented_labels

if __name__ == "__main__":
    inject_fakes()
