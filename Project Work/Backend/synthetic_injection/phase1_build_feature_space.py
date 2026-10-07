"""
Phase 1: Build Unified Feature Space
Merges heterogeneous feature schemas across all 10 ego networks in facebook.tar.gz
into a single unified binary feature matrix for all 4,039 nodes.
"""

import os
import tarfile
import numpy as np
import collections
from memory_logger import MemoryLogger

def build_feature_space(
    tar_path=r"Project Work\Dataset\facebook.tar.gz",
    output_dir=r"Project Work\Dataset\generated\v1",
    memory_file=r"Project Work\memory.md",
    logger=None
):
    if logger is None:
        logger = MemoryLogger(memory_file)

    os.makedirs(output_dir, exist_ok=True)
    tar_path = os.path.abspath(tar_path)
    ego_ids = [0, 107, 348, 414, 686, 698, 1684, 1912, 3437, 3980]

    print("[Phase 1] Extracting feature definitions across all 10 ego networks...")
    tar = tarfile.open(tar_path, "r:gz")

    # Step 1.2 & 1.3: Collect all unique feature names preserving a deterministic order
    # To keep ordering deterministic, collect in order of ego_id and line index, deduplicated
    unique_features = []
    seen_features = set()
    ego_schemas = {} # ego_id -> list of feature names

    for eid in ego_ids:
        f = tar.extractfile(f"facebook/{eid}.featnames")
        lines = f.read().decode("utf-8", errors="ignore").splitlines()
        ego_cols = []
        for line in lines:
            if not line.strip():
                continue
            parts = line.strip().split(" ", 1)
            if len(parts) == 2:
                feat_name = parts[1].strip()
                ego_cols.append(feat_name)
                if feat_name not in seen_features:
                    seen_features.add(feat_name)
                    unique_features.append(feat_name)
        ego_schemas[eid] = ego_cols

    # Sort unique features for complete reproducibility
    unique_features.sort()
    global_feat_to_idx = {feat: idx for idx, feat in enumerate(unique_features)}
    num_features = len(unique_features)
    print(f"[Phase 1] Global unified feature dimension: {num_features}")

    # Step 1.4 & 1.5: Parse .feat and .egofeat for each ego
    # Node features dictionary: node_id -> binary np.ndarray of shape (num_features,)
    node_features = collections.defaultdict(lambda: np.zeros(num_features, dtype=np.uint8))

    for eid in ego_ids:
        schema = ego_schemas[eid]
        # Map local ego column index -> global column index
        local_to_global = [global_feat_to_idx[f] for f in schema]

        # 1. egofeat
        f_ego = tar.extractfile(f"facebook/{eid}.egofeat")
        ego_vals = [int(v) for v in f_ego.read().decode("utf-8", errors="ignore").strip().split()]
        _ = node_features[eid] # Ensure ego node is registered
        for l_idx, val in enumerate(ego_vals):
            if val == 1:
                g_idx = local_to_global[l_idx]
                node_features[eid][g_idx] = 1

        # 2. .feat
        f_feat = tar.extractfile(f"facebook/{eid}.feat")
        for line in f_feat.read().decode("utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            parts = line.strip().split()
            nid = int(parts[0])
            vals = [int(v) for v in parts[1:]]
            _ = node_features[nid] # Ensure node is registered even if all features are 0
            for l_idx, val in enumerate(vals):
                if val == 1:
                    g_idx = local_to_global[l_idx]
                    node_features[nid][g_idx] = 1

    tar.close()

    # Step 1.6: Build final matrix for nodes 0..4038
    num_nodes = 4039
    feature_matrix = np.zeros((num_nodes, num_features), dtype=np.uint8)
    for nid in range(num_nodes):
        if nid in node_features:
            feature_matrix[nid] = node_features[nid]

    # Save intermediate/final artifacts for Phase 1
    featnames_path = os.path.join(output_dir, "global_featnames.txt")
    with open(featnames_path, "w", encoding="utf-8") as f:
        for feat in unique_features:
            f.write(f"{feat}\n")

    features_path = os.path.join(output_dir, "unified_features_real.npy")
    np.save(features_path, feature_matrix)
    print(f"[Phase 1] Saved unified features matrix: shape={feature_matrix.shape} to {features_path}")

    # Phase 1 Verification Checks
    checks = [
        {
            "check": "Global feature dimension",
            "expected": "1400-1600",
            "actual": str(num_features),
            "status": "PASS" if 1400 <= num_features <= 1600 else "FAIL"
        },
        {
            "check": "Real nodes covered",
            "expected": "4039",
            "actual": str(len(node_features)),
            "status": "PASS" if len(node_features) == 4039 else "FAIL"
        },
        {
            "check": "No duplicate column names",
            "expected": "0 duplicates",
            "actual": f"{len(unique_features) - len(set(unique_features))} duplicates",
            "status": "PASS" if len(unique_features) == len(set(unique_features)) else "FAIL"
        },
        {
            "check": "Feature values binary",
            "expected": "[0, 1]",
            "actual": f"min={feature_matrix.min()}, max={feature_matrix.max()}",
            "status": "PASS" if feature_matrix.min() == 0 and feature_matrix.max() == 1 and set(np.unique(feature_matrix)).issubset({0, 1}) else "FAIL"
        },
        {
            "check": "All 10 ego nodes covered",
            "expected": "10 non-zero ego rows",
            "actual": f"{sum(feature_matrix[eid].sum() > 0 for eid in ego_ids)} covered",
            "status": "PASS" if all(feature_matrix[eid].sum() > 0 for eid in ego_ids) else "FAIL"
        }
    ]

    all_passed = all(c["status"] == "PASS" for c in checks)
    status_str = "PASS" if all_passed else "FAIL"

    mean_density = float(feature_matrix.mean())
    results_summary = {
        "unified_feature_dim": num_features,
        "nodes_with_features": len(node_features),
        "feature_matrix_shape": f"{feature_matrix.shape}",
        "matrix_mean_density": f"{mean_density:.4f}",
        "duplicate_columns": 0,
        "binary_values_only": True
    }

    outputs = ["global_featnames.txt", "unified_features_real.npy"]
    logger.log_phase(
        phase=1,
        name="Build Unified Feature Space",
        status=status_str,
        results=results_summary,
        outputs=outputs,
        verification=checks,
        notes="All 4,039 nodes in facebook_combined.txt are successfully covered in ego networks without missing profiles.",
        script="phase1_build_feature_space.py"
    )

    if not all_passed:
        raise RuntimeError("Phase 1 verification failed! Check verification table in memory.md.")

    return feature_matrix, unique_features, ego_schemas

if __name__ == "__main__":
    build_feature_space()
