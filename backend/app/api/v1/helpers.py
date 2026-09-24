"""
Shared helper — builds InstitutionSummary from an Institution ORM object.
Defined once here; imported by institutions.py and inspections.py to avoid duplication.
"""

from __future__ import annotations
from app.models import Institution
from app.schemas import InstitutionSummary, RiskDrivers
from app.services import RiskEngine

_risk = RiskEngine()


def build_institution_summary(inst: Institution) -> InstitutionSummary:
    """Compute risk score and format an InstitutionSummary schema."""
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
