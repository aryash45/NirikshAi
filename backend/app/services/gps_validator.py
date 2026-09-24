"""
GPS Validator service — backend-authoritative geofence verification.

ARCHITECTURE PRINCIPLE:
  The frontend captures raw GPS coordinates from navigator.geolocation.
  The BACKEND is the ONLY authority that may produce "VERIFIED_ON_SITE".
  Frontend GPS coordinates are UNTRUSTED INPUT until validated here.

Possible states:
  ON_SITE             — inspector is within allowed_radius_meters of institution
  OUTSIDE_GEOFENCE    — inspector is outside the allowed radius
  GPS_UNVERIFIED      — GPS not yet submitted for validation
  GPS_UNAVAILABLE     — GPS permission denied or device error
  GPS_STALE           — GPS timestamp too old (> max_age_seconds)
  LOW_ACCURACY        — GPS accuracy worse than threshold
  COORDINATES_MISSING — No coordinates in payload
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


# ── Configuration ──────────────────────────────────────────────────────────
# Configurable via environment; sensible defaults for field inspection
GEOFENCE_RADIUS_METERS = 300       # Inspector must be within 300m of institution
MAX_GPS_AGE_SECONDS    = 300       # GPS reading must be < 5 minutes old
MIN_GPS_ACCURACY       = 100.0     # Reject if accuracy worse than 100m (lower is better)

# Institution coordinates — source of truth.
# In production these would come from a surveyed database.
# DEMO: coordinates for each seed institution (lat, lng).
INSTITUTION_COORDINATES: dict[int, tuple[float, float]] = {
    1:  (26.8467, 80.9462),   # Navjeevan Skill Centre, Lucknow
    2:  (20.0059, 73.7898),   # Sahyadri Vocational, Nashik
    3:  (25.5941, 85.1376),   # Ganga Technical, Patna
    4:  (28.6139, 77.2090),   # Sunrise Apprentice Hub, New Delhi
    5:  (17.3850, 78.4867),   # Deccan Skills Academy, Hyderabad
    6:  (31.1048, 77.1734),   # Himalayan Training Centre, Shimla
    7:  (18.5204, 73.8567),   # Blue Ridge Institute, Pune
    8:  (28.6139, 77.2090),   # Capital Vocational School, New Delhi
    9:  (26.9124, 75.7873),   # Rajputana Skills Hub, Jaipur
    10: (21.1702, 72.8311),   # Coastal Training Academy, Surat
}


@dataclass
class GpsValidationResult:
    status: str                       # See module docstring for valid states
    distance_meters: Optional[float]  # Distance from institution (if computable)
    allowed_radius_meters: int        # Config at time of check
    inspector_lat: Optional[float]
    inspector_lng: Optional[float]
    inspector_accuracy_meters: Optional[float]
    gps_timestamp: Optional[str]      # ISO-8601 timestamp from device
    institution_lat: Optional[float]
    institution_lng: Optional[float]
    validated_at: str                 # Server timestamp
    reason: str                       # Human-readable explanation


class GpsValidator:
    """
    Validates that an inspector's GPS location falls within the
    institution's geofence. All validation is backend-side.
    """

    def _haversine(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        Returns distance in meters between two GPS coordinates.
        Haversine formula — accurate for short distances (<100km).
        """
        R = 6_371_000  # Earth radius in meters
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlng / 2) ** 2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def validate(
        self,
        institution_id: int,
        inspector_lat: Optional[float],
        inspector_lng: Optional[float],
        accuracy_meters: Optional[float],
        gps_timestamp: Optional[str],     # ISO-8601 from device
        allowed_radius: int = GEOFENCE_RADIUS_METERS,
    ) -> GpsValidationResult:
        """
        Main validation entry point. Called by backend on inspection submission.
        Never trusts client-side GPS status claims.
        """
        now_str = datetime.now(timezone.utc).isoformat()
        inst_coords = INSTITUTION_COORDINATES.get(institution_id)

        # ── Missing coordinates ───────────────────────────────────────────
        if inspector_lat is None or inspector_lng is None:
            return GpsValidationResult(
                status="COORDINATES_MISSING",
                distance_meters=None,
                allowed_radius_meters=allowed_radius,
                inspector_lat=None, inspector_lng=None,
                inspector_accuracy_meters=accuracy_meters,
                gps_timestamp=gps_timestamp,
                institution_lat=inst_coords[0] if inst_coords else None,
                institution_lng=inst_coords[1] if inst_coords else None,
                validated_at=now_str,
                reason="No GPS coordinates provided. Inspection cannot be marked on-site.",
            )

        # ── Validate coordinate ranges ────────────────────────────────────
        if not (-90 <= inspector_lat <= 90 and -180 <= inspector_lng <= 180):
            return GpsValidationResult(
                status="GPS_UNAVAILABLE",
                distance_meters=None,
                allowed_radius_meters=allowed_radius,
                inspector_lat=inspector_lat, inspector_lng=inspector_lng,
                inspector_accuracy_meters=accuracy_meters,
                gps_timestamp=gps_timestamp,
                institution_lat=inst_coords[0] if inst_coords else None,
                institution_lng=inst_coords[1] if inst_coords else None,
                validated_at=now_str,
                reason=f"Impossible GPS coordinates: ({inspector_lat}, {inspector_lng}). Rejected.",
            )

        # ── Low accuracy check ────────────────────────────────────────────
        if accuracy_meters is not None and accuracy_meters > MIN_GPS_ACCURACY:
            return GpsValidationResult(
                status="LOW_ACCURACY",
                distance_meters=None,
                allowed_radius_meters=allowed_radius,
                inspector_lat=inspector_lat, inspector_lng=inspector_lng,
                inspector_accuracy_meters=accuracy_meters,
                gps_timestamp=gps_timestamp,
                institution_lat=inst_coords[0] if inst_coords else None,
                institution_lng=inst_coords[1] if inst_coords else None,
                validated_at=now_str,
                reason=f"GPS accuracy {accuracy_meters:.0f}m exceeds threshold of {MIN_GPS_ACCURACY:.0f}m. Move to open area and retry.",
            )

        # ── Stale GPS check ───────────────────────────────────────────────
        if gps_timestamp:
            try:
                gps_dt = datetime.fromisoformat(gps_timestamp.replace("Z", "+00:00"))
                age_seconds = (datetime.now(timezone.utc) - gps_dt).total_seconds()
                if age_seconds > MAX_GPS_AGE_SECONDS:
                    return GpsValidationResult(
                        status="GPS_STALE",
                        distance_meters=None,
                        allowed_radius_meters=allowed_radius,
                        inspector_lat=inspector_lat, inspector_lng=inspector_lng,
                        inspector_accuracy_meters=accuracy_meters,
                        gps_timestamp=gps_timestamp,
                        institution_lat=inst_coords[0] if inst_coords else None,
                        institution_lng=inst_coords[1] if inst_coords else None,
                        validated_at=now_str,
                        reason=f"GPS reading is {age_seconds:.0f}s old (max {MAX_GPS_AGE_SECONDS}s). Refresh location.",
                    )
            except (ValueError, TypeError):
                pass  # Cannot parse timestamp; proceed without staleness check

        # ── Institution not in coordinate database ────────────────────────
        if inst_coords is None:
            return GpsValidationResult(
                status="GPS_UNVERIFIED",
                distance_meters=None,
                allowed_radius_meters=allowed_radius,
                inspector_lat=inspector_lat, inspector_lng=inspector_lng,
                inspector_accuracy_meters=accuracy_meters,
                gps_timestamp=gps_timestamp,
                institution_lat=None, institution_lng=None,
                validated_at=now_str,
                reason=f"Institution #{institution_id} has no registered coordinates. GPS cannot be verified.",
            )

        # ── Geofence distance check ───────────────────────────────────────
        inst_lat, inst_lng = inst_coords
        dist = self._haversine(inspector_lat, inspector_lng, inst_lat, inst_lng)
        dist_rounded = round(dist, 1)

        if dist <= allowed_radius:
            return GpsValidationResult(
                status="ON_SITE",
                distance_meters=dist_rounded,
                allowed_radius_meters=allowed_radius,
                inspector_lat=inspector_lat, inspector_lng=inspector_lng,
                inspector_accuracy_meters=accuracy_meters,
                gps_timestamp=gps_timestamp,
                institution_lat=inst_lat, institution_lng=inst_lng,
                validated_at=now_str,
                reason=f"Inspector is {dist_rounded:.0f}m from institution (within {allowed_radius}m geofence). ON SITE.",
            )
        else:
            return GpsValidationResult(
                status="OUTSIDE_GEOFENCE",
                distance_meters=dist_rounded,
                allowed_radius_meters=allowed_radius,
                inspector_lat=inspector_lat, inspector_lng=inspector_lng,
                inspector_accuracy_meters=accuracy_meters,
                gps_timestamp=gps_timestamp,
                institution_lat=inst_lat, institution_lng=inst_lng,
                validated_at=now_str,
                reason=f"Inspector is {dist_rounded:.0f}m away. Must be within {allowed_radius}m to be marked on-site.",
            )
