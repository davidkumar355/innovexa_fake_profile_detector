"""
run_injection_pipeline.py
Master Orchestrator for the Synthetic Fake Profile Injection Pipeline.
Executes all 7 phases in sequence and runs the end-to-end acceptance audit:
  Phase 1: Build Unified Feature Space across 10 Ego Networks
  Phase 2: Load & Merge Real Facebook Graph
  Phase 3: Generate 450 Fake Profiles across 4 Difficulty Archetypes
  Phase 4: Inject Fake Nodes & Edges into the Graph
  Phase 5: Randomly Shuffle Node IDs to Eliminate Ordering Leakage
  Phase 6: Sanity & Difficulty Baseline Validation
  Phase 7: Save & Package All Final Deliverables
  E2E:     Comprehensive Acceptance Test (verify_pipeline.py)
All progress, metrics, and verification results are logged to Project Work/memory.md.
"""

import sys
import os

# Add script directory to sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from memory_logger import MemoryLogger
import phase1_build_feature_space
import phase2_load_graph
import phase3_generate_fakes
import phase4_inject
import phase5_shuffle_ids
import phase6_validate
import phase7_save_artifacts
import verify_pipeline

def main():
    print("="*70)
    print("   INNOVEXA: SYNTHETIC FAKE PROFILE INJECTION PIPELINE")
    print("="*70)

    base_dir = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
    dataset_dir = os.path.join(base_dir, "Dataset")
    output_dir = os.path.join(dataset_dir, "generated", "v1")
    memory_file = os.path.join(base_dir, "memory.md")

    tar_path = os.path.join(dataset_dir, "facebook.tar.gz")
    edges_path = os.path.join(dataset_dir, "facebook_combined.txt")

    logger = MemoryLogger(memory_file)
    seed = 42
    total_fakes = 450

    print(f"Target Output Directory: {output_dir}")
    print(f"Memory Log File:         {memory_file}")
    print(f"Random Seed:             {seed}")
    print(f"Total Fake Profiles:     {total_fakes}")
    print("="*70 + "\n")

    try:
        # Phase 1
        print(">>> [1/7] Executing Phase 1: Build Unified Feature Space...")
        phase1_build_feature_space.build_feature_space(
            tar_path=tar_path,
            output_dir=output_dir,
            logger=logger
        )

        # Phase 2
        print("\n>>> [2/7] Executing Phase 2: Load & Merge Real Graph...")
        phase2_load_graph.load_real_graph(
            edges_path=edges_path,
            tar_path=tar_path,
            features_path=os.path.join(output_dir, "unified_features_real.npy"),
            output_dir=output_dir,
            logger=logger
        )

        # Phase 3
        print("\n>>> [3/7] Executing Phase 3: Generate Fake Nodes per Archetype...")
        phase3_generate_fakes.generate_fakes(
            features_path=os.path.join(output_dir, "unified_features_real.npy"),
            circles_path=os.path.join(output_dir, "circles_data.json"),
            edges_path=edges_path,
            output_dir=output_dir,
            seed=seed,
            total_fakes=total_fakes,
            logger=logger
        )

        # Phase 4
        print("\n>>> [4/7] Executing Phase 4: Inject into Graph...")
        phase4_inject.inject_fakes(
            edges_path=edges_path,
            real_feats_path=os.path.join(output_dir, "unified_features_real.npy"),
            fake_bundle_path=os.path.join(output_dir, "fake_bundle.json"),
            fake_feats_path=os.path.join(output_dir, "fake_features.npy"),
            output_dir=output_dir,
            logger=logger
        )

        # Phase 5
        print("\n>>> [5/7] Executing Phase 5: Shuffle Node IDs...")
        phase5_shuffle_ids.shuffle_node_ids(
            preshuffle_feats_path=os.path.join(output_dir, "augmented_features_preshuffle.npy"),
            preshuffle_labels_path=os.path.join(output_dir, "augmented_labels_preshuffle.npy"),
            preshuffle_edges_path=os.path.join(output_dir, "augmented_edges_preshuffle.txt"),
            metadata_path=os.path.join(output_dir, "fake_metadata.csv"),
            output_dir=output_dir,
            seed=seed,
            logger=logger
        )

        # Phase 6
        print("\n>>> [6/7] Executing Phase 6: Sanity & Difficulty Validation...")
        phase6_validate.run_validation(
            shuffled_edges_path=os.path.join(output_dir, "shuffled_edges.txt"),
            shuffled_feats_path=os.path.join(output_dir, "shuffled_features.npy"),
            shuffled_labels_path=os.path.join(output_dir, "shuffled_labels.npy"),
            metadata_path=os.path.join(output_dir, "fake_metadata.csv"),
            output_dir=output_dir,
            logger=logger
        )

        # Phase 7
        print("\n>>> [7/7] Executing Phase 7: Save & Package Final Artifacts...")
        phase7_save_artifacts.save_artifacts(
            output_dir=output_dir,
            seed=seed,
            logger=logger
        )

        # E2E Acceptance Audit
        print("\n>>> [E2E] Running Comprehensive Acceptance Test...")
        verify_pipeline.run_e2e_verification(
            data_dir=output_dir,
            logger=logger
        )

        print("\n" + "="*70)
        print("   [SUCCESS] PIPELINE COMPLETED SUCCESSFULLY!")
        print("   All results, metrics, and checks logged to Project Work/memory.md")
        print(f"   Deliverables saved to: {output_dir}")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\n[ERROR] Pipeline aborted: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
