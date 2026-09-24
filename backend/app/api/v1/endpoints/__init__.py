"""Endpoints package."""

from app.api.v1.endpoints import institutions, inspections, cctv, stats, field_audit

__all__ = ["institutions", "inspections", "cctv", "stats", "field_audit"]
