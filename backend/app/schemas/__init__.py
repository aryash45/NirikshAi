"""
Pydantic schemas registry.
"""

from app.schemas.attendance import AttendanceSeries, AttendancePatternResult
from app.schemas.risk import RiskDrivers
from app.schemas.common import StatsSummary
from app.schemas.inspection import (
    InspectionFindings,
    InspectionCreate,
    InspectionOut,
)
from app.schemas.institution import (
    InstitutionBase,
    InstitutionSummary,
    InstitutionDetail,
    InspectionResponse,
)
from app.schemas.cctv import OccupancyPoint, CctvAnalysisResult

__all__ = [
    "AttendanceSeries",
    "AttendancePatternResult",
    "RiskDrivers",
    "StatsSummary",
    "InspectionFindings",
    "InspectionCreate",
    "InspectionOut",
    "InstitutionBase",
    "InstitutionSummary",
    "InstitutionDetail",
    "InspectionResponse",
    "OccupancyPoint",
    "CctvAnalysisResult",
]
