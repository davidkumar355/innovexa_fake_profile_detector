"""
Pydantic schemas for prediction endpoints.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class BrowsePredictResponse(BaseModel):
    node_id: int
    prediction: int
    prediction_label: str
    risk_score: float
    confidence: float
    threshold: float
    model_version: str
    archetype: Optional[str] = None
    true_label: Optional[int] = None
    split: Optional[str] = None
    degree: int
    clustering_coefficient: float
    community_id: int
    feature_summary: Dict[str, Any]

class SimulatePredictRequest(BaseModel):
    active_feature_indices: List[int] = Field(default=[], description="List of active binary feature indices (0-1405)")
    connection_node_ids: List[int] = Field(default=[], description="List of existing graph node IDs to connect to (0-4488)")

class SimulatePredictResponse(BaseModel):
    prediction: int
    prediction_label: str
    risk_score: float
    confidence: float
    risk_tier: str
    threshold: float
    model_version: str
    structural_features: Dict[str, Any]
    active_feature_count: int
    connected_neighbors: List[int]
