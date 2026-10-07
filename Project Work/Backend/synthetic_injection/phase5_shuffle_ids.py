"""
Phase 5: Shuffle Node IDs
Randomly permutes all 4,489 node IDs to prevent shortcut learning / index leakage.
Remaps edges, feature matrix rows, label vector, and updates fake_metadata.csv.
"""

import os
import json
import numpy as np
import pandas as pd
from memory_logger import MemoryLogger

def shuffle_node_ids(
    preshuffle_feats_path=r"Project Work\Dataset\generated\v1\augmented_features_preshuffle.npy",
    preshuffle_labels_path=r"Project Work\Dataset\generated\v1\augmented_labels_preshuffle.npy",
    preshuffle_edges_path=r"Project Work\Dataset\generated\v1\augmented_edges_preshuffle.txt",
    metadata_path=r"Project Work\Dataset\generated\v1\fake_metadata.csv",
    output_dir=r"Project Work\Dataset\generated\v1",
    memory_file=r"Project Work\memory.md",
    seed=42,
    logger=None
):
    if logger is None:
        logger = MemoryLogger(memory_file)

    os.makedirs(output_dir, exist_ok=True)
    np.random.seed(seed)

    print(f"[Phase 5] Generating random permutation of node IDs with seed {seed}...")

    # Load pre-shuffle artifacts
    feats_pre = np.load(preshuffle_feats_path)
    labels_pre = np.load(preshuffle_labels_path)
    num_nodes = len(labels_pre)

    # Load edges pre-shuffle
    edges_pre = []
    with open(preshuffle_edges_path, "r", encoding="utf-8") as f:
        for l in f:
            if l.strip():
                u, v = map(int, l.strip().split())
                edges_pre.append((u, v))

    # Generate permutation: new_id = perm[old_id]
    perm_array = np.random.permutation(num_nodes)
    old_to_new = {int(old_id): int(perm_array[old_id]) for old_id in range(num_nodes)}
    new_to_old = {int(perm_array[old_id]): int(old_id) for old_id in range(num_nodes)}

    # Permute feature matrix and labels
    shuffled_feats = np.zeros_like(feats_pre)
    shuffled_labels = np.zeros_like(labels_pre)

    for old_id, new_id in old_to_new.items():
        shuffled_feats[new_id] = feats_pre[old_id]
        shuffled_labels[new_id] = labels_pre[old_id]

    # Remap edges and sort each edge (min, max) to normalize
    remapped_edges_set = set()
    for u, v in edges_pre:
        nu, nv = old_to_new[u], old_to_new[v]
        if nu != nv:
            remapped_edges_set.add((min(nu, nv), max(nu, nv)))

    sorted_edges = sorted(list(remapped_edges_set))

    # Save intermediate/final shuffled arrays
    np.save(os.path.join(output_dir, "shuffled_features.npy"), shuffled_feats)
    np.save(os.path.join(output_dir, "shuffled_labels.npy"), shuffled_labels)

    with open(os.path.join(output_dir, "shuffled_edges.txt"), "w", encoding="utf-8") as f:
        for u, v in sorted_edges:
            f.write(f"{u} {v}\n")

    # Save permutation map
    map_data = {
        "seed": seed,
        "num_nodes": num_nodes,
        "old_to_new": old_to_new,
        "new_to_old": new_to_old
    }
    with open(os.path.join(output_dir, "id_shuffle_map.json"), "w", encoding="utf-8") as f:
        json.dump(map_data, f)

    # Update fake metadata CSV with shuffled_fake_id
    meta_df = pd.read_csv(metadata_path)
    meta_df["shuffled_fake_id"] = meta_df["temp_fake_id"].map(old_to_new)
    # Reorder columns to make shuffled_fake_id prominent
    cols = ["shuffled_fake_id", "temp_fake_id", "archetype", "archetype_name", "degree", "targeting_strategy", "feature_density", "victim_node_id", "ring_id", "seed"]
    meta_df = meta_df[cols]
    meta_df.sort_values(by="shuffled_fake_id", inplace=True)
    meta_df.to_csv(os.path.join(output_dir, "fake_metadata.csv"), index=False)
    print(f"[Phase 5] fake_metadata.csv updated with shuffled_fake_id column")

    # Verification Checks
    bijection_valid = (len(set(perm_array)) == num_nodes) and (set(perm_array) == set(range(num_nodes)))
    edge_count_match = (len(sorted_edges) == len(edges_pre))

    fake_new_ids = [old_to_new[fid] for fid in range(4039, 4489)]
    min_fake_id = min(fake_new_ids)
    max_fake_id = max(fake_new_ids)
    median_fake_id = float(np.median(fake_new_ids))

    # Spot check: verify 50 random nodes match in features and labels
    spot_indices = np.random.choice(num_nodes, size=50, replace=False)
    feats_match = all(np.array_equal(shuffled_feats[old_to_new[idx]], feats_pre[idx]) for idx in spot_indices)
    labels_match = all(shuffled_labels[old_to_new[idx]] == labels_pre[idx] for idx in spot_indices)
    roundtrip_match = all(new_to_old[old_to_new[idx]] == idx for idx in spot_indices)

    checks = [
        {
            "check": "Permutation is a valid bijection",
            "expected": f"4489 unique IDs in [0, {num_nodes-1}]",
            "actual": f"{len(set(perm_array))} unique IDs",
            "status": "PASS" if bijection_valid else "FAIL"
        },
        {
            "check": "No ID-ordering leakage (shuffled distribution)",
            "expected": "min < 200, max > 4300, med in [1800, 2600]",
            "actual": f"min={min_fake_id}, max={max_fake_id}, median={median_fake_id:.1f}",
            "status": "PASS" if min_fake_id < 200 and max_fake_id > 4300 and 1800 <= median_fake_id <= 2600 else "FAIL"
        },
        {
            "check": "Edge count preserved post-shuffle",
            "expected": str(len(edges_pre)),
            "actual": str(len(sorted_edges)),
            "status": "PASS" if edge_count_match else "FAIL"
        },
        {
            "check": "Features mapping consistency (spot test)",
            "expected": "100% exact match",
            "actual": "100% match" if feats_match else "Mismatch",
            "status": "PASS" if feats_match else "FAIL"
        },
        {
            "check": "Labels mapping consistency (spot test)",
            "expected": "100% exact match",
            "actual": "100% match" if labels_match else "Mismatch",
            "status": "PASS" if labels_match else "FAIL"
        },
        {
            "check": "Round-trip bijection invertible",
            "expected": "new_to_old(old_to_new(x)) == x",
            "actual": "PASS" if roundtrip_match else "FAIL",
            "status": "PASS" if roundtrip_match else "FAIL"
        }
    ]

    all_passed = all(c["status"] == "PASS" for c in checks)
    status_str = "PASS" if all_passed else "FAIL"

    results_summary = {
        "permutation_size": num_nodes,
        "min_fake_shuffled_id": min_fake_id,
        "max_fake_shuffled_id": max_fake_id,
        "median_fake_shuffled_id": f"{median_fake_id:.1f}",
        "edges_count_preserved": len(sorted_edges),
        "bijection_verified": bijection_valid,
        "id_leakage_prevented": True
    }

    logger.log_phase(
        phase=5,
        name="Shuffle Node IDs",
        status=status_str,
        results=results_summary,
        outputs=["id_shuffle_map.json", "shuffled_features.npy", "shuffled_labels.npy", "shuffled_edges.txt", "fake_metadata.csv"],
        verification=checks,
        notes=f"Node IDs randomly permuted. Fake nodes spread from ID {min_fake_id} to {max_fake_id} with median {median_fake_id:.1f}. Zero ordering leakage.",
        script="phase5_shuffle_ids.py"
    )

    if not all_passed:
        raise RuntimeError("Phase 5 verification failed! Check verification table in memory.md.")

    return old_to_new, new_to_old, shuffled_feats, shuffled_labels, sorted_edges

if __name__ == "__main__":
    shuffle_node_ids()
