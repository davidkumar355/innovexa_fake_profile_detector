"""
Export Model Artifacts for Innovexa Backend
Extracts trained baseline models, scalers, graph structure, node metadata,
and community detection clusters from the synthetic injection dataset.
"""

import json
import os
import networkx as nx
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib

try:
    import community as community_louvain
    LOUVAIN_AVAILABLE = True
except ImportError:
    LOUVAIN_AVAILABLE = False

RANDOM_SEED = 42
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "Dataset", "generated", "v1"))
ARTIFACTS_DIR = os.path.join(BASE_DIR, "artifacts")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

print(f"[Phase B0 Export] Dataset dir: {DATASET_DIR}")
print(f"[Phase B0 Export] Artifacts dir: {ARTIFACTS_DIR}")

# 1. Load data
print("1. Loading raw dataset artifacts...")
X_profile = np.load(os.path.join(DATASET_DIR, "final_features.npy"))
y = np.load(os.path.join(DATASET_DIR, "final_labels.npy"))
metadata_df = pd.read_csv(os.path.join(DATASET_DIR, "fake_metadata.csv"))

with open(os.path.join(DATASET_DIR, "global_featnames.txt"), "r", encoding="utf-8") as f:
    featnames = [line.strip() for line in f if line.strip()]

G = nx.Graph()
G.add_nodes_from(range(len(y)))
with open(os.path.join(DATASET_DIR, "final_edge_list.txt"), "r", encoding="utf-8") as f:
    for line in f:
        parts = line.strip().split()
        if len(parts) >= 2:
            G.add_edge(int(parts[0]), int(parts[1]))

n_nodes = G.number_of_nodes()
n_edges = G.number_of_edges()
print(f"   Loaded graph: {n_nodes} nodes, {n_edges} edges, feature dim: {X_profile.shape[1]}")

# 2. Compute structural features
print("2. Computing structural graph features (degree, clustering, betweenness, closeness, community)...")
degree_arr = np.array([G.degree(i) for i in range(n_nodes)], dtype=np.float32)

clust = nx.clustering(G)
clust_arr = np.array([clust.get(i, 0.0) for i in range(n_nodes)], dtype=np.float32)

btwn = nx.betweenness_centrality(G, k=100, seed=RANDOM_SEED)
btwn_arr = np.array([btwn.get(i, 0.0) for i in range(n_nodes)], dtype=np.float32)

close = nx.closeness_centrality(G)
close_arr = np.array([close.get(i, 0.0) for i in range(n_nodes)], dtype=np.float32)

if LOUVAIN_AVAILABLE:
    partition = community_louvain.best_partition(G, random_state=RANDOM_SEED)
    comm_arr = np.array([partition.get(i, 0) for i in range(n_nodes)], dtype=np.float32)
else:
    partition = {i: 0 for i in range(n_nodes)}
    comm_arr = np.zeros(n_nodes, dtype=np.float32)

struct_feats = np.stack([degree_arr, clust_arr, btwn_arr, close_arr, comm_arr], axis=1)
X_full = np.hstack([X_profile.astype(np.float32), struct_feats])
print(f"   X_full shape: {X_full.shape}")

# 3. Train / Val / Test Splits
print("3. Generating stratified train / val / test splits (70/15/15)...")
indices = np.arange(n_nodes)
train_idx, temp_idx = train_test_split(indices, test_size=0.30, stratify=y, random_state=RANDOM_SEED)
val_idx, test_idx = train_test_split(temp_idx, test_size=0.50, stratify=y[temp_idx], random_state=RANDOM_SEED)

scaler = StandardScaler()
X_full_scaled = X_full.copy()
X_full_scaled[train_idx, 1406:] = scaler.fit_transform(X_full[train_idx, 1406:])
X_full_scaled[val_idx, 1406:] = scaler.transform(X_full[val_idx, 1406:])
X_full_scaled[test_idx, 1406:] = scaler.transform(X_full[test_idx, 1406:])

# 4. Train Models
print("4. Training Random Forest & Logistic Regression...")
X_tr, y_tr = X_full_scaled[train_idx], y[train_idx]
X_val, y_val = X_full_scaled[val_idx], y[val_idx]
X_te, y_te = X_full_scaled[test_idx], y[test_idx]

rf = RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=RANDOM_SEED, n_jobs=-1)
rf.fit(X_tr, y_tr)

lr = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=RANDOM_SEED, n_jobs=-1)
lr.fit(X_tr, y_tr)

# Threshold tuning on validation set
def tune_threshold(clf, X_v, y_v):
    proba = clf.predict_proba(X_v)[:, 1]
    best_t, best_f1 = 0.5, 0.0
    for t in np.arange(0.3, 0.8, 0.05):
        f = f1_score(y_v, (proba >= t).astype(int), zero_division=0)
        if f > best_f1:
            best_f1, best_t = f, float(t)
    return round(best_t, 2)

