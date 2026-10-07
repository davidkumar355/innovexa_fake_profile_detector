"""
History router: Endpoints to inspect, filter, and paginate detection history.
"""

from typing import Optional
from fastapi import APIRouter, Query
from app.schemas.history import HistoryListResponse
from app.services.history_store import HistoryStore

router = APIRouter(prefix="/history", tags=["Detection History"])

history_store = HistoryStore.get_instance()

@router.get("", response_model=HistoryListResponse)
def get_detection_history(
    mode: Optional[str] = Query(None, description="Filter by mode ('browse' or 'simulate')"),
    prediction: Optional[int] = Query(None, description="Filter by prediction (0=Genuine, 1=Fake)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Returns paginated prediction history records logged from live user interactions.
    """
    return history_store.list_history(
        mode=mode,
        prediction=prediction,
        page=page,
        page_size=page_size
    )

@router.delete("/clear")
def clear_detection_history():
    """
    Clears the detection history table (demo utility).
    """
    import sqlite3
    conn = sqlite3.connect(history_store.db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM detection_history")
    conn.commit()
    conn.close()
    return {"message": "Detection history cleared successfully."}
