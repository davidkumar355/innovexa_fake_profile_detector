"""
Phase 7: Save Final Artifacts
Finalizes and packages all dataset deliverables into Project Work/Dataset/generated/v1/:
  1. final_edge_list.txt
  2. final_features.npy
  3. final_labels.npy
  4. fake_metadata.csv
  5. global_featnames.txt
  6. id_shuffle_map.json
  7. generation_config.json
  8. validation_report.txt
"""

import os
import json
import shutil
import numpy as np
import pandas as pd
from memory_logger import MemoryLogger

def save_artifacts(
    output_dir=r"Project Work\Dataset\generated\v1",
    memory_file=r"Project Work\memory.md",
    seed=42,
    logger=None
):
    if logger is None:
        logger = MemoryLogger(memory_file)

    output_dir = os.path.abspath(output_dir)
    print(f"[Phase 7] Packaging final dataset deliverables into {output_dir}...")

    # Copy / rename shuffled edges -> final_edge_list.txt
    shuffled_edges = os.path.join(output_dir, "shuffled_edges.txt")
    final_edges = os.path.join(output_dir, "final_edge_list.txt")
    shutil.copyfile(shuffled_edges, final_edges)

    # Copy / rename shuffled features -> final_features.npy
    shuffled_feats = os.path.join(output_dir, "shuffled_features.npy")
    final_feats = os.path.join(output_dir, "final_features.npy")
    shutil.copyfile(shuffled_feats, final_feats)

    # Copy / rename shuffled labels -> final_labels.npy
    shuffled_labels = os.path.join(output_dir, "shuffled_labels.npy")
    final_labels = os.path.join(output_dir, "final_labels.npy")
    shutil.copyfile(shuffled_labels, final_labels)

    # Load arrays to inspect final metrics
    feats = np.load(final_feats)
    labels = np.load(final_labels)
    total_nodes, num_features = feats.shape
    total_fakes = int((labels == 1).sum())
    total_genuine = int((labels == 0).sum())

    with open(final_edges, "r", encoding="utf-8") as f:
        edge_lines = [l.strip() for l in f if l.strip()]
    total_edges = len(edge_lines)

    meta_df = pd.read_csv(os.path.join(output_dir, "fake_metadata.csv"))

    # Generate config / metadata manifest
    config_data = {
        "dataset_name": "Facebook SNAP Augmented (Synthetic Fake Profiles v1)",
        "random_seed": seed,
        "date_created": "2026-10-07",
        "num_total_nodes": total_nodes,
        "num_genuine_nodes": total_genuine,
        "num_fake_nodes": total_fakes,
        "fake_ratio_percent": round((total_fakes / total_nodes) * 100.0, 2),
        "total_edges": total_edges,
        "feature_dimension": num_features,
        "archetypes": {
            "A": {
                "name": "Obvious Bot",
                "count": int((meta_df["archetype"] == "A").sum()),
                "targeting": "uniform_random",
                "features": "low_density_sparse"
            },
            "B": {
                "name": "Hub Targeter",
                "count": int((meta_df["archetype"] == "B").sum()),
                "targeting": "preferential_hub",
                "features": "moderate_density_random"
            },
            "C": {
                "name": "Camouflaged",
                "count": int((meta_df["archetype"] == "C").sum()),
                "targeting": "community_embedded_circle",
                "features": "victim_profile_mimicking"
            },
            "D": {
                "name": "Sybil Ring",
                "count": int((meta_df["archetype"] == "D").sum()),
                "targeting": "sybil_clique_hub_sharing",
                "features": "coordinated_base_template"
            }
        },
        "deliverables": [
            "final_edge_list.txt",
            "final_features.npy",
            "final_labels.npy",
            "fake_metadata.csv",
            "global_featnames.txt",
            "id_shuffle_map.json",
            "generation_config.json",
            "validation_report.txt"
        ]
    }

    config_path = os.path.join(output_dir, "generation_config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)
    print(f"[Phase 7] Configuration manifest written to {config_path}")

    # Check deliverables existence
    expected_files = config_data["deliverables"]
    file_checks = {}
    for fname in expected_files:
        fpath = os.path.join(output_dir, fname)
        file_checks[fname] = os.path.exists(fpath) and os.path.getsize(fpath) > 0

    all_exist = all(file_checks.values())

    # Verification Checks
    checks = [
        {
            "check": "All 8 deliverable files present",
            "expected": "8 files > 0 bytes",
            "actual": f"{sum(file_checks.values())}/8 files present",
            "status": "PASS" if all_exist else "FAIL"
        },
        {
            "check": "Final edge count",
            "expected": "102561 edges",
            "actual": f"{total_edges} edges",
            "status": "PASS" if total_edges == 102561 else "FAIL"
        },
        {
            "check": "Final feature matrix shape",
            "expected": "(4489, 1406)",
            "actual": str(feats.shape),
            "status": "PASS" if feats.shape == (4489, 1406) else "FAIL"
        },
        {
            "check": "Final label classes",
            "expected": "4039 genuine (0), 450 fake (1)",
            "actual": f"{total_genuine} gen, {total_fakes} fake",
            "status": "PASS" if total_genuine == 4039 and total_fakes == 450 else "FAIL"
        },
        {
            "check": "Fake metadata records complete",
            "expected": "450 rows",
            "actual": f"{len(meta_df)} rows",
            "status": "PASS" if len(meta_df) == 450 else "FAIL"
        },
        {
            "check": "generation_config.json valid",
            "expected": "seed=42 present",
            "actual": f"seed={config_data['random_seed']}",
            "status": "PASS" if config_data["random_seed"] == 42 else "FAIL"
        }
    ]

    all_passed = all(c["status"] == "PASS" for c in checks)
    status_str = "PASS" if all_passed else "FAIL"

    results_summary = {
        "final_node_count": total_nodes,
        "final_edge_count": total_edges,
        "genuine_nodes": total_genuine,
        "fake_nodes": total_fakes,
        "fake_ratio_percent": f"{(total_fakes / total_nodes) * 100.0:.2f}%",
        "feature_columns": num_features,
        "total_deliverables_saved": len(expected_files)
    }

    logger.log_phase(
        phase=7,
        name="Save Final Artifacts",
        status=status_str,
        results=results_summary,
        outputs=expected_files,
        verification=checks,
        notes="All 8 standardized artifacts saved to Project Work/Dataset/generated/v1/. Ready for downstream GNN pipeline.",
        script="phase7_save_artifacts.py"
    )

    if not all_passed:
        raise RuntimeError("Phase 7 verification failed! Check missing files.")

    # Print summary table
    print("\n" + "="*60)
    print("        [SUCCESS] SYNTHETIC INJECTION DELIVERABLES READY")
    print("="*60)
    print(f"Total Nodes:          {total_nodes} (Genuine: {total_genuine}, Fake: {total_fakes})")
    print(f"Total Edges:          {total_edges}")
    print(f"Feature Dimension:    {num_features}")
    print(f"Fake Ratio:           {(total_fakes / total_nodes) * 100.0:.2f}% (Realistic Imbalance)")
    print("Deliverables in Project Work/Dataset/generated/v1/:")
    for f in expected_files:
        sz = os.path.getsize(os.path.join(output_dir, f))
        print(f"  - {f:<26} ({sz/1024:.1f} KB)")
    print("="*60 + "\n")

    return config_data

if __name__ == "__main__":
    save_artifacts()