rf_thresh = tune_threshold(rf, X_val, y_val)
lr_thresh = tune_threshold(lr, X_val, y_val)

rf_val_proba = rf.predict_proba(X_val)[:, 1]
rf_te_proba = rf.predict_proba(X_te)[:, 1]
rf_te_pred = (rf_te_proba >= rf_thresh).astype(int)

lr_te_proba = lr.predict_proba(X_te)[:, 1]
lr_te_pred = (lr_te_proba >= lr_thresh).astype(int)

# Overall predictions on all nodes for quick cache
rf_all_proba = rf.predict_proba(X_full_scaled)[:, 1]
rf_all_pred = (rf_all_proba >= rf_thresh).astype(int)

metrics = {
    "random_forest": {
        "threshold": rf_thresh,
        "accuracy": float(accuracy_score(y_te, rf_te_pred)),
        "precision": float(precision_score(y_te, rf_te_pred, zero_division=0)),
        "recall": float(recall_score(y_te, rf_te_pred, zero_division=0)),
        "f1": float(f1_score(y_te, rf_te_pred, zero_division=0)),
        "auc": float(roc_auc_score(y_te, rf_te_proba)),
    },
    "logistic_regression": {
        "threshold": lr_thresh,
        "accuracy": float(accuracy_score(y_te, lr_te_pred)),
        "precision": float(precision_score(y_te, lr_te_pred, zero_division=0)),
        "recall": float(recall_score(y_te, lr_te_pred, zero_division=0)),
        "f1": float(f1_score(y_te, lr_te_pred, zero_division=0)),
        "auc": float(roc_auc_score(y_te, lr_te_proba)),
    }
}
print(f"   RF test metrics: F1={metrics['random_forest']['f1']:.4f}, Prec={metrics['random_forest']['precision']:.4f}, Rec={metrics['random_forest']['recall']:.4f}")

# Archetype mapping
archetype_map = {}
if "shuffled_fake_id" in metadata_df.columns and "archetype" in metadata_df.columns:
    for _, row in metadata_df.iterrows():
        archetype_map[int(row["shuffled_fake_id"])] = str(row["archetype"])

# 5. Build node metadata
print("5. Constructing node metadata table...")
split_map = {}
for i in train_idx:
    split_map[int(i)] = "train"
for i in val_idx:
    split_map[int(i)] = "val"
for i in test_idx:
    split_map[int(i)] = "test"

node_metadata = {}
for i in range(n_nodes):
    is_fake = bool(y[i] == 1)
    arch = archetype_map.get(i, None)
    node_metadata[str(i)] = {
        "node_id": i,
        "is_fake": is_fake,
        "true_label": int(y[i]),
        "archetype": arch,
        "split": split_map.get(i, "unknown"),
        "degree": int(degree_arr[i]),
        "clustering_coefficient": float(round(clust_arr[i], 4)),
        "betweenness_centrality": float(round(btwn_arr[i], 6)),
        "closeness_centrality": float(round(close_arr[i], 6)),
        "community_id": int(comm_arr[i]),
        "risk_score": float(round(rf_all_proba[i], 4)),
        "prediction": int(rf_all_pred[i]),
        "prediction_label": "Fake" if rf_all_pred[i] == 1 else "Genuine",
    }

# 6. Build Community Clusters Summary
print("6. Summarizing graph communities (clusters)...")
comm_to_nodes = {}
for i in range(n_nodes):
    c_id = int(comm_arr[i])
    comm_to_nodes.setdefault(c_id, []).append(i)

clusters = []
for c_id, members in comm_to_nodes.items():
    members_fake = [m for m in members if y[m] == 1]
    fake_cnt = len(members_fake)
    total_cnt = len(members)
    fake_ratio = fake_cnt / total_cnt if total_cnt > 0 else 0.0
    mean_risk = float(np.mean([rf_all_proba[m] for m in members]))
    
    # Archetype breakdown in cluster
    arch_dist = {}
    for m in members_fake:
        a = archetype_map.get(m, "Unknown")
        arch_dist[a] = arch_dist.get(a, 0) + 1

    risk_level = "High" if fake_ratio > 0.35 or mean_risk > 0.4 else ("Medium" if fake_ratio > 0.15 else "Low")
    clusters.append({
        "cluster_id": c_id,
        "size": total_cnt,
        "fake_count": fake_cnt,
        "genuine_count": total_cnt - fake_cnt,
        "fake_ratio": round(fake_ratio, 4),
        "mean_risk_score": round(mean_risk, 4),
        "risk_level": risk_level,
        "archetype_distribution": arch_dist,
        "sample_nodes": members[:20],  # sample nodes for preview
        "all_nodes": members
    })

clusters.sort(key=lambda c: (c["fake_ratio"], c["fake_count"]), reverse=True)

