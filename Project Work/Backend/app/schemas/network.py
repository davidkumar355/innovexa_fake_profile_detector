"""
Pydantic schemas for network analysis endpoints.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel

class ClusterSummary(BaseModel):
    cluster_id: int
    size: int
    fake_count: int
    genuine_count: int
    fake_ratio: float
    mean_risk_score: float
    risk_level: str
    archetype_distribution: Dict[str, int]
    sample_nodes: List[int]

class ClusterListResponse(BaseModel):
    total_clusters: int
    high_risk_clusters: int
    clusters: List[ClusterSummary]

class GraphNode(BaseModel):
    id: int
    label: str
    is_target: bool
    is_fake: bool
    true_label: int
    archetype: Optional[str] = None
    risk_score: float
    degree: int
    community_id: int

class GraphEdge(BaseModel):
    source: int
    target: int

class SubgraphResponse(BaseModel):
    center_node_id: Optional[int] = None
    cluster_id: Optional[int] = None
    node_count: int
    edge_count: int
    nodes: List[GraphNode]
    edges: List[GraphEdge]
