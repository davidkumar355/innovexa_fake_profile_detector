"""
Network router: Endpoints for cluster exploration and interactive subgraph visualization.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.schemas.network import (
    ClusterListResponse,
    SubgraphResponse
)
from app.services.data_store import DataStore

router = APIRouter(prefix="/network", tags=["Network Analysis"])

data_store = DataStore.get_instance()

@router.get("/clusters", response_model=ClusterListResponse)
def get_clusters(
    min_fake_ratio: float = Query(0.0, ge=0.0, le=1.0, description="Filter clusters with fake ratio >= threshold"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level (High, Medium, Low)")
):
    """
    Returns detected community clusters ranked by risk and fake ratio.
    """
    filtered = []
    for c in data_store.clusters:
        if c["fake_ratio"] < min_fake_ratio:
            continue
        if risk_level and c["risk_level"].lower() != risk_level.lower():
            continue
        filtered.append({
            "cluster_id": c["cluster_id"],
            "size": c["size"],
            "fake_count": c["fake_count"],
            "genuine_count": c["genuine_count"],
            "fake_ratio": c["fake_ratio"],
            "mean_risk_score": c["mean_risk_score"],
            "risk_level": c["risk_level"],
            "archetype_distribution": c["archetype_distribution"],
            "sample_nodes": c["sample_nodes"]
        })

    high_risk_cnt = sum(1 for c in filtered if c["risk_level"] == "High")

    return {
        "total_clusters": len(filtered),
        "high_risk_clusters": high_risk_cnt,
        "clusters": filtered
    }

@router.get("/cluster/{cluster_id}/subgraph", response_model=SubgraphResponse)
def get_cluster_subgraph(cluster_id: int, max_nodes: int = Query(50, ge=5, le=100)):
    """
    Returns visual subgraph nodes and edges for a given community cluster.
    """
    sub = data_store.get_cluster_subgraph(cluster_id, max_nodes=max_nodes)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cluster ID {cluster_id} not found."
        )
    return sub

@router.get("/node/{node_id}/subgraph", response_model=SubgraphResponse)
def get_node_neighborhood_subgraph(node_id: int, max_neighbors: int = Query(25, ge=1, le=50)):
    """
    Returns local 1-hop / 2-hop neighborhood of a node to visually inspect
    why the model classified it as Fake or Genuine.
    """
    if node_id < 0 or node_id >= data_store.total_nodes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node ID {node_id} out of range."
        )

    sub = data_store.get_subgraph(node_id, max_neighbors=max_neighbors)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not construct subgraph for node {node_id}."
        )
    return sub