# 7. Precompute Dashboard Summary
print("7. Precomputing dashboard statistics...")
test_meta = [node_metadata[str(i)] for i in test_idx]
total_test = len(test_meta)
fake_test_count = sum(1 for m in test_meta if m["is_fake"])
genuine_test_count = total_test - fake_test_count
high_risk_count = sum(1 for m in test_meta if m["risk_score"] >= 0.70)

# Detections by archetype in test set
test_archetype_counts = {"A": 0, "B": 0, "C": 0, "D": 0}
for m in test_meta:
    if m["archetype"] in test_archetype_counts:
        test_archetype_counts[m["archetype"]] += 1

# Mock timeline of detections over time (e.g. simulated 7-day batches)
np.random.seed(RANDOM_SEED)
days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
detections_over_time = []
chunk_size = len(test_meta) // 7
for idx, day in enumerate(days):
    chunk = test_meta[idx * chunk_size : (idx + 1) * chunk_size] if idx < 6 else test_meta[idx * chunk_size :]
    d_fake = sum(1 for m in chunk if m["prediction"] == 1)
    d_gen = sum(1 for m in chunk if m["prediction"] == 0)
    detections_over_time.append({
        "day": day,
        "fake_detected": d_fake,
        "genuine_detected": d_gen,
        "total_analyzed": len(chunk)
    })

dashboard_summary = {
    "total_profiles_analyzed": total_test,
    "fake_detected": sum(1 for m in test_meta if m["prediction"] == 1),
    "genuine_detected": sum(1 for m in test_meta if m["prediction"] == 0),
    "high_risk_pending_review": high_risk_count,
    "true_fake_count": fake_test_count,
    "true_genuine_count": genuine_test_count,
    "model_accuracy": metrics["random_forest"]["accuracy"],
    "model_f1_score": metrics["random_forest"]["f1"],
    "model_precision": metrics["random_forest"]["precision"],
    "model_recall": metrics["random_forest"]["recall"],
    "model_auc": metrics["random_forest"]["auc"],
    "threshold": rf_thresh,
    "archetype_distribution": test_archetype_counts,
    "detections_over_time": detections_over_time,
}

# 8. Feature Categories for UI Feature Toggles
print("8. Categorizing 1406 profile features...")
category_map = {}
for idx, feat in enumerate(featnames):
    if ";" in feat:
        cat, name = feat.split(";", 1)
    else:
        cat, name = "other", feat
    cat = cat.strip().lower()
    category_map.setdefault(cat, []).append({
        "feature_index": idx,
        "feature_name": name.strip(),
        "raw_string": feat
    })

print(f"   Found {len(category_map)} distinct feature categories: {list(category_map.keys())[:8]}")

# 9. Graph Adjacency representation
print("9. Exporting graph adjacency list...")
adjacency = {}
for i in range(n_nodes):
    adjacency[i] = list(G.neighbors(i))

# 10. Save all artifacts
print("10. Writing artifacts to disk...")
joblib.dump(rf, os.path.join(ARTIFACTS_DIR, "random_forest.joblib"))
joblib.dump(lr, os.path.join(ARTIFACTS_DIR, "logistic_regression.joblib"))
joblib.dump(scaler, os.path.join(ARTIFACTS_DIR, "scaler.joblib"))

np.save(os.path.join(ARTIFACTS_DIR, "features_full.npy"), X_full)
np.save(os.path.join(ARTIFACTS_DIR, "features_scaled.npy"), X_full_scaled)
np.save(os.path.join(ARTIFACTS_DIR, "labels.npy"), y)

with open(os.path.join(ARTIFACTS_DIR, "thresholds.json"), "w", encoding="utf-8") as f:
    json.dump({"random_forest": rf_thresh, "logistic_regression": lr_thresh}, f, indent=2)

with open(os.path.join(ARTIFACTS_DIR, "model_metrics.json"), "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2)

with open(os.path.join(ARTIFACTS_DIR, "splits.json"), "w", encoding="utf-8") as f:
    json.dump({
        "train_idx": train_idx.tolist(),
        "val_idx": val_idx.tolist(),
        "test_idx": test_idx.tolist()
    }, f, indent=2)

with open(os.path.join(ARTIFACTS_DIR, "node_metadata.json"), "w", encoding="utf-8") as f:
    json.dump(node_metadata, f, indent=2)

with open(os.path.join(ARTIFACTS_DIR, "community_clusters.json"), "w", encoding="utf-8") as f:
    json.dump(clusters, f, indent=2)

with open(os.path.join(ARTIFACTS_DIR, "dashboard_summary.json"), "w", encoding="utf-8") as f:
    json.dump(dashboard_summary, f, indent=2)

with open(os.path.join(ARTIFACTS_DIR, "feature_categories.json"), "w", encoding="utf-8") as f:
    json.dump(category_map, f, indent=2)

with open(os.path.join(ARTIFACTS_DIR, "graph_adjacency.json"), "w", encoding="utf-8") as f:
    json.dump(adjacency, f)

print("Export completed successfully! All artifacts generated in:", ARTIFACTS_DIR)
