"""
Pydantic schemas for dashboard summary endpoint.
"""

from typing import List, Dict
from pydantic import BaseModel

class DayDetection(BaseModel):
    day: str
    fake_detected: int
    genuine_detected: int
    total_analyzed: int

class ArchetypeDistribution(BaseModel):
    A: int
    B: int
    C: int
    D: int

class DashboardSummaryResponse(BaseModel):
    total_profiles_analyzed: int
    fake_detected: int
    genuine_detected: int
    high_risk_pending_review: int
    true_fake_count: int
    true_genuine_count: int
    model_accuracy: float
    model_f1_score: float
    model_precision: float
    model_recall: float
    model_auc: float
    threshold: float
    archetype_distribution: Dict[str, int]
    detections_over_time: List[DayDetection]
