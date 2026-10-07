"""
Predict router: Endpoints for browsing node predictions and simulating new profiles.
"""

from fastapi import APIRouter, HTTPException, status
from app.schemas.predict import (
    BrowsePredictResponse,
    SimulatePredictRequest,
    SimulatePredictResponse
)
from app.services.predictor import PredictorService
from app.services.history_store import HistoryStore

router = APIRouter(prefix="/predict", tags=["Predictions"])

predictor = PredictorService.get_instance()
history_store = HistoryStore.get_instance()

@router.post("/browse/{node_id}", response_model=BrowsePredictResponse)
def predict_browse_node(node_id: int):
    """
    Option A: Look up an existing graph/test node and run inference.
    """
    if node_id < 0 or node_id >= predictor.data_store.total_nodes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node ID {node_id} out of range [0, {predictor.data_store.total_nodes - 1}]"
        )
    
    result = predictor.predict_browse(node_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not load data for node ID {node_id}"
        )

    # Persist interaction to detection history
    history_store.record_prediction(
        node_id=result["node_id"],
        mode="browse",
        prediction=result["prediction"],
        prediction_label=result["prediction_label"],
        risk_score=result["risk_score"],
        confidence=result["confidence"],
        archetype=result["archetype"],
        model_version=result["model_version"],
        details=f"True label: {result['true_label']}, split: {result['split']}"
    )

    return result

@router.post("/simulate", response_model=SimulatePredictResponse)
def predict_simulate_profile(payload: SimulatePredictRequest):
    """
    Option B: Inductive simulation — constructs a temporary profile from feature toggles
    and chosen graph connections, derives structural graph metrics, and runs inference.
    """
    # Validation
    for cid in payload.connection_node_ids:
        if cid < 0 or cid >= predictor.data_store.total_nodes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid connection node ID: {cid}. Must be within [0, {predictor.data_store.total_nodes - 1}]"
            )

    result = predictor.simulate_profile(
        active_feature_indices=payload.active_feature_indices,
        connection_node_ids=payload.connection_node_ids
    )

    # Persist interaction to detection history
    history_store.record_prediction(
        node_id=None,
        mode="simulate",
        prediction=result["prediction"],
        prediction_label=result["prediction_label"],
        risk_score=result["risk_score"],
        confidence=result["confidence"],
        archetype=None,
        model_version=result["model_version"],
        details=f"Connections: {len(payload.connection_node_ids)}, Active features: {len(payload.active_feature_indices)}"
    )

    return result
