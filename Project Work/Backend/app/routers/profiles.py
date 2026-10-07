"""
Profiles router: Endpoints for searching, paginating, and inspecting node profiles and features.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from app.services.data_store import DataStore

router = APIRouter(prefix="/profiles", tags=["Profiles"])

data_store = DataStore.get_instance()

class ProfileListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[Dict[str, Any]]

@router.get("", response_model=ProfileListResponse)
def list_profiles(
    split: Optional[str] = Query("test", description="Filter by split ('test', 'val', 'train', or None for all)"),
    label: Optional[int] = Query(None, description="Filter by true label (0=Genuine, 1=Fake)"),
    archetype: Optional[str] = Query(None, description="Filter by fake archetype ('A', 'B', 'C', 'D')"),
    search_id: Optional[int] = Query(None, description="Direct search by Node ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Search and paginate profiles with optional filters for split, label, and archetype.
    """
    return data_store.list_nodes(
        split=split if split != "all" else None,
        label=label,
        archetype=archetype,
        search_id=search_id,
        page=page,
        page_size=page_size
    )

@router.get("/categories")
def get_feature_categories():
    """
    Returns the grouped feature categories (education, work, hometown, languages, etc.)
    derived from global_featnames.txt for the simulation UI toggles.
    """
    return data_store.feature_categories

@router.get("/{node_id}")
def get_profile_details(node_id: int):
    """
    Returns full metadata, structural attributes, and human-readable feature category summary
    for an individual node.
    """
    if node_id < 0 or node_id >= data_store.total_nodes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node ID {node_id} out of range [0, {data_store.total_nodes - 1}]"
        )
    
    node = data_store.get_node(node_id)
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found.")

    node["feature_summary"] = data_store.get_category_summary(node_id)
    return node
