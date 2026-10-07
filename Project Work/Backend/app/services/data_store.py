"""
DataStore service: High-performance in-memory access layer for nodes, graph structure,
features, and metadata.
"""

import json
import os
from typing import Dict, List, Optional, Any
import numpy as np

from app.config import settings

class DataStore:
    _instance: Optional["DataStore"] = None

    def __init__(self):
        self.artifacts_dir = settings.ARTIFACTS_DIR
        self._load_artifacts()

    @classmethod
    def get_instance(cls) -> "DataStore":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_artifacts(self):
        print(f"[DataStore] Loading artifacts from {self.artifacts_dir}...")
        
        # Load matrices
        self.features_full = np.load(os.path.join(self.artifacts_dir, "features_full.npy"))
        self.features_scaled = np.load(os.path.join(self.artifacts_dir, "features_scaled.npy"))
        self.labels = np.load(os.path.join(self.artifacts_dir, "labels.npy"))
        
        # Load JSON configs and maps
        with open(os.path.join(self.artifacts_dir, "node_metadata.json"), "r", encoding="utf-8") as f:
            self.node_metadata = json.load(f)
            
        with open(os.path.join(self.artifacts_dir, "graph_adjacency.json"), "r", encoding="utf-8") as f:
            raw_adj = json.load(f)
            # Store keys as integers for fast indexing
            self.adjacency = {int(k): v for k, v in raw_adj.items()}
            
        with open(os.path.join(self.artifacts_dir, "splits.json"), "r", encoding="utf-8") as f:
            self.splits = json.load(f)
            
        with open(os.path.join(self.artifacts_dir, "feature_categories.json"), "r", encoding="utf-8") as f:
            self.feature_categories = json.load(f)

        with open(os.path.join(self.artifacts_dir, "community_clusters.json"), "r", encoding="utf-8") as f:
            self.clusters = json.load(f)

        with open(os.path.join(self.artifacts_dir, "dashboard_summary.json"), "r", encoding="utf-8") as f:
            self.dashboard_summary = json.load(f)

        with open(os.path.join(self.artifacts_dir, "model_metrics.json"), "r", encoding="utf-8") as f:
            self.model_metrics = json.load(f)

        with open(os.path.join(self.artifacts_dir, "thresholds.json"), "r", encoding="utf-8") as f:
            self.thresholds = json.load(f)

        # Precompute inverted category index: feature_index -> (category, feature_name)
        self.feat_idx_to_cat = {}
        for cat, feats in self.feature_categories.items():
            for item in feats:
                self.feat_idx_to_cat[item["feature_index"]] = (cat, item["feature_name"])

        self.total_nodes = len(self.labels)
        print(f"[DataStore] Successfully loaded {self.total_nodes} nodes and {len(self.clusters)} clusters.")

    def get_node(self, node_id: int) -> Optional[Dict[str, Any]]:
        key = str(node_id)
        if key not in self.node_metadata:
            return None
        meta = self.node_metadata[key].copy()
        meta["neighbor_count"] = len(self.adjacency.get(node_id, []))
        return meta

    def get_node_features(self, node_id: int, scaled: bool = True) -> Optional[np.ndarray]:
        if 0 <= node_id < self.total_nodes:
            return self.features_scaled[node_id] if scaled else self.features_full[node_id]
        return None

    def get_neighbors(self, node_id: int) -> List[int]:
        return self.adjacency.get(node_id, [])

    def get_category_summary(self, node_id: int) -> Dict[str, Any]:
        """
        Converts the raw sparse 1406-dim profile vector into readable category counts and active attributes.
        """
        if node_id < 0 or node_id >= self.total_nodes:
            return {}
        
        raw_vec = self.features_full[node_id, :1406]
        active_indices = np.where(raw_vec > 0)[0]
        
        category_breakdown = {}
        active_attributes = []
        for idx in active_indices:
            cat, name = self.feat_idx_to_cat.get(int(idx), ("other", f"feature_{idx}"))
            category_breakdown[cat] = category_breakdown.get(cat, 0) + 1
            if len(active_attributes) < 25: # Cap preview for fast serialization
                active_attributes.append({"category": cat, "name": name, "index": int(idx)})

        return {
            "total_active_features": int(len(active_indices)),
            "category_counts": category_breakdown,
            "active_sample": active_attributes
        }

    def get_subgraph(self, node_id: int, max_neighbors: int = 30) -> Optional[Dict[str, Any]]:
        if node_id < 0 or node_id >= self.total_nodes:
            return None
        
        neighbors = self.get_neighbors(node_id)[:max_neighbors]
        subgraph_nodes = [node_id] + neighbors
        node_set = set(subgraph_nodes)
        
        nodes_data = []
        for nid in subgraph_nodes:
            n_meta = self.node_metadata.get(str(nid), {})
            nodes_data.append({
                "id": nid,
                "label": f"Node #{nid}",
                "is_target": (nid == node_id),
                "is_fake": n_meta.get("is_fake", False),
                "true_label": n_meta.get("true_label", 0),
                "archetype": n_meta.get("archetype"),
                "risk_score": n_meta.get("risk_score", 0.0),
                "degree": n_meta.get("degree", 0),
                "community_id": n_meta.get("community_id", 0)
            })

        edges_data = []
        # Target node connections
        for neighbor in neighbors:
            edges_data.append({"source": node_id, "target": neighbor})
            
        # Inter-neighbor connections in subgraph
        for u in neighbors:
            for v in self.get_neighbors(u):
                if v in node_set and v != node_id and u < v:
                    edges_data.append({"source": u, "target": v})

        return {
            "center_node_id": node_id,
            "nodes": nodes_data,
            "edges": edges_data,
            "node_count": len(nodes_data),
            "edge_count": len(edges_data)
        }

    def get_cluster_subgraph(self, cluster_id: int, max_nodes: int = 50) -> Optional[Dict[str, Any]]:
        # Find cluster
        target_cluster = next((c for c in self.clusters if c["cluster_id"] == cluster_id), None)
        if not target_cluster:
            return None

        # Take sample nodes (prioritizing fakes for meaningful visualization)
        all_members = target_cluster["all_nodes"]
        fake_members = [nid for nid in all_members if self.labels[nid] == 1]
        gen_members = [nid for nid in all_members if self.labels[nid] == 0]

        selected_nodes = fake_members[:max_nodes // 2] + gen_members[:(max_nodes - min(len(fake_members), max_nodes // 2))]
        if not selected_nodes:
            selected_nodes = all_members[:max_nodes]

        node_set = set(selected_nodes)
        nodes_data = []
        for nid in selected_nodes:
            n_meta = self.node_metadata.get(str(nid), {})
            nodes_data.append({
                "id": nid,
                "label": f"Node #{nid}",
                "is_target": False,
                "is_fake": n_meta.get("is_fake", False),
                "true_label": n_meta.get("true_label", 0),
                "archetype": n_meta.get("archetype"),
                "risk_score": n_meta.get("risk_score", 0.0),
                "degree": n_meta.get("degree", 0),
                "community_id": cluster_id
            })

        edges_data = []
        for u in selected_nodes:
            for v in self.get_neighbors(u):
                if v in node_set and u < v:
                    edges_data.append({"source": u, "target": v})

        return {
            "cluster_id": cluster_id,
            "nodes": nodes_data,
            "edges": edges_data,
            "node_count": len(nodes_data),
            "edge_count": len(edges_data)
        }

    def list_nodes(
        self,
        split: Optional[str] = None,
        label: Optional[int] = None,
        archetype: Optional[str] = None,
        search_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        results = []
        
        # If explicit node id searched
        if search_id is not None:
            if 0 <= search_id < self.total_nodes:
                meta = self.get_node(search_id)
                if meta:
                    return {
                        "total": 1,
                        "page": 1,
                        "page_size": page_size,
                        "total_pages": 1,
                        "items": [meta]
                    }
            return {"total": 0, "page": 1, "page_size": page_size, "total_pages": 0, "items": []}

        # Filter nodes
        candidate_ids = range(self.total_nodes)
        if split == "test":
            candidate_ids = self.splits["test_idx"]
        elif split == "val":
            candidate_ids = self.splits["val_idx"]
        elif split == "train":
            candidate_ids = self.splits["train_idx"]

        for nid in candidate_ids:
            meta = self.node_metadata[str(nid)]
            if label is not None and meta["true_label"] != label:
                continue
            if archetype is not None and meta.get("archetype") != archetype:
                continue
            results.append(meta)

        total = len(results)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        start = (page - 1) * page_size
        end = start + page_size
        page_items = results[start:end]

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "items": page_items
        }
