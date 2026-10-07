"""
Dashboard router: Endpoint for aggregate detection metrics, trends, and distributions.
"""

from fastapi import APIRouter
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.data_store import DataStore

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

data_store = DataStore.get_instance()

@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary():
    """
    Returns high-level aggregate statistics powering dashboard KPI cards,
    detections-over-time trend chart, and fake archetype distribution donut chart.
    """
    return data_store.dashboard_summary
