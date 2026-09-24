"""
Updated evidence, inspector, and GPS schemas.
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
    gps_status: str = "GPS_NOT_IN_IMAGE"  # Honest default
    exif_available: bool = False


class EvidenceValidationResult(BaseModel):
    is_valid: bool
    file_name: str
    file_size_kb: float
    sha256_hash: str
    perceptual_hash: Optional[str] = None
    exif_telemetry: ExifMetadata
    duplicate_alert: DuplicateAlert
    integrity_status: str  # UNIQUE | EXACT_DUPLICATE | HIGH_VISUAL_SIMILARITY | REJECTED | REQUIRES_REVIEW
    rejection_reason: Optional[str] = None


class ChecklistItem(BaseModel):
    id: str
    category: str
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
    active_workload: int
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
    assigned_inspector: Optional[InspectorProfile] = None
    dispatch_code: str
    scheduled_for: date
    message: str
    assignment_id: Optional[str] = None
    eligible_count: Optional[int] = None
    algorithm_version: Optional[str] = None


# ── GPS Validation Schemas ─────────────────────────────────────────────────

class GpsSubmission(BaseModel):
    """GPS coordinates submitted by field inspector device."""
    institution_id: int
    inspector_lat: float = Field(..., ge=-90, le=90)
    inspector_lng: float = Field(..., ge=-180, le=180)
    accuracy_meters: Optional[float] = Field(None, ge=0)
    gps_timestamp: Optional[str] = None   # ISO-8601


class GpsValidationResponse(BaseModel):
    status: str           # ON_SITE | OUTSIDE_GEOFENCE | GPS_UNVERIFIED | etc.
    distance_meters: Optional[float]
    allowed_radius_meters: int
    inspector_lat: Optional[float]
    inspector_lng: Optional[float]
    inspector_accuracy_meters: Optional[float]
    gps_timestamp: Optional[str]
    institution_lat: Optional[float]
    institution_lng: Optional[float]
    validated_at: str
    reason: str


# ── Audit Trail Schemas ────────────────────────────────────────────────────

class AuditEventOut(BaseModel):
    id: int
    event_id: str
    event_type: str
    actor_id: Optional[str]
    actor_role: Optional[str]
    actor_name: Optional[str]
    entity_type: Optional[str]
    entity_id: Optional[str]
    metadata_json: str
    previous_hash: Optional[str]
    event_hash: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditChainVerification(BaseModel):
    valid: bool
    total_events: int
    broken_at_id: Optional[int]
    chain_status: str  # AUDIT_CHAIN_VALID | AUDIT_CHAIN_BROKEN
