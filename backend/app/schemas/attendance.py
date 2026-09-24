"""
Attendance schemas.
"""

from __future__ import annotations
from pydantic import BaseModel


class AttendanceSeries(BaseModel):
    day:      str
    reported: int
    observed: int


class AttendancePatternResult(BaseModel):
    avg_reported:               float
    avg_observed:               float
    persistent_gap_percent:     float
    is_significant_discrepancy: bool
