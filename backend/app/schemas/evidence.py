"""
Evidence validation, field audit, and inspector dispatcher schemas.
"""

from __future__ import annotations
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field


class DuplicateAlert(BaseModel):
    is_duplicate: bool
    similarity_pct: float
    matched_institution: Optional[str] = None
    original_inspection_date: Optional[str] = None
    alert_message: Optional[str] = None


class ExifMetadata(BaseModel):
    captured_at: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    device_model: Optional[str] = None
    is_gps_valid: bool = False
    gps_match_status: str = "VERIFIED_ON_SITE"


class EvidenceValidationResult(BaseModel):
    is_valid: bool
    file_name: str
    file_size_kb: float
    sha256_hash: str
    perceptual_hash: str
    exif_telemetry: ExifMetadata
    duplicate_alert: DuplicateAlert
    integrity_status: str  # "AUTHENTIC" | "SUSPECT_DUPLICATE" | "GEO_TAMPERED"


class ChecklistItem(BaseModel):
    id: str
    category: str  # "Attendance", "Infrastructure", "Staff", "Biometric"
    label: str
    required: bool = True
    evidence_required: bool = False


class SchemeChecklist(BaseModel):
    scheme: str
    scheme_code: str
    items: List[ChecklistItem]


class InspectorProfile(BaseModel):
    id: int
    name: str
    badge_number: str
    state: str
    district: str
    active_workload: int  # Current assigned inspections
    rating: float
    conflict_free: bool = True


class InspectionScheduleRequest(BaseModel):
    institution_id: int
    target_date: Optional[date] = None


class InspectionScheduleResponse(BaseModel):
    success: bool
    institution_id: int
    institution_name: str
    risk_score: float
    risk_level: str
    priority_multiplier: int
    assigned_inspector: InspectorProfile
    dispatch_code: str
    scheduled_for: date
    message: str
