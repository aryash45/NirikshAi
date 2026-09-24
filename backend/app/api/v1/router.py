"""
API v1 Router aggregating all endpoint sub-routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import institutions, inspections, cctv, stats, field_audit

api_v1_router = APIRouter()

api_v1_router.include_router(
    institutions.router, prefix="/institutions", tags=["Institutions"]
)
api_v1_router.include_router(
    inspections.router, prefix="/inspections", tags=["Inspections"]
)
api_v1_router.include_router(
    cctv.router, prefix="/cctv", tags=["CCTV Analysis"]
)
api_v1_router.include_router(
    stats.router, prefix="/stats", tags=["Statistics"]
)
api_v1_router.include_router(
    field_audit.router, prefix="/field-audit", tags=["Field Audit & Evidence"]
)
