"""
Statistics API endpoints.
"""

from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.v1.endpoints.institutions import build_institution_summary
from app.models import Institution
from app.schemas import StatsSummary

router = APIRouter()


@router.get("/summary", response_model=StatsSummary)
def stats_summary(db: Session = Depends(get_db)):
    """Summary KPI metrics for the header cards."""
    institutions = db.query(Institution).all()
    summaries = [build_institution_summary(i) for i in institutions]

    high = sum(1 for s in summaries if s.risk_level == "HIGH")
    medium = sum(1 for s in summaries if s.risk_level == "MEDIUM")
    low = sum(1 for s in summaries if s.risk_level == "LOW")
    avg = round(sum(s.risk_score for s in summaries) / max(len(summaries), 1), 1)

    return StatsSummary(
        total=len(summaries),
        high=high,
        medium=medium,
        low=low,
        avg_risk_score=avg,
    )
