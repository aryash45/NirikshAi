"""
Field Audit, Evidence Validation, and Smart Inspector Dispatcher endpoints.
"""

from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import Institution
from app.schemas.evidence import (
    EvidenceValidationResult,
    SchemeChecklist,
    InspectorProfile,
    InspectionScheduleRequest,
    InspectionScheduleResponse,
)
from app.services.evidence_validator import EvidenceValidator
from app.services.inspector_matcher import InspectorMatcher
from app.services.risk_engine import RiskEngine

router = APIRouter()
_validator = EvidenceValidator()
_matcher = InspectorMatcher()
_risk = RiskEngine()


@router.post("/evidence/validate", response_model=EvidenceValidationResult)
async def validate_evidence(
    file: UploadFile = File(...),
    simulate_duplicate: bool = Query(
        False,
        description="Force duplicate alert matching previous inspection for demo evaluation",
    ),
):
    """
    Validates uploaded inspection photo/document:
    - Generates cryptographic SHA-256 digest
    - Generates 64-bit Difference Perceptual Hash (dHash)
    - Compares perceptual similarity against historical inspection evidence
    - Extracts GPS geolocation & capture timestamp from EXIF
    """
    contents = await file.read()
    if len(contents) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Evidence file must be smaller than 25MB")

    return _validator.validate_file(
        file_bytes=contents,
        filename=file.filename or "evidence.jpg",
        simulate_duplicate=simulate_duplicate,
    )


@router.get("/checklists/{scheme}", response_model=SchemeChecklist)
def get_scheme_checklist(scheme: str):
    """
    Returns dynamic, statutory compliance checklist tailored to the scheme
    (Skill India, PMSSS, Apprenticeship Promotion Scheme).
    """
    return _matcher.get_checklist_for_scheme(scheme)


@router.get("/inspectors", response_model=List[InspectorProfile])
def list_available_inspectors():
    """
    Returns active certified field auditors with jurisdiction and workload metrics.
    """
    return _matcher.CERTIFIED_INSPECTORS


@router.post("/schedule", response_model=InspectionScheduleResponse)
def schedule_inspection(
    payload: InspectionScheduleRequest,
    db: Session = Depends(get_db),
):
    """
    Smart Inspector Assignment Algorithm:
    1. Looks up target institution and recalculates risk score.
    2. Applies priority multiplier (7x for HIGH risk, 4x for MEDIUM, 1x for LOW).
    3. Matches available auditors by jurisdiction and eliminates conflicts of interest.
    4. Balances workload and assigns official dispatch code.
    """
    inst = db.query(Institution).filter(Institution.id == payload.institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    risk_result = _risk.calculate_risk({
        "name": inst.name,
        "attendance_gap_pct": inst.attendance_gap_pct,
        "camera_uptime_pct": inst.camera_uptime_pct,
        "past_findings": inst.past_findings,
        "vc_failures": inst.vc_failures,
        "compliance_days_overdue": inst.compliance_days_overdue,
    })

    return _matcher.schedule_dispatch(
        institution_id=inst.id,
        institution_name=inst.name,
        state=inst.state or "Delhi",
        risk_score=risk_result.risk_score,
        risk_level=risk_result.risk_level,
        priority_multiplier=risk_result.inspection_probability,
        target_date=payload.target_date,
    )
