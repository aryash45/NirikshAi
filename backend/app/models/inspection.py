"""
Inspection database model.
"""

from __future__ import annotations
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Inspection(Base):
    __tablename__ = "inspections"

    id                   = Column(Integer, primary_key=True, index=True)
    institution_id       = Column(Integer, ForeignKey("institutions.id"), nullable=False)
    inspector_name       = Column(String(200))
    date                 = Column(Date, nullable=False)
    beneficiary_present  = Column(Boolean, default=False)
    staff_present        = Column(Boolean, default=False)
    infrastructure_ok    = Column(Boolean, default=False)
    cctv_functional      = Column(Boolean, default=False)
    documents_available  = Column(Boolean, default=False)
    observations         = Column(Text, default="")
    severity             = Column(String(20))   # MINOR / MAJOR / CRITICAL
    created_at           = Column(DateTime, default=func.now())

    institution = relationship("Institution", back_populates="inspections")
