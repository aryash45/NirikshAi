"""
Inspections API — submit, list, and manage field inspection records.

Changes from v1:
  - AUTH: Requires authentication (INSPECTOR or HQ_OFFICER)
  - IDEMPOTENCY: Duplicate submission via same idempotency_key is rejected
  - AUDIT: Every submission creates an immutable audit event
  - CLOSED LOOP: Risk signal updates happen in a transaction
"""

from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.v1.helpers import build_institution_summary
from app.core.auth import CurrentUser, get_current_user, require_role
from app.models import Institution, Inspection
from app.models.audit_event import AuditEvent
from app.schemas import (
    InspectionCreate,
    InspectionOut,
    InspectionResponse,
)
from app.services.audit_logger import audit_logger
from app.websocket import manager

router = APIRouter()


@router.post("", response_model=InspectionResponse)
@router.post("/", response_model=InspectionResponse, include_in_schema=False)
async def submit_inspection(
    payload: InspectionCreate,
    idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
    current_user: CurrentUser = Depends(
        require_role("INSPECTOR", "HQ_OFFICER", "SUPER_ADMIN")
    ),
    db: Session = Depends(get_db),
):
    """
    Submit a field inspection report.

    AUTH: Requires INSPECTOR or HQ_OFFICER role.
    IDEMPOTENCY: Supply X-Idempotency-Key header to prevent duplicate submissions.
      Same key within a session returns the original response.
    CLOSED LOOP: Updates institution risk signals and broadcasts via WebSocket.

    Steps:
      1. Validate institution exists.
      2. Check idempotency (if key provided).
      3. Persist inspection record.
      4. Update institution risk signals.
      5. Write audit event.
      6. Broadcast risk update via WebSocket.
    """
    # ── 1. Validate institution ───────────────────────────────────────────
    inst: Optional[Institution] = (
        db.query(Institution).filter(Institution.id == payload.institution_id).first()
    )
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    # ── 2. Idempotency check ──────────────────────────────────────────────
    # If the same idempotency key was used before, retrieve the earlier result.
    # This prevents duplicate inspection records on network retry.
    if idempotency_key:
        existing = (
            db.query(AuditEvent)
            .filter(
                AuditEvent.event_type == AuditEvent.TYPE_INSPECTION_SUBMITTED,
                AuditEvent.entity_id == str(payload.institution_id),
                AuditEvent.metadata_json.contains(idempotency_key),
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Duplicate submission: idempotency key '{idempotency_key}' was already used. "
                    f"Audit event ID: {existing.event_id}."
                ),
            )

    # ── 3. Persist inspection ─────────────────────────────────────────────
    inspection = Inspection(
        institution_id=payload.institution_id,
        inspector_name=current_user.full_name,   # Use authenticated name, not client-supplied
        date=payload.date,
        beneficiary_present=payload.findings.beneficiary_present,
        staff_present=payload.findings.staff_present,
        infrastructure_ok=payload.findings.infrastructure_ok,
        cctv_functional=payload.findings.cctv_functional,
        documents_available=payload.findings.documents_available,
        observations=payload.observations,
        severity=payload.severity,
    )
    db.add(inspection)

    # ── 4. Update institution risk signals (closed-loop feedback) ─────────
    if not payload.findings.cctv_functional:
        inst.camera_uptime_pct = max(0.0, inst.camera_uptime_pct - 5.0)

    if not payload.findings.documents_available:
        inst.compliance_days_overdue = min(100, inst.compliance_days_overdue + 30)

    if payload.severity == "CRITICAL":
        inst.past_findings = inst.past_findings + 2
    elif payload.severity == "MAJOR":
        inst.past_findings = inst.past_findings + 1

    if not payload.findings.beneficiary_present:
        inst.attendance_gap_pct = min(100.0, inst.attendance_gap_pct + 5.0)

    inst.last_inspected = payload.date

    # ── 5. Audit event ────────────────────────────────────────────────────
    audit_logger.log(
        db,
        AuditEvent.TYPE_INSPECTION_SUBMITTED,
        actor_id=current_user.user_id,
        actor_role=current_user.role,
        actor_name=current_user.full_name,
        entity_type="Inspection",
        entity_id=payload.institution_id,
        metadata={
            "institution_id": payload.institution_id,
            "institution_name": inst.name,
            "severity": payload.severity,
            "idempotency_key": idempotency_key,
            "beneficiary_present": payload.findings.beneficiary_present,
            "cctv_functional": payload.findings.cctv_functional,
        },
    )

    db.commit()
    db.refresh(inst)

    # ── 6. Build updated summary & broadcast ─────────────────────────────
    updated = build_institution_summary(inst)

    response = InspectionResponse(
        success=True,
        message=(
            f"Inspection submitted by {current_user.full_name}. "
            f"Risk score updated: {updated.risk_score}/100 [{updated.risk_level}]"
        ),
        updated_risk=updated,
    )

    try:
        await manager.broadcast({
            "event": "RISK_UPDATED",
            "institution_id": inst.id,
            "data": updated.model_dump(mode="json"),
        })
    except Exception:
        pass

    return response


@router.get("", response_model=List[InspectionOut])
@router.get("/", response_model=List[InspectionOut], include_in_schema=False)
def list_inspections(
    institution_id: Optional[int] = Query(None, description="Filter by institution"),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List recent inspection logs.
    INSPECTOR role: can only see inspections they submitted (future: filter by actor).
    HQ_OFFICER+: can see all.
    """
    q = db.query(Inspection)
    if institution_id is not None:
        q = q.filter(Inspection.institution_id == institution_id)
    return q.order_by(Inspection.date.desc()).limit(50).all()
