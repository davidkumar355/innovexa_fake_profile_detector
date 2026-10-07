"""
Pydantic schemas for detection history endpoints.
"""

from typing import List, Optional
from pydantic import BaseModel

class HistoryItem(BaseModel):
    id: int
    node_id: Optional[int] = None
    mode: str
    prediction: int
    prediction_label: str
    risk_score: float
    confidence: float
    archetype: Optional[str] = None
    model_version: str
    details: Optional[str] = None
    timestamp: str

class HistoryListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[HistoryItem]
