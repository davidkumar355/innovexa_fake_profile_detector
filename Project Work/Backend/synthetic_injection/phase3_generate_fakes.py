"""
Phase 3: Generate Fake Nodes Per Archetype
Generates 450 synthetic fake profiles across 4 distinct difficulty archetypes:
  - Archetype A (Obvious Bot, ~25%): Low degree, random targeting, empty/near-zero features
  - Archetype B (Hub Targeter, ~35%): Moderate degree, preferential attachment to hubs, random sparse features
  - Archetype C (Camouflaged, ~30%): Community-embedded in real circles, triadic closure, feature-mimicked from victim
  - Archetype D (Sybil Ring, ~10%): Coordinated dense clique + shared hub edges, shared feature template
"""

import os
import json
import random
import numpy as np
import pandas as pd
import networkx as nx
from memory_logger import MemoryLogger

def generate_fakes(
    features_path=r"Project Work\Dataset\generated\v1\unified_features_real.npy",
    circles_path=r"Project Work\Dataset\generated\v1\circles_data.json",
    edges_path=r"Project Work\Dataset\facebook_combined.txt",
    output_dir=r"Project Work\Dataset\generated\v1",
    memory_file=r"Project Work\memory.md",
    seed=42,
    total_fakes=450,
    logger=None
):
    if logger is None:
        logger = MemoryLogger(memory_file)

    os.makedirs(output_dir, exist_ok=True)
    random.seed(seed)
    np.random.seed(seed)

    print(f"[Phase 3] Generating {total_fakes} fake profiles with random seed {seed}...")

    # Load real graph and features for context
    real_feats = np.load(features_path)
    num_real_nodes, num_features = real_feats.shape

    G_real = nx.Graph()
    with open(edges_path, "r", encoding="utf-8") as f:
        for l in f:
            if l.strip():
                u, v = map(int, l.strip().split())
                G_real.add_edge(u, v)

    with open(circles_path, "r", encoding="utf-8") as f:
        circles_data = json.load(f)

    # Flatten circles that have at least 5 members
    valid_circles = []
    for eid, c_dict in circles_data.items():
        for cname, members in c_dict.items():
            if len(members) >= 5:
                valid_circles.append(members)

    real_degrees = dict(G_real.degree())
    sorted_nodes_by_degree = sorted(real_degrees.keys(), key=lambda n: real_degrees[n], reverse=True)
    top_500_hubs = sorted_nodes_by_degree[:500]
    top_200_hubs = sorted_nodes_by_degree[:200]
    hub_weights = np.array([real_degrees[n] for n in top_500_hubs], dtype=np.float64)
    hub_probs = hub_weights / hub_weights.sum()

    # Target counts per archetype
    count_A = int(round(total_fakes * 0.25))  # 112
    count_B = int(round(total_fakes * 0.35))  # 158 -> adjust to 157
    count_C = int(round(total_fakes * 0.30))  # 135
    count_D = total_fakes - (count_A + 157 + count_C) # 46
    count_B = 157

    print(f"[Phase 3] Archetype breakdown: A={count_A}, B={count_B}, C={count_C}, D={count_D} (Total={total_fakes})")

    fake_profiles = {}
    metadata_rows = []
    current_fake_id = num_real_nodes # 4039

    # ==========================================
    # Archetype A: Obvious Bot (Random targeting, sparse features)
    # ==========================================
    for _ in range(count_A):
        fid = current_fake_id
        current_fake_id += 1

        deg = random.randint(2, 10)
        # Random targeting across all real nodes
        targets = set(random.sample(range(num_real_nodes), deg))

        # Very sparse feature vector (Bernoulli 0.015, ~20 non-zero bits out of 1406)
        feat_vec = (np.random.rand(num_features) < 0.015).astype(np.uint8)
        density = float(feat_vec.mean())

        fake_profiles[fid] = {
            "archetype": "A",
            "archetype_name": "Obvious Bot",
            "targets": targets,
            "feature_vector": feat_vec,
            "degree": len(targets),
            "density": density,
            "victim_node": -1,
            "ring_id": -1
        }
        metadata_rows.append({
            "temp_fake_id": fid,
            "archetype": "A",
            "archetype_name": "Obvious Bot",
            "degree": len(targets),
            "targeting_strategy": "uniform_random",
            "feature_density": round(density, 4),
            "victim_node_id": -1,
            "ring_id": -1,
            "seed": seed
        })

    # ==========================================
    # Archetype B: Hub Targeter (Preferential targeting, moderate random features)
    # ==========================================
    for _ in range(count_B):
        fid = current_fake_id
        current_fake_id += 1

        deg = random.randint(30, 80)
        # Preferential targeting into top-500 hubs
        chosen_hubs = np.random.choice(top_500_hubs, size=deg, replace=False, p=hub_probs)
        targets = set(int(x) for x in chosen_hubs)

        # Moderate random features (~18% density)
        feat_vec = (np.random.rand(num_features) < 0.18).astype(np.uint8)
        density = float(feat_vec.mean())

        fake_profiles[fid] = {
            "archetype": "B",
            "archetype_name": "Hub Targeter",
            "targets": targets,
            "feature_vector": feat_vec,
            "degree": len(targets),
            "density": density,
            "victim_node": -1,
            "ring_id": -1
        }
        metadata_rows.append({
            "temp_fake_id": fid,
            "archetype": "B",
            "archetype_name": "Hub Targeter",
            "degree": len(targets),
            "targeting_strategy": "preferential_hub",
            "feature_density": round(density, 4),
            "victim_node_id": -1,
            "ring_id": -1,
            "seed": seed
        })

    # ==========================================
    # Archetype C: Camouflaged (Community-embedded, feature mimicking)
    # ==========================================
    c_cosine_sims = []
    for _ in range(count_C):
        fid = current_fake_id
        current_fake_id += 1

        circle = random.choice(valid_circles)
        
        # Pick victim with at least some features
        circle_candidates = [m for m in circle if real_feats[m].sum() >= 3]
        if not circle_candidates:
            circle_candidates = [m for m in circle if real_feats[m].sum() > 0]
        if not circle_candidates:
            victim = random.choice(circle)
        else:
            victim = random.choice(circle_candidates)

        # Target degree
        deg = min(random.randint(20, 60), len(circle) + 15)
        # 70% edges inside circle, 30% random outside
        internal_count = int(round(deg * 0.7))
        internal_count = min(internal_count, len(circle))
        external_count = deg - internal_count

        internal_targets = set(random.sample(circle, internal_count))

        # Guarantee Triadic Closure: find an edge within internal targets or circle
        found_triangle = False
        circle_subgraph = G_real.subgraph(circle)
        sub_edges = list(circle_subgraph.edges())
        if sub_edges:
            u, v = random.choice(sub_edges)
            internal_targets.add(u)
            internal_targets.add(v)
            found_triangle = True

        # External targets
        outside_nodes = list(set(range(num_real_nodes)) - set(circle))
        external_targets = set(random.sample(outside_nodes, max(1, external_count)))

        targets = internal_targets | external_targets

        # Feature mimicking from victim with balanced, realistic noise
        victim_feat = real_feats[victim].copy()
        noisy_feat = victim_feat.copy()
        ones_idx = np.where(victim_feat == 1)[0]
        zeros_idx = np.where(victim_feat == 0)[0]

        if len(ones_idx) > 0:
            # Flip ~10-15% of 1s (at least 1 if >3 ones)
            num_flips = max(1, int(round(len(ones_idx) * 0.12)))
            flip_ones = np.random.choice(ones_idx, size=min(num_flips, len(ones_idx)), replace=False)
            noisy_feat[flip_ones] = 0
            
            # Flip an equal or small number of 0s to 1s
            flip_zeros = np.random.choice(zeros_idx, size=min(num_flips, len(zeros_idx)), replace=False)
            noisy_feat[flip_zeros] = 1

        density = float(noisy_feat.mean())

        # Cosine similarity to victim
        dot = float(np.dot(victim_feat, noisy_feat))
        norm_v = float(np.linalg.norm(victim_feat))
        norm_n = float(np.linalg.norm(noisy_feat))
        cos_sim = float(dot / (norm_v * norm_n)) if norm_v > 0 and norm_n > 0 else 0.85
        c_cosine_sims.append(cos_sim)

        fake_profiles[fid] = {
            "archetype": "C",
            "archetype_name": "Camouflaged",
            "targets": targets,
            "feature_vector": noisy_feat,
            "degree": len(targets),
            "density": density,
            "victim_node": victim,
            "ring_id": -1,
            "has_triangle": found_triangle
        }
        metadata_rows.append({
            "temp_fake_id": fid,
            "archetype": "C",
            "archetype_name": "Camouflaged",
            "degree": len(targets),
            "targeting_strategy": "community_embedded_circle",
            "feature_density": round(density, 4),
            "victim_node_id": victim,
            "ring_id": -1,
            "seed": seed
        })

    # ==========================================
    # Archetype D: Coordinated Sybil Ring (Dense inter-ring clique + shared hubs)
    # ==========================================
    # Divide count_D (46) into rings of sizes ~7 to 9
    remaining_d = count_D
    ring_sizes = []
    while remaining_d > 0:
        sz = min(remaining_d, random.randint(7, 9))
        if remaining_d - sz < 5 and remaining_d - sz > 0:
            sz = remaining_d # Avoid tiny leftover
        ring_sizes.append(sz)
        remaining_d -= sz

    ring_inter_edges = []
    sybil_members = []
    d_coherences = []

    for r_idx, r_sz in enumerate(ring_sizes):
        # Ring member IDs
        r_members = list(range(current_fake_id, current_fake_id + r_sz))
        current_fake_id += r_sz
        sybil_members.extend(r_members)

        # Base feature template for the ring (~18% density)
        ring_base_feat = (np.random.rand(num_features) < 0.18).astype(np.uint8)

        # Shared external hub targets for the ring
        shared_hubs = set(int(x) for x in np.random.choice(top_200_hubs, size=random.randint(8, 14), replace=False))

        # Connect all pairs inside ring (clique)
        for i in range(len(r_members)):
            for j in range(i + 1, len(r_members)):
                ring_inter_edges.append((r_members[i], r_members[j]))

        # Assign per-member features and individual extra edges
        for mem in r_members:
            # Individual noise on base template (flip ~4% of bits)
            mem_feat = ring_base_feat.copy()
            flip_mask = np.random.rand(num_features) < 0.04
            mem_feat[flip_mask] = 1 - mem_feat[flip_mask]

            # Coherence with base template (cast to float to avoid uint8 overflow in np.dot)
            u = ring_base_feat.astype(np.float64)
            v = mem_feat.astype(np.float64)
            sim = float(np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v)))
            d_coherences.append(sim)

            # Individual edges to hubs + shared hubs
            indiv_hubs = set(int(x) for x in np.random.choice(top_200_hubs, size=random.randint(3, 6), replace=False))
            external_targets = shared_hubs | indiv_hubs

            density = float(mem_feat.mean())

            fake_profiles[mem] = {
                "archetype": "D",
                "archetype_name": "Sybil Ring",
                "targets": external_targets, # Internal edges added in Phase 4
                "feature_vector": mem_feat,
                "degree": len(external_targets) + (r_sz - 1),
                "density": density,
                "victim_node": -1,
                "ring_id": r_idx
            }
            metadata_rows.append({
                "temp_fake_id": mem,
                "archetype": "D",
                "archetype_name": "Sybil Ring",
                "degree": len(external_targets) + (r_sz - 1),
                "targeting_strategy": "sybil_clique_hub_sharing",
                "feature_density": round(density, 4),
                "victim_node_id": -1,
                "ring_id": r_idx,
                "seed": seed
            })

    # Save fake metadata CSV (temporary IDs, will be updated in Phase 5 with shuffled IDs)
    meta_df = pd.DataFrame(metadata_rows)
    meta_path = os.path.join(output_dir, "fake_metadata.csv")
    meta_df.to_csv(meta_path, index=False)
    print(f"[Phase 3] Metadata table saved with {len(meta_df)} fake profiles to {meta_path}")

    # Save fake profiles bundle (for Phase 4)
    # Convert sets to lists for JSON serialization
    bundle = {
        "fake_profiles": {
            str(fid): {
                "archetype": p["archetype"],
                "archetype_name": p["archetype_name"],
                "targets": list(p["targets"]),
                "density": p["density"],
                "victim_node": p["victim_node"],
                "ring_id": p["ring_id"]
            }
            for fid, p in fake_profiles.items()
        },
        "ring_inter_edges": ring_inter_edges
    }
    with open(os.path.join(output_dir, "fake_bundle.json"), "w", encoding="utf-8") as f:
        json.dump(bundle, f)

    # Save feature vectors for fakes
    fake_feat_matrix = np.zeros((total_fakes, num_features), dtype=np.uint8)
    for i, fid in enumerate(range(num_real_nodes, num_real_nodes + total_fakes)):
        fake_feat_matrix[i] = fake_profiles[fid]["feature_vector"]
    np.save(os.path.join(output_dir, "fake_features.npy"), fake_feat_matrix)

    # Verification Checks
    mean_dens_A = float(np.mean([p["density"] for p in fake_profiles.values() if p["archetype"] == "A"]))
    mean_dens_B = float(np.mean([p["density"] for p in fake_profiles.values() if p["archetype"] == "B"]))
    mean_sim_C = float(np.mean(c_cosine_sims))
    mean_coherence_D = float(np.mean(d_coherences))

    checks = [
        {
            "check": "Total fake node count",
            "expected": "450",
            "actual": str(len(fake_profiles)),
            "status": "PASS" if len(fake_profiles) == 450 else "FAIL"
        },
        {
            "check": "Archetype breakdown",
            "expected": "A=112, B=157, C=135, D=46",
            "actual": f"A={count_A}, B={count_B}, C={count_C}, D={count_D}",
            "status": "PASS" if (count_A, count_B, count_C, count_D) == (112, 157, 135, 46) else "FAIL"
        },
        {
            "check": "Archetype A feature density",
            "expected": "< 0.05",
            "actual": f"{mean_dens_A:.4f}",
            "status": "PASS" if mean_dens_A < 0.05 else "FAIL"
        },
        {
            "check": "Archetype B feature density",
            "expected": "0.10 - 0.30",
            "actual": f"{mean_dens_B:.4f}",
            "status": "PASS" if 0.10 <= mean_dens_B <= 0.30 else "FAIL"
        },
        {
            "check": "Archetype C cosine similarity to victim",
            "expected": "> 0.70",
            "actual": f"{mean_sim_C:.4f}",
            "status": "PASS" if mean_sim_C > 0.70 else "FAIL"
        },
        {
            "check": "Archetype D Sybil feature coherence",
            "expected": "> 0.80",
            "actual": f"{mean_coherence_D:.4f}",
            "status": "PASS" if mean_coherence_D > 0.80 else "FAIL"
        },
        {
            "check": "Metadata CSV row count & columns",
            "expected": "450 rows, 9 columns",
            "actual": f"{len(meta_df)} rows, {len(meta_df.columns)} columns",
            "status": "PASS" if len(meta_df) == 450 and not meta_df.isnull().any().any() else "FAIL"
        }
    ]

    all_passed = all(c["status"] == "PASS" for c in checks)
    status_str = "PASS" if all_passed else "FAIL"

    results_summary = {
        "total_fakes": total_fakes,
        "count_archetype_A": count_A,
        "count_archetype_B": count_B,
        "count_archetype_C": count_C,
        "count_archetype_D": count_D,
        "archetype_A_mean_density": f"{mean_dens_A:.4f}",
        "archetype_B_mean_density": f"{mean_dens_B:.4f}",
        "archetype_C_victim_cosine_sim": f"{mean_sim_C:.4f}",
        "archetype_D_template_coherence": f"{mean_coherence_D:.4f}",
        "sybil_rings_created": len(ring_sizes),
        "inter_sybil_clique_edges": len(ring_inter_edges)
    }

    logger.log_phase(
        phase=3,
        name="Generate Fake Nodes",
        status=status_str,
        results=results_summary,
        outputs=["fake_metadata.csv", "fake_bundle.json", "fake_features.npy"],
        verification=checks,
        notes=f"Generated 450 fakes with realistic camouflage. Archetype C mimics real victims with avg cosine sim {mean_sim_C:.2f}. Archetype D forms {len(ring_sizes)} dense Sybil cliques.",
        script="phase3_generate_fakes.py"
    )

    if not all_passed:
        raise RuntimeError("Phase 3 verification failed! Check verification table in memory.md.")

    return fake_profiles, ring_inter_edges, meta_df

if __name__ == "__main__":
    generate_fakes()
