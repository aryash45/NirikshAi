"""
GPS Geofence Validation endpoint.

ARCHITECTURE:
  The frontend captures GPS via navigator.geolocation.getCurrentPosition().
  Those raw coordinates are POSTed here for backend validation.
  The backend is the SOLE authority on ON_SITE / OUTSIDE_GEOFENCE status.
  The frontend NEVER determines geofence status — only the backend does.

This endpoint is called before inspection submission to confirm proximity.
Result is recorded in the audit trail.
"""

from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.auth import CurrentUser, get_current_user
from app.models.audit_event import AuditEvent
from app.models import Institution
from app.schemas.evidence import GpsSubmission, GpsValidationResponse
from app.services.gps_validator import GpsValidator
from app.services.audit_logger import audit_logger

router = APIRouter()
_gps = GpsValidator()


@router.post("/validate", response_model=GpsValidationResponse)
def validate_gps(
    payload: GpsSubmission,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Validates inspector GPS location against institution geofence.

    Input: GPS coordinates from navigator.geolocation (browser/device)
    Output: ON_SITE | OUTSIDE_GEOFENCE | GPS_STALE | LOW_ACCURACY | etc.

    Only this endpoint may determine VERIFIED_ON_SITE status.
    The frontend UI may display the result but must NOT compute it independently.
    """
    # Verify institution exists
    inst = db.query(Institution).filter(Institution.id == payload.institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail=f"Institution #{payload.institution_id} not found")

    result = _gps.validate(
        institution_id=payload.institution_id,
        inspector_lat=payload.inspector_lat,
        inspector_lng=payload.inspector_lng,
        accuracy_meters=payload.accuracy_meters,
        gps_timestamp=payload.gps_timestamp,
    )

    # Record GPS verification in audit trail
    event_type = (
        AuditEvent.TYPE_GPS_VERIFIED
        if result.status == "ON_SITE"
        else AuditEvent.TYPE_GPS_REJECTED
    )
    audit_logger.log(
        db,
        event_type,
        actor_id=current_user.user_id,
        actor_role=current_user.role,
        actor_name=current_user.full_name,
        entity_type="Institution",
        entity_id=payload.institution_id,
        metadata={
            "gps_status": result.status,
            "distance_meters": result.distance_meters,
            "accuracy_meters": payload.accuracy_meters,
            "institution_name": inst.name,
        },
    )
    db.commit()

    return GpsValidationResponse(
        status=result.status,
        distance_meters=result.distance_meters,
        allowed_radius_meters=result.allowed_radius_meters,
        inspector_lat=result.inspector_lat,
        inspector_lng=result.inspector_lng,
        inspector_accuracy_meters=result.inspector_accuracy_meters,
        gps_timestamp=result.gps_timestamp,
        institution_lat=result.institution_lat,
        institution_lng=result.institution_lng,
        validated_at=result.validated_at,
        reason=result.reason,
    )
