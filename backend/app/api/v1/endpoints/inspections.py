"""
Inspections API endpoints.
Implements the closed-loop feedback mechanism updating institution risk signals.
"""

from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import Institution, Inspection
from app.schemas import (
    InspectionCreate,
    InspectionOut,
    InspectionResponse,
    InstitutionSummary,
    RiskDrivers,
)
from app.services import RiskEngine
from app.websocket import manager

router = APIRouter()
_risk = RiskEngine()


def _build_summary(inst: Institution) -> InstitutionSummary:
    """Re-calculate risk from current DB state of the institution."""
    result = _risk.calculate_risk({
        "name":                    inst.name,
        "attendance_gap_pct":      inst.attendance_gap_pct,
        "camera_uptime_pct":       inst.camera_uptime_pct,
        "past_findings":           inst.past_findings,
        "vc_failures":             inst.vc_failures,
        "compliance_days_overdue": inst.compliance_days_overdue,
    })
    return InstitutionSummary(
        id=inst.id,
        name=inst.name,
        scheme=inst.scheme or "",
        district=inst.district or "",
        state=inst.state or "",
        attendance_gap_pct=inst.attendance_gap_pct,
        camera_uptime_pct=inst.camera_uptime_pct,
        past_findings=inst.past_findings,
        vc_failures=inst.vc_failures,
        compliance_days_overdue=inst.compliance_days_overdue,
        last_inspected=inst.last_inspected,
        risk_score=result.risk_score,
        risk_level=result.risk_level,
        inspection_probability=result.inspection_probability,
        drivers=RiskDrivers(**result.drivers),
    )


@router.post("", response_model=InspectionResponse)
@router.post("/", response_model=InspectionResponse, include_in_schema=False)
async def submit_inspection(payload: InspectionCreate, db: Session = Depends(get_db)):
    """
    Core closed-loop endpoint.

    Steps:
      1. Validate institution exists.
      2. Persist inspection record.
      3. Update institution's risk signals based on findings:
           - CCTV non-functional  → lower camera_uptime_pct by 5 points
           - Docs unavailable     → increment compliance_days_overdue by 30
           - Severity CRITICAL    → increment past_findings by 2
           - Severity MAJOR       → increment past_findings by 1
           - Absent beneficiaries → increment attendance_gap_pct by 5
      4. Update last_inspected date.
      5. Broadcast updated risk to connected WebSocket clients.
      6. Return refreshed risk score (frontend shows live score change).
    """
    inst: Optional[Institution] = (
        db.query(Institution)
        .filter(Institution.id == payload.institution_id)
        .first()
    )
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    # ── 1. Persist inspection record ─────────────────────────────────────
    inspection = Inspection(
        institution_id=payload.institution_id,
        inspector_name=payload.inspector_name,
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

    # ── 2. Update institution risk signals (closed-loop feedback) ─────────
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

    db.commit()
    db.refresh(inst)

    # ── 3. Return refreshed risk summary & broadcast ─────────────────────
    updated = _build_summary(inst)

    response = InspectionResponse(
        success=True,
        message=(
            f"Inspection recorded. Risk score updated: "
            f"{updated.risk_score}/100 [{updated.risk_level}]"
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
    db: Session = Depends(get_db),
):
    """List recent inspection logs with optional institution filtering."""
    q = db.query(Inspection)
    if institution_id is not None:
        q = q.filter(Inspection.institution_id == institution_id)
    return q.order_by(Inspection.date.desc()).limit(50).all()
