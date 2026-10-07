# OBJECTIVE:

Parameters to control, grouped by what they govern
A. Structural parameters (how fake nodes connect)
Degree — not a single fixed number. Real users range wildly (your combined graph has degree variance already). A fake node with degree 500 when the graph average is ~44 is trivially flaggable by degree alone. Vary this per archetype.
Targeting strategy — this is the single most important knob:
Random targeting (easy): edges go to randomly chosen nodes across the whole graph — low clustering, spans unrelated communities, structurally obvious
Preferential targeting (medium): edges go disproportionately to high-degree "hub" nodes — mimics real botnet behavior (bots follow popular accounts to look legitimate) and is harder to catch with simple degree-based rules
Community-embedded targeting (hard): edges concentrated within one existing friend circle (.circles data gives you real community structure to embed into) — this is the "relation camouflage" the paper explicitly calls out
Clustering coefficient — fakes with zero triangles (no mutual friends) are easy to flag; realistic camouflage means some triadic closure, i.e., connecting to two people who are already friends with each other
Reciprocity / mutual-connection density — in undirected friend graphs this is less relevant, but if you later add directed interactions (likes/mentions), one-way-only edges from fakes are a tell you can choose to include or suppress
B. Attribute/feature parameters (what the fake node's profile looks like)
Feature density — empty/near-zero feature vector (low-effort fake, trivially easy) vs. populated vector (requires actually deciding what to populate)
Feature similarity to a "victim" node — true feature mimicking means copying a real user's attribute pattern closely, not generating random bits. A random 224-dim binary vector will statistically look nothing like real sparse, correlated attribute patterns and becomes an easy tell on its own
Internal feature coherence — real profiles have correlated attributes (someone with "education;concentration" features usually also has "education;classes" features). Randomly flipping bits independent of real co-occurrence patterns creates attribute combinations that look statistically unnatural even without being flagged as "fake" per se — another unintended easy tell you want to avoid or deliberately include as a difficulty lever
C. Temporal parameters

Important limitation to flag honestly: this dataset has no real timestamps at all — not in facebook_combined.txt, not in the ego files. So any "burst creation" timing signal has to be entirely synthetic, not derived from real data. You have two honest choices: (1) skip the temporal dimension entirely and stick to structural+feature signals, which is simpler and defensible, or (2) synthesize a plausible timeline (e.g., assign fake nodes a compressed "creation window," assign genuine nodes a spread-out one) and document clearly that this is a fully synthetic signal layered on, not derived from real behavior. I'd lean toward (1) for your first version — keep the synthetic part to what you can control precisely (structure + features), add temporal fakery later only if you want a harder challenge.

D. Label/class design parameters — this is where leakage happens
Class imbalance ratio — real-world fake populations are a minority. Something like 8-15% fake is realistic and also directly lets you exercise the paper's "class imbalance handling" stage instead of skipping it. Don't do 50/50 — that's unrealistic and sidesteps a problem the paper explicitly says to solve.
Archetype mix (difficulty spectrum) — don't generate one type of fake. Use a blend, roughly:
~25% "obvious bot" (random targeting, sparse features) — sanity-check easy cases
~35% "preferential/hub-targeting" (medium difficulty)
~30% "camouflaged / community-embedded + feature-mimicking" (hard cases — this is your real test of the GNN's value over baselines)
~10% "coordinated Sybil ring" (several fake nodes densely connected to each other plus shared edges into real hubs — tests the suspicious-network-analysis stage specifically)
No ID/index leakage — if you just append fake nodes as IDs 4039-4600, any model (or even you, accidentally) could learn "node ID > 4038 → fake" as a shortcut with zero relational reasoning. After generation, shuffle/relabel all node IDs so fake and genuine are interleaved with no ID pattern.
No structural leakage via isolated components — if fake nodes only connect to each other and never touch the real graph, a trivial connected-component check solves your whole task. Every fake node needs at least some edges into the genuine population (this is actually also just realistic — real fake accounts always touch real users, that's the point).
E. Reproducibility parameters (the paper cares about this explicitly)
Fixed random seed, documented
A generation metadata table — one row per fake node recording which archetype it came from and what parameters were used. You'll want this later for ablation ("how well did the model catch camouflaged fakes specifically vs. obvious ones") — that's actually a stronger result section than a single aggregate accuracy number.

# Implementation plan:

Phase 1 — Build the unified feature space.
Real complication worth flagging: your 10 ego-network .feat/.featnames files don't share one feature schema — each ego network has its own column set (overlapping in category, not necessarily identical indices). Before you can assign comparable feature vectors to anyone (real or fake), you need to union the featname strings across all 10 ego networks, build one consistent feature-column index, and remap each real node's existing feature vector into that unified space (filling 0 where a node's original ego-network schema didn't include a given column). This has to happen before fake-feature generation, since fakes need to be expressed in the same space.

Phase 2 — Load and merge the real graph.
Combine facebook_combined.txt (the full 4,039-node, 88,234-edge graph) with the unified feature matrix from Phase 1. Label every real node genuine.

Phase 3 — Generate fake nodes per archetype.
For each archetype bucket (sized per the mix above): pick target degree range → pick targeting strategy (random / preferential / community-embedded, using .circles data for the embedded case) → generate feature vector (empty / random-but-coherent / copied-from-victim-with-noise) → record archetype + parameters in the metadata table.

Phase 4 — Inject into the graph.
Add new node IDs, add their edges into the existing edge list, append their feature rows to the unified matrix, append fake labels.

Phase 5 — Shuffle node IDs.
Generate a random permutation, remap every node ID (real and fake) through it, so no ID-ordering signal survives. Re-map edges and labels consistently.

Phase 6 — Sanity/difficulty validation before you trust the dataset.
This step matters more than people think: run a trivial baseline (e.g., "flag anyone with degree > threshold" or "flag anyone with empty feature vector") and check it does not get near-perfect accuracy. If it does, your fakes are too easy — go back and push more of the mix toward camouflaged/hard archetypes. This check is what separates a dataset that actually tests the GNN's relational value from one that doesn't.

Phase 7 — Save artifacts.
Final edge list, unified feature matrix, label vector, and the per-node archetype metadata table as separate versioned files — this is your actual deliverable going into the preprocessing/feature-engineering stages of the paper's pipeline.
