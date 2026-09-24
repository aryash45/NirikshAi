"""
Inspection request and response schemas.
"""

from __future__ import annotations
from datetime import date
from pydantic import BaseModel, Field


class InspectionFindings(BaseModel):
    beneficiary_present: bool
    staff_present:       bool
    infrastructure_ok:   bool
    cctv_functional:     bool
    documents_available: bool


class InspectionCreate(BaseModel):
    institution_id: int
    inspector_name: str
    date:           date
    findings:       InspectionFindings
    observations:   str = ""
    severity:       str = Field(..., pattern="^(MINOR|MAJOR|CRITICAL)$")


class InspectionOut(BaseModel):
    id:             int
    institution_id: int
    inspector_name: str
    date:           date
    severity:       str
    observations:   str

    model_config = {"from_attributes": True}
