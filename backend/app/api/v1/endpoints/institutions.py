"""
Institutions API endpoints.
"""

from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import Institution, AttendanceRecord, Inspection
from app.schemas import (
    InstitutionSummary,
    InstitutionDetail,
    AttendanceSeries,
    AttendancePatternResult,
    RiskDrivers,
    InspectionOut,
)
from app.services import RiskEngine, AttendanceAnalyzer

router = APIRouter()
_risk = RiskEngine()
_att = AttendanceAnalyzer()


def build_institution_summary(inst: Institution) -> InstitutionSummary:
    """Helper to compute risk score and format an InstitutionSummary schema."""
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


@router.get("", response_model=List[InstitutionSummary])
@router.get("/", response_model=List[InstitutionSummary], include_in_schema=False)
def list_institutions(db: Session = Depends(get_db)):
    """Retrieve all institutions sorted by risk score descending."""
    institutions = db.query(Institution).all()
    summaries = [build_institution_summary(i) for i in institutions]
    summaries.sort(key=lambda x: x.risk_score, reverse=True)
    return summaries


@router.get("/{institution_id}", response_model=InstitutionDetail)
def get_institution(institution_id: int, db: Session = Depends(get_db)):
    """Retrieve detailed institution profile with attendance series and pattern metrics."""
    inst = db.query(Institution).filter(Institution.id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    summary = build_institution_summary(inst)

    # Attendance series (last 7 records)
    records: List[AttendanceRecord] = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.institution_id == institution_id)
        .order_by(AttendanceRecord.date)
        .limit(7)
        .all()
    )
    att_series = [
        AttendanceSeries(day=r.day_label, reported=r.reported, observed=r.observed)
        for r in records
    ]

    # Pattern analysis
    reported_list = [r.reported for r in records]
    observed_list = [r.observed for r in records]
    pattern_raw = _att.analyze(reported_list, observed_list)
    pattern = AttendancePatternResult(
        avg_reported=pattern_raw.avg_reported,
        avg_observed=pattern_raw.avg_observed,
        persistent_gap_percent=pattern_raw.persistent_gap_percent,
        is_significant_discrepancy=pattern_raw.is_significant_discrepancy,
    )

    # Recent inspections (last 3)
    recent_inspections = (
        db.query(Inspection)
        .filter(Inspection.institution_id == institution_id)
        .order_by(Inspection.date.desc())
        .limit(3)
        .all()
    )
    insp_out = [InspectionOut.model_validate(i) for i in recent_inspections]

    return InstitutionDetail(
        **summary.model_dump(),
        attendance_series=att_series,
        attendance_pattern=pattern,
        recent_inspections=insp_out,
    )


@router.post("/{institution_id}/risk/recalculate", response_model=InstitutionSummary)
def recalculate_risk(institution_id: int, db: Session = Depends(get_db)):
    """Force re-calculation of risk score based on current DB signals."""
    inst = db.query(Institution).filter(Institution.id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    return build_institution_summary(inst)
