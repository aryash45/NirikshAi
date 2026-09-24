"""
Attendance record database model.
"""

from __future__ import annotations
from sqlalchemy import Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id             = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False)
    date           = Column(Date, nullable=False)
    day_label      = Column(String(10))    # "Mon", "Tue", etc.
    reported       = Column(Integer)       # MIS / register figure
    observed       = Column(Integer)       # CCTV headcount

    institution = relationship("Institution", back_populates="attendance_records")
