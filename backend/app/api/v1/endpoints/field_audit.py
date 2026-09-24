"""
Field Audit, Evidence Validation, and Inspector Assignment endpoints.

Changes from v1:
  - Evidence validate: no more simulate_duplicate hack (removed)
  - Inspector schedule: uses cryptographic randomization + audit trail
  - Evidence validate: MIME/magic byte check, honest GPS status
"""

from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.auth import CurrentUser, get_current_user, require_role
from app.models import Institution
from app.models.audit_event import AuditEvent
from app.schemas.evidence import (
    EvidenceValidationResult,
    SchemeChecklist,
    InspectorProfile,
    InspectionScheduleRequest,
    InspectionScheduleResponse,
)
from app.services.evidence_validator import EvidenceValidator
from app.services.inspector_matcher import InspectorAssigner
from app.services.risk_engine import RiskEngine
from app.services.audit_logger import audit_logger

router = APIRouter()
_validator = EvidenceValidator()
_assigner  = InspectorAssigner()
_risk      = RiskEngine()


@router.post("/evidence/validate", response_model=EvidenceValidationResult)
async def validate_evidence(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Validates uploaded inspection evidence photo:
      - MIME / magic bytes check (rejects non-images and malformed files)
      - SHA-256 cryptographic hash
      - 64-bit dHash perceptual duplicate detection
      - Real EXIF GPS extraction (honest status — never claims VERIFIED_ON_SITE)
      - Comparison against historical evidence fingerprint database

    NOTE: simulate_duplicate parameter removed.
    Test with a real image to see genuine duplicate detection.
    """
    contents = await file.read()

    result = _validator.validate_file(
        file_bytes=contents,
        filename=file.filename or "evidence",
    )

    # Audit evidence upload
    audit_logger.log(
        db,
        AuditEvent.TYPE_EVIDENCE_VALIDATED,
        actor_id=current_user.user_id,
        actor_role=current_user.role,
        actor_name=current_user.full_name,
        metadata={
            "filename": file.filename,
            "integrity_status": result.integrity_status,
            "is_valid": result.is_valid,
            "sha256_prefix": result.sha256_hash[:16],
            "gps_status": result.exif_telemetry.gps_status,
        },
    )
    db.commit()

    return result


@router.get("/checklists/{scheme}", response_model=SchemeChecklist)
def get_scheme_checklist(
    scheme: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Returns dynamic statutory compliance checklist for the given scheme."""
    return _assigner.get_checklist_for_scheme(scheme)


@router.get("/inspectors", response_model=List[InspectorProfile])
def list_available_inspectors(
    current_user: CurrentUser = Depends(
        require_role("HQ_OFFICER", "SUPER_ADMIN")
    ),
):
    """
    Returns active certified inspectors.
    Access: HQ_OFFICER and above only (inspector pool is sensitive).
    """
    from app.services.inspector_matcher import CERTIFIED_INSPECTORS
    return CERTIFIED_INSPECTORS


@router.post("/schedule", response_model=InspectionScheduleResponse)
def schedule_inspection(
    payload: InspectionScheduleRequest,
    current_user: CurrentUser = Depends(
        require_role("HQ_OFFICER", "SUPER_ADMIN")
    ),
    db: Session = Depends(get_db),
):
    """
    Cryptographically randomized inspector assignment.

    Algorithm:
      1. Fetch institution and recalculate current risk.
      2. Filter eligible inspectors (jurisdiction + COI + availability).
      3. secrets.choice() for cryptographic random selection.
      4. Record full assignment audit metadata (who was eligible, who was selected).
      5. Return assignment with dispatch code.

    Access: HQ_OFFICER and above only.
    """
    inst = db.query(Institution).filter(Institution.id == payload.institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    risk_result = _risk.calculate_risk({
        "name":                    inst.name,
        "attendance_gap_pct":      inst.attendance_gap_pct,
        "camera_uptime_pct":       inst.camera_uptime_pct,
        "past_findings":           inst.past_findings,
        "vc_failures":             inst.vc_failures,
        "compliance_days_overdue": inst.compliance_days_overdue,
    })

    response = _assigner.assign(
        institution_id=inst.id,
        institution_name=inst.name,
        institution_state=inst.state or "Delhi",
        risk_score=risk_result.risk_score,
        risk_level=risk_result.risk_level,
        priority_multiplier=risk_result.inspection_probability,
        target_date=payload.target_date,
    )

    # Audit the assignment
    audit_logger.log(
        db,
        AuditEvent.TYPE_INSPECTION_ASSIGNED,
        actor_id=current_user.user_id,
        actor_role=current_user.role,
        actor_name=current_user.full_name,
        entity_type="Institution",
        entity_id=payload.institution_id,
        metadata={
            "institution_name": inst.name,
            "risk_score": risk_result.risk_score,
            "risk_level": risk_result.risk_level,
            "dispatch_code": response.dispatch_code,
            "assigned_inspector": (
                response.assigned_inspector.name if response.assigned_inspector else None
            ),
            "eligible_count": response.eligible_count,
            "algorithm_version": response.algorithm_version,
            "assignment_id": response.assignment_id,
        },
    )
    db.commit()

    return response
