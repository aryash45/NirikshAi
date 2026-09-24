"""
Institution database model.
"""

from __future__ import annotations
from datetime import date, datetime
from sqlalchemy import Column, Date, DateTime, Float, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Institution(Base):
    __tablename__ = "institutions"

    id                      = Column(Integer, primary_key=True, index=True)
    name                    = Column(String(200), nullable=False)
    scheme                  = Column(String(100))          # Skill India / PMSSS / Apprentice
    district                = Column(String(100))
    state                   = Column(String(100))
    attendance_gap_pct      = Column(Float, default=0.0)   # % gap reported vs observed
    camera_uptime_pct       = Column(Float, default=100.0) # % camera availability
    past_findings           = Column(Integer, default=0)   # Unresolved inspection issues
    vc_failures             = Column(Integer, default=0)   # Failed video-conferencing verifications
    compliance_days_overdue = Column(Integer, default=0)   # Days since compliance deadline
    last_inspected          = Column(Date, nullable=True)
    created_at              = Column(DateTime, default=func.now())

    attendance_records = relationship(
        "AttendanceRecord", back_populates="institution",
        cascade="all, delete-orphan", order_by="AttendanceRecord.date",
    )
    inspections = relationship(
        "Inspection", back_populates="institution",
        cascade="all, delete-orphan", order_by="Inspection.date.desc()",
    )
