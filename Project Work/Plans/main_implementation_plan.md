Here's the full implementation plan, phased, with a verification checkpoint built into each phase so you don't move forward on a broken assumption. Fake data injection is intentionally left out — that slots in as its own phase between Phase 3 and Phase 5 later, using the plan from the previous message.

---

## Phase 0 — Environment & Project Setup

**Objective:** Reproducible environment before any data touches code.

**Steps:**
- Set up project structure: `/data/raw`, `/data/processed`, `/notebooks`, `/src` (empty for now — notebooks first)
- Pin library versions: `torch`, `torch_geometric`, `networkx`, `scikit-learn`, `pandas`, `numpy` — write a `requirements.txt` immediately, not at the end
- Fix global random seed (one constant, used everywhere — numpy, torch, sklearn splits)
- Set up `.gitignore` for raw data files (keep repo light)

**Verification checkpoint:**
- Re-run environment setup on a clean cell restart → confirm no import errors, confirm seed reproducibility (run same random op twice, get identical output)

---

## Phase 1 — Data Ingestion

**Objective:** Load all three raw sources without transformation yet.

**Steps:**
- Load `facebook_combined.txt` → edge list (4,039 nodes, 88,234 edges, already confirmed)
- Load all 10 ego-network `.edges`, `.feat`, `.featnames`, `.circles`, `.egofeat` files from the extracted tar
- Keep these as raw/untouched DataFrames or dicts — no merging yet

**Verification checkpoint:**
- Assert node count from `facebook_combined.txt` == 4,039
- Assert edge count == 88,234
- Assert all 10 ego IDs (0, 107, 348, 414, 686, 698, 1684, 1912, 3437, 3980) have exactly 5 corresponding files each
- Print row/column shape for every loaded file — catch truncated reads early

---

## Phase 2 — Feature Schema Unification

**Objective:** Resolve the problem flagged earlier — each ego network has its own feature-column set, not a shared schema.

**Steps:**
- Parse all 10 `.featnames` files, extract the feature-description strings
- Build one master ordered list of unique feature names (union across all 10 ego networks)
- Build a mapping: `{ego_id: {local_feature_index: master_feature_index}}`
- Remap every real node's existing feature vector into the master schema (0-fill where absent)

**Verification checkpoint:**
- Assert master feature list length ≥ the largest individual ego's feature count (sanity floor)
- Spot-check 3 random nodes: manually trace their original feature vector → remapped vector, confirm no 1s got dropped or misaligned
- Check for exact duplicate feature-name strings across ego networks that *should* merge to the same master column (e.g. "education;school;id" appearing in two egos) — confirm they're merged, not duplicated as separate columns

---

## Phase 3 — Real Graph Construction

**Objective:** Produce one unified graph object: genuine nodes only, full feature matrix, no labels needed yet (all genuine).

**Steps:**
- Merge `facebook_combined.txt` edges with any additional ego-specific edges not already covered (check for non-overlap)
- Build master node list (4,039 nodes) aligned row-index to the Phase 2 feature matrix
- Construct adjacency structure (NetworkX graph object — human-readable, easy to inspect, before converting to tensor format later)
- Assign `label = genuine` to all nodes at this stage (placeholder column)

**Verification checkpoint:**
- Assert node count in graph == row count in feature matrix (no misalignment)
- Check graph connectivity: is it one connected component, or several? (matters for later GNN message passing — isolated components behave differently)
- Compute and sanity-check basic stats: average degree, max degree, density — compare against known published stats for this dataset (avg degree ~43-44) to confirm nothing broke during merge

*(Fake data injection phase goes here — deliberately excluded per your request.)*

---

## Phase 4 — Data Preprocessing

**Objective:** Clean, validate, and prep post-injection data (will apply to real+fake combined graph once that's ready, but write it now against real data so it's ready to run immediately after injection).

