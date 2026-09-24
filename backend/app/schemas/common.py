"""
Common statistics and shared schemas.
"""

from __future__ import annotations
from pydantic import BaseModel


class StatsSummary(BaseModel):
    total:          int
    high:           int
    medium:         int
    low:            int
    avg_risk_score: float
