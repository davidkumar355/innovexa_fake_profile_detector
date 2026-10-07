"""
Predictor service: Handles inference for existing nodes and simulated profiles.
"""

import json
import os
from typing import Dict, List, Optional, Any
import joblib
import numpy as np

from app.config import settings
from app.services.data_store import DataStore

class PredictorService:
    _instance: Optional["PredictorService"] = None

    def __init__(self):
        self.artifacts_dir = settings.ARTIFACTS_DIR
        self.data_store = DataStore.get_instance()
        self._load_models()

    @classmethod
    def get_instance(cls) -> "PredictorService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_models(self):
        rf_path = os.path.join(self.artifacts_dir, "random_forest.joblib")
        scaler_path = os.path.join(self.artifacts_dir, "scaler.joblib")
        thresh_path = os.path.join(self.artifacts_dir, "thresholds.json")
        
        self.rf_model = joblib.load(rf_path)
        self.scaler = joblib.load(scaler_path)
        
        with open(thresh_path, "r", encoding="utf-8") as f:
            thresh_data = json.load(f)
            self.rf_threshold = float(thresh_data.get("random_forest", 0.50))
            
        print(f"[PredictorService] Loaded Random Forest model (threshold={self.rf_threshold:.2f}).")

    def predict_browse(self, node_id: int) -> Optional[Dict[str, Any]]:
        """
        Option A: Look up an existing test-set or graph node, return prediction + confidence.
        """
        meta = self.data_store.get_node(node_id)
        if not meta:
            return None

        scaled_feat = self.data_store.get_node_features(node_id, scaled=True)
        if scaled_feat is None:
            return None

        proba = float(self.rf_model.predict_proba(scaled_feat.reshape(1, -1))[0, 1])
        pred = 1 if proba >= self.rf_threshold else 0
        conf = round(proba if pred == 1 else (1.0 - proba), 4)

        cat_summary = self.data_store.get_category_summary(node_id)

        return {
            "node_id": node_id,
            "prediction": pred,
            "prediction_label": "Fake" if pred == 1 else "Genuine",
            "risk_score": round(proba, 4),
            "confidence": conf,
            "threshold": self.rf_threshold,
            "model_version": "RandomForest-v1.0",
            "archetype": meta.get("archetype"),
            "true_label": meta.get("true_label"),
            "split": meta.get("split"),
            "degree": meta.get("degree"),
            "clustering_coefficient": meta.get("clustering_coefficient"),
            "community_id": meta.get("community_id"),
            "feature_summary": cat_summary
        }

    def simulate_profile(
        self,
        active_feature_indices: List[int],
        connection_node_ids: List[int]
    ) -> Dict[str, Any]:
        """
        Option B: Inductive simulation — accepts user-chosen feature toggles and connection IDs.
        Computes structural metrics dynamically, standardizes, and evaluates via model.
        """
        # 1. Construct 1406 profile vector
        x_profile = np.zeros(1406, dtype=np.float32)
        valid_indices = [idx for idx in active_feature_indices if 0 <= idx < 1406]
        for idx in valid_indices:
            x_profile[idx] = 1.0

        # 2. Derive structural features from chosen connection nodes
        degree = float(len(connection_node_ids))
        
        # Estimate clustering coefficient among connected neighbors
        if degree >= 2:
            connected_set = set(connection_node_ids)
            triangles = 0
            possible_edges = (degree * (degree - 1)) / 2.0
            for u in connection_node_ids:
                u_neighbors = set(self.data_store.get_neighbors(u))
                triangles += len(u_neighbors.intersection(connected_set))
            triangles /= 2.0  # undirected count
            clustering = float(triangles / possible_edges) if possible_edges > 0 else 0.0
        else:
            clustering = 0.0

        # Estimate betweenness, closeness, community from neighbor averages
        if connection_node_ids:
            neighbor_metas = [self.data_store.get_node(n) for n in connection_node_ids if self.data_store.get_node(n)]
            if neighbor_metas:
                betweenness = float(np.mean([m["betweenness_centrality"] for m in neighbor_metas])) * 0.1
                closeness = float(np.mean([m["closeness_centrality"] for m in neighbor_metas])) * 0.9
                # Mode community ID
                comm_ids = [m["community_id"] for m in neighbor_metas]
                community_id = float(max(set(comm_ids), key=comm_ids.count))
            else:
                betweenness, closeness, community_id = 0.0, 0.25, 0.0
        else:
            betweenness, closeness, community_id = 0.0, 0.0, 0.0

        struct_raw = np.array([[degree, clustering, betweenness, closeness, community_id]], dtype=np.float32)
        
        # Scale structural features using fitted scaler
        struct_scaled = self.scaler.transform(struct_raw)

        # Concatenate full vector (1411,)
        x_simulated = np.hstack([x_profile.reshape(1, -1), struct_scaled])

        # Predict
        proba = float(self.rf_model.predict_proba(x_simulated)[0, 1])
        pred = 1 if proba >= self.rf_threshold else 0
        conf = round(proba if pred == 1 else (1.0 - proba), 4)

        # Risk classification
        if proba >= 0.70:
            risk_tier = "High Risk (Likely Fake)"
        elif proba >= self.rf_threshold:
            risk_tier = "Suspicious (Flagged for Review)"
        elif proba >= 0.30:
            risk_tier = "Low-Medium Risk (Normal Behavior)"
        else:
            risk_tier = "Very Low Risk (Highly Genuine)"

        return {
            "prediction": pred,
            "prediction_label": "Fake" if pred == 1 else "Genuine",
            "risk_score": round(proba, 4),
            "confidence": conf,
            "risk_tier": risk_tier,
            "threshold": self.rf_threshold,
            "model_version": "RandomForest-v1.0",
            "structural_features": {
                "degree": int(degree),
                "clustering_coefficient": round(clustering, 4),
                "betweenness_centrality": round(betweenness, 6),
                "closeness_centrality": round(closeness, 6),
                "inferred_community_id": int(community_id)
            },
            "active_feature_count": len(valid_indices),
            "connected_neighbors": connection_node_ids
        }