**Steps:**
- Schema validation: check for duplicate node IDs, self-loop edges, orphaned edges (pointing to nonexistent nodes)
- Missing value handling for feature matrix (expected to be sparse/binary here, so "missing" mostly won't apply, but validate dtype consistency)
- Class distribution check (post-injection: confirm your 8-15% fake ratio target actually landed where intended)
- Confirm **no leakage pathway exists yet** — this is just prep, actual train/val/test separation happens in Phase 7, but validate here that no label-derived field accidentally got mixed into the feature matrix

**Verification checkpoint:**
- Zero self-loops, zero dangling edge references (hard assert, not just a log print)
- Feature matrix dtype check — all binary/numeric, no stray strings or NaNs
- Print class balance table — confirm actual vs. intended ratio

---

## Phase 5 — Feature Engineering (Structural)

**Objective:** Compute graph-derived features the paper calls for — this is separate from the raw profile features already in the matrix.

**Steps:**
- Compute per-node: degree, clustering coefficient, betweenness/closeness centrality (sample-based if full computation is too slow at this node count), community membership (Louvain or similar)
- Concatenate structural features onto the existing profile feature matrix → final node-feature matrix
- Scale continuous structural features using **training-set-only** statistics (fit scaler after split in Phase 7, not before — avoid leakage here)

**Verification checkpoint:**
- Assert structural feature computation covers 100% of nodes (no silent drops from centrality algorithms that fail on disconnected components)
- Distribution check: plot degree histogram — confirm genuine vs. fake nodes show the expected separation pattern from your injection design (sanity check that injection actually produced learnable signal, not noise)

---

## Phase 6 — Train / Validation / Test Split

**Objective:** Leakage-safe split, exactly as the paper insists on.

**Steps:**
- Stratified split by label (genuine/fake) to preserve class ratio across all three sets
- No timestamp available (flagged earlier) → random stratified split, not chronological
- Fit any scalers/encoders on **training set only**, then transform val/test using those fitted parameters

**Verification checkpoint:**
- Assert no node ID appears in more than one split
- Assert class ratio in train/val/test are all within a small tolerance of each other (e.g., ±1-2%)
- Explicit re-check: confirm scaler was fit on train only (print the fit-source shape and compare to train set size, not full dataset size)

---

## Phase 7 — Baseline Models (Non-Graph)

**Objective:** Logistic Regression → SVM → Random Forest → MLP, on profile+structural features only, no graph structure used.

**Steps:**
- Train each model on the same train/val/test split
- Tune minimal hyperparameters on validation set only
- Record Accuracy, Precision, Recall, F1, AUC for each

**Verification checkpoint:**
- Confirm test set was touched exactly once per model (no repeated test-set peeking during tuning)
- Sanity floor: none of these should hit near-perfect scores — if one does, it signals either label leakage or your fake nodes are too easy (ties back to the Phase 6 trivial-baseline check from the injection plan)

---

## Phase 8 — Graph Object Construction (PyTorch Geometric)

**Objective:** Convert the NetworkX/pandas representation into a `torch_geometric.data.Data` object — node feature tensor, edge index tensor, label tensor.

**Steps:**
- Build `edge_index` (2×E tensor), `x` (node feature tensor), `y` (label tensor)
- Attach train/val/test masks as boolean tensors (same split from Phase 6, not recomputed)

**Verification checkpoint:**
- Assert `edge_index.max() < x.shape[0]` (no edge references a nonexistent node index)
- Assert `x.shape[0] == y.shape[0]` and mask lengths all match node count
- Load the Data object into a dummy single-layer GNN forward pass just to confirm shapes flow correctly before building the real model

---

## Phase 9 — GNN Model Development

**Objective:** GCN → GraphSAGE → GAT, in that order, matching the paper's isolation-of-improvement-source logic.

**Steps:**
- Implement each architecture with a configurable number of layers (2-3 to start — deeper risks oversmoothing on a graph this size)
- Binary cross-entropy loss, same train/val/test masks as baselines

**Verification checkpoint:**
- Confirm loss decreases over epochs on training mask (basic sanity — if it doesn't, something's wrong before you even get to evaluation)
- Confirm validation metric is computed strictly on val mask, never touching test mask during training loop

---

## Phase 10 — Training & Hyperparameter Tuning

**Objective:** Proper tuning loop, early stopping, test set held out until the very end.

**Steps:**
- Grid or random search over learning rate, hidden dim, number of layers, dropout — validation set only
- Early stopping on validation loss/F1
- Lock final model only after tuning is done

**Verification checkpoint:**
- Explicit assertion/log: "test set accessed: 0 times" tracked through the tuning loop, only flips to 1 at final evaluation
- Confirm the selected hyperparameters are logged with the run (so results are reproducible)

---

## Phase 11 — Final Evaluation & Model Comparison

**Objective:** The actual comparison table — baselines vs. GNNs, same metrics, same split.

**Steps:**
- Run final trained GNN(s) on test set, exactly once
- Compile Table III-style comparison: all models × all 5 metrics
- Compute the specific claim the paper cares about: delta between best non-graph baseline and best GNN

**Verification checkpoint:**
- Confirm every model in the table was evaluated on the identical test set (same node indices)
- Sanity-check result direction: GNN should outperform baselines on the camouflaged-fake subset specifically (break out metrics by archetype, using the metadata table from injection) — if it doesn't, that's a real finding to report honestly, not a bug to hide

---

## Phase 12 — Adversarial Robustness Testing

**Objective:** Feature masking + edge injection, measured against the already-trained final model (no retraining).

**Steps:**
- Feature masking: zero out a controlled % of each test node's attributes, re-evaluate
- Edge injection: add random/strategic edges to test nodes, re-evaluate
- Record metric degradation curve (performance vs. perturbation strength)

**Verification checkpoint:**
- Confirm perturbations are applied only to a copy of the test set, original untouched (so you can compare before/after on the same baseline)
- Confirm perturbation strength is logged per run — this becomes your robustness result table

---

## Phase 13 — Suspicious Network Analysis

**Objective:** Post-hoc community detection on predicted high-risk nodes.

**Steps:**
- Filter nodes above a chosen risk threshold
- Run community detection (Louvain) restricted to this high-risk subgraph
- Flag clusters, not individual verdicts — matches the paper's explicit framing ("candidate suspicious subgraph, not automatic declaration")

**Verification checkpoint:**
- Cross-check detected clusters against your known Sybil-ring archetype from injection (if you included one) — confirm the method actually recovers the planted coordinated group, not just noise

---

## Phase 14 — Results Compilation & Reporting

**Objective:** Package everything into the paper's expected output structure.

**Steps:**
- Final comparison table, robustness table, suspicious-cluster summary
- Document every design decision (injection ratios, split strategy, hyperparameters) in one reproducibility log

**Verification checkpoint:**
- Full pipeline re-run from a clean notebook restart, confirm identical results given the fixed seed — this is your final reproducibility gate before calling the project done

---

## Code workflow, as you specified

All of the above gets built as a **Jupyter notebook first**, phase by phase — I'll write each phase as its own set of notebook cells so you can run, inspect output, and approve incrementally rather than getting one giant unreviewable block. Once you've approved the full notebook end-to-end, I'll convert it into a structured `.py` module layout (`src/data.py`, `src/features.py`, `src/models.py`, etc.) for the production/portfolio version.
