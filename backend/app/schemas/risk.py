"""
Risk breakdown drivers schema.
"""

from __future__ import annotations
from pydantic import BaseModel, Field


class RiskDrivers(BaseModel):
    attendance_discrepancy: float = Field(..., description="Attendance gap contribution (max 30)")
    camera_issues:          float = Field(..., description="Camera downtime contribution (max 25)")
    inspection_history:     float = Field(..., description="Past findings contribution (max 20)")
    vc_verification:        float = Field(..., description="VC failure contribution (max 15)")
    compliance_overdue:     float = Field(..., description="Compliance delay contribution (max 10)")
