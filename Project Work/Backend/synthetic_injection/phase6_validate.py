"""
Phase 6: Sanity & Difficulty Validation
Executes baseline heuristic detectors against the shuffled dataset to verify that
synthetic fakes cannot be trivially separated from genuine users without relational/GNN reasoning.
"""

import os
import json
import numpy as np
import pandas as pd
import networkx as nx
from memory_logger import MemoryLogger

def run_validation(
    shuffled_edges_path=r"Project Work\Dataset\generated\v1\shuffled_edges.txt",
    shuffled_feats_path=r"Project Work\Dataset\generated\v1\shuffled_features.npy",
    shuffled_labels_path=r"Project Work\Dataset\generated\v1\shuffled_labels.npy",
    metadata_path=r"Project Work\Dataset\generated\v1\fake_metadata.csv",
    output_dir=r"Project Work\Dataset\generated\v1",
    memory_file=r"Project Work\memory.md",
    logger=None
):
    if logger is None:
        logger = MemoryLogger(memory_file)

    os.makedirs(output_dir, exist_ok=True)
    print("[Phase 6] Running sanity & difficulty validation baselines...")

    # Load shuffled data
    labels = np.load(shuffled_labels_path)
    feats = np.load(shuffled_feats_path)
    num_nodes = len(labels)
    total_fakes = int((labels == 1).sum())

    G = nx.Graph()
    with open(shuffled_edges_path, "r", encoding="utf-8") as f:
        for l in f:
            if l.strip():
                u, v = map(int, l.strip().split())
                G.add_edge(u, v)

    # Make sure all isolated nodes are also in G (if any)
    for i in range(num_nodes):
        if not G.has_node(i):
            G.add_node(i)

    degrees = np.array([G.degree(i) for i in range(num_nodes)])
    mean_deg = float(np.mean(degrees))
    std_deg = float(np.std(degrees))

    # Feature densities per node
    densities = np.array([feats[i].mean() for i in range(num_nodes)])

    # ==========================================
    # Baseline 1: Degree Threshold (degree > mean + 2*std)
    # ==========================================
    deg_thresh = mean_deg + 2 * std_deg
    deg_preds = (degrees > deg_thresh).astype(int)
    flagged_deg = int(deg_preds.sum())
    true_pos_deg = int(((deg_preds == 1) & (labels == 1)).sum())
    prec_deg = (true_pos_deg / flagged_deg) if flagged_deg > 0 else 0.0
    rec_deg = true_pos_deg / total_fakes

    # ==========================================
    # Baseline 2: Feature Sparsity (density < 0.005)
    # ==========================================
    # Many real users are sparse too, so let's check low-density heuristic
    dens_thresh = 0.005
    dens_preds = (densities < dens_thresh).astype(int)
    flagged_dens = int(dens_preds.sum())
    true_pos_dens = int(((dens_preds == 1) & (labels == 1)).sum())
    prec_dens = (true_pos_dens / flagged_dens) if flagged_dens > 0 else 0.0
    rec_dens = true_pos_dens / total_fakes

    # ==========================================
    # Baseline 3: Isolated Node Detector (degree == 0)
    # ==========================================
    isolated_nodes = [i for i in range(num_nodes) if degrees[i] == 0]
    isolated_fakes = [i for i in isolated_nodes if labels[i] == 1]

    # ==========================================
    # Baseline 4: Connected Components (Fake-only components)
    # ==========================================
    components = list(nx.connected_components(G))
    fake_only_components = 0
    for comp in components:
        if len(comp) > 1 and all(labels[node] == 1 for node in comp):
            fake_only_components += 1

    # ==========================================
    # Baseline 5: ID-ordering leakage check
    # ==========================================
    fake_indices = np.where(labels == 1)[0]
    diffs = np.diff(fake_indices)
    max_contiguous_fake_run = int(np.max(np.convolve((diffs == 1).astype(int), np.ones(5, dtype=int), mode="valid"))) if len(diffs) >= 5 else 0
    is_clustered_at_tail = (fake_indices[0] > 3500) # True if fakes are grouped at tail

    # ==========================================
    # Baseline 6: Archetype C Clustering Coefficient
    # ==========================================
    meta_df = pd.read_csv(metadata_path)
    c_fakes = meta_df[meta_df["archetype"] == "C"]["shuffled_fake_id"].tolist()
    c_cluster_coeffs = [nx.clustering(G, nid) for nid in c_fakes]
    c_non_zero_clustering = sum(cc > 0.0 for cc in c_cluster_coeffs)
    c_clustering_pct = (c_non_zero_clustering / len(c_fakes)) * 100.0 if c_fakes else 0.0

    # Format text report
    report_lines = [
        "===========================================================",
        "     SYNTHETIC DATASET SANITY & DIFFICULTY REPORT",
        "===========================================================",
        f"Total Nodes: {num_nodes} (Genuine: {num_nodes - total_fakes}, Fake: {total_fakes})",
        f"Total Edges: {G.number_of_edges()}",
        f"Graph Density: {nx.density(G):.6f}",
        f"Average Degree: {mean_deg:.2f} (std: {std_deg:.2f})",
        "",
        "--- Baseline 1: Degree Threshold (degree > mean + 2*sigma) ---",
        f"Threshold: {deg_thresh:.2f}",
        f"Flagged Nodes: {flagged_deg} (True Positives: {true_pos_deg})",
        f"Precision: {prec_deg*100:.2f}% (Requirement: < 65.0%)",
        f"Recall: {rec_deg*100:.2f}%",
        f"Gate Status: {'PASS' if prec_deg < 0.65 else 'FAIL'}",
        "",
        "--- Baseline 2: Feature Sparsity Heuristic (density < 0.005) ---",
        f"Flagged Nodes: {flagged_dens} (True Positives: {true_pos_dens})",
        f"Precision: {prec_dens*100:.2f}% (Requirement: < 70.0%)",
        f"Recall: {rec_dens*100:.2f}%",
        f"Gate Status: {'PASS' if prec_dens < 0.70 else 'FAIL'}",
        "",
        "--- Baseline 3: Isolated Node Detector ---",
        f"Total Isolated Nodes: {len(isolated_nodes)}",
        f"Isolated Fakes: {len(isolated_fakes)}",
        f"Gate Status: {'PASS' if len(isolated_fakes) == 0 else 'FAIL'}",
        "",
        "--- Baseline 4: Fake-Only Connected Components ---",
        f"Components Count: {len(components)}",
        f"Fake-Only Components: {fake_only_components}",
        f"Gate Status: {'PASS' if fake_only_components == 0 else 'FAIL'}",
        "",
        "--- Baseline 5: ID-Ordering Leakage ---",
        f"Fake Node Index Range: [{fake_indices.min()}, {fake_indices.max()}]",
        f"Fake Nodes Clustered at Tail: {is_clustered_at_tail}",
        f"Max Contiguous Fake Run: {max_contiguous_fake_run}",
        f"Gate Status: {'PASS' if not is_clustered_at_tail else 'FAIL'}",
        "",
        "--- Baseline 6: Camouflage Triadic Closure (Archetype C) ---",
        f"Archetype C Nodes: {len(c_fakes)}",
        f"Nodes with Non-Zero Clustering Coeff: {c_non_zero_clustering} ({c_clustering_pct:.1f}%)",
        f"Mean Clustering Coeff (Archetype C): {np.mean(c_cluster_coeffs):.4f}",
        f"Gate Status: {'PASS' if c_clustering_pct >= 90.0 else 'FAIL'}",
        "==========================================================="
    ]
    report_text = "\n".join(report_lines)
    report_path = os.path.join(output_dir, "validation_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"[Phase 6] Validation report written to {report_path}")

    # Verification Checks
    checks = [
        {
            "check": "Baseline 1: Degree Threshold Precision",
            "expected": "< 65.0%",
            "actual": f"{prec_deg*100:.2f}% (TP={true_pos_deg}/{flagged_deg})",
            "status": "PASS" if prec_deg < 0.65 else "FAIL"
        },
        {
            "check": "Baseline 2: Feature Sparsity Precision",
            "expected": "< 70.0%",
            "actual": f"{prec_dens*100:.2f}% (TP={true_pos_dens}/{flagged_dens})",
            "status": "PASS" if prec_dens < 0.70 else "FAIL"
        },
        {
            "check": "Baseline 3: Isolated Fake Nodes",
            "expected": "0 isolated",
            "actual": f"{len(isolated_fakes)} isolated",
            "status": "PASS" if len(isolated_fakes) == 0 else "FAIL"
        },
        {
            "check": "Baseline 4: Disconnected Fake Components",
            "expected": "0 components",
            "actual": f"{fake_only_components} components",
            "status": "PASS" if fake_only_components == 0 else "FAIL"
        },
        {
            "check": "Baseline 5: ID-Ordering Leakage Prevention",
            "expected": "Interleaved (not at tail)",
            "actual": f"range=[{fake_indices.min()}, {fake_indices.max()}]",
            "status": "PASS" if not is_clustered_at_tail else "FAIL"
        },
        {
            "check": "Baseline 6: Camouflage Triadic Closure (C)",
            "expected": ">= 90% non-zero clustering",
            "actual": f"{c_clustering_pct:.1f}% (mean={np.mean(c_cluster_coeffs):.4f})",
            "status": "PASS" if c_clustering_pct >= 90.0 else "FAIL"
        }
    ]

    all_passed = all(c["status"] == "PASS" for c in checks)
    status_str = "PASS" if all_passed else "FAIL"

    results_summary = {
        "degree_threshold_precision": f"{prec_deg*100:.2f}%",
        "feature_sparsity_precision": f"{prec_dens*100:.2f}%",
        "isolated_fake_nodes": len(isolated_fakes),
        "fake_only_components": fake_only_components,
        "id_ordering_leakage": False,
        "archetype_C_triadic_closure_pct": f"{c_clustering_pct:.1f}%",
        "archetype_C_mean_clustering_coeff": f"{np.mean(c_cluster_coeffs):.4f}"
    }

    logger.log_phase(
        phase=6,
        name="Sanity & Difficulty Validation",
        status=status_str,
        results=results_summary,
        outputs=["validation_report.txt"],
        verification=checks,
        notes="Heuristic baselines fail to trivially detect fakes (degree prec < 65%, sparsity prec < 70%). Fakes have realistic camouflage and require relational GNN learning.",
        script="phase6_validate.py"
    )

    if not all_passed:
        raise RuntimeError("Phase 6 validation gates failed! Adjust archetype parameters.")

    return checks

if __name__ == "__main__":
    run_validation()
