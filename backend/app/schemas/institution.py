"""
Institution schemas (Base, Summary, Detail, InspectionResponse).
"""

from __future__ import annotations
from datetime import date
from typing import Optional
from pydantic import BaseModel

from app.schemas.attendance import AttendanceSeries, AttendancePatternResult
from app.schemas.risk import RiskDrivers
from app.schemas.inspection import InspectionOut


class InstitutionBase(BaseModel):
    id:                      int
    name:                    str
    scheme:                  str
    district:                str
    state:                   str
    attendance_gap_pct:      float
    camera_uptime_pct:       float
    past_findings:           int
    vc_failures:             int
    compliance_days_overdue: int
    last_inspected:          Optional[date] = None


class InstitutionSummary(InstitutionBase):
    """Lightweight card for the dashboard list view."""
    risk_score:             float
    risk_level:             str   # "LOW" | "MEDIUM" | "HIGH"
    inspection_probability: int   # 1 | 4 | 7 multiplier
    drivers:                RiskDrivers

    model_config = {"from_attributes": True}


class InstitutionDetail(InstitutionSummary):
    """Full detail with attendance time-series and recent inspections."""
    attendance_series:   list[AttendanceSeries]
    attendance_pattern:  AttendancePatternResult
    recent_inspections:  list[InspectionOut]

    model_config = {"from_attributes": True}


class InspectionResponse(BaseModel):
    success:      bool
    message:      str
    updated_risk: InstitutionSummary
