"""
Evidence Integrity Validation Service.

WHAT THIS DOES:
  1. SHA-256 cryptographic hash — proves file integrity (detects byte-level changes)
  2. dHash (Difference Hash) — perceptual duplicate detection (detects recycled photos)
  3. EXIF metadata extraction — reads real capture timestamp and GPS (if present)
  4. File MIME validation via magic bytes — rejects malicious uploads
  5. Duplicate comparison against historical evidence database

WHAT THIS DOES NOT DO:
  - Does NOT prove authenticity of a new image (hash confirms integrity, not origin)
  - Does NOT guarantee photo was taken at a specific location
  - Does NOT perform facial recognition or biometric identification
  - Does NOT store images or raw media

HONEST LABELING:
  GPS status comes from actual EXIF data — never hardcoded.
  If EXIF GPS is absent: gps_status = "GPS_NOT_IN_IMAGE"
  If PIL unavailable:    gps_status = "EXIF_UNAVAILABLE"
  "VERIFIED_ON_SITE" requires backend GPS validation (see gps_validator.py)

DUPLICATE DETECTION:
  HIGH_VISUAL_SIMILARITY does not prove fraud.
  It flags the image for human review.
  Statuses: UNIQUE | EXACT_DUPLICATE | HIGH_VISUAL_SIMILARITY | REQUIRES_REVIEW
"""

from __future__ import annotations
import hashlib
import io
import struct
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

try:
    from PIL import Image, ExifTags
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from app.schemas.evidence import (
    EvidenceValidationResult,
    DuplicateAlert,
    ExifMetadata,
)

# ── MIME magic bytes ───────────────────────────────────────────────────────
# Maps mime type to (magic_bytes_hex_prefix, allowed_extensions)
ALLOWED_MIME_SIGNATURES: dict[str, Tuple[bytes, set]] = {
    "image/jpeg": (bytes.fromhex("FFD8FF"), {".jpg", ".jpeg"}),
    "image/png":  (bytes.fromhex("89504E470D0A1A0A"), {".png"}),
    "image/webp": (b"RIFF", {".webp"}),
}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
MIN_FILE_SIZE_BYTES = 64                # Anything smaller is not a real image

# ── Historical evidence fingerprints (demo) ────────────────────────────────
# In production: these come from the database (evidence table).
# These are REAL dHashes that would be computed from previously uploaded images.
# The hardcoded values here represent the demo historical database.
HISTORICAL_EVIDENCE: List[Dict] = [
    {
        "phash": "a5c3e1b7d9f20486",
        "institution_id": 1,
        "institution_name": "Navjeevan Skill Centre",
        "date": "2025-06-10",
        "inspector": "Ravi Kumar",
        "description": "Classroom attendance register",
    },
    {
        "phash": "f0e4c2a688b13579",
        "institution_id": 2,
        "institution_name": "Sahyadri Vocational Institute",
        "date": "2025-05-20",
        "inspector": "Ananya Sen",
        "description": "Computer lab batch occupancy",
    },
]

# Thresholds
EXACT_DUPLICATE_THRESHOLD = 99.0     # >= 99% identical: exact duplicate
HIGH_SIMILARITY_THRESHOLD  = 88.0    # >= 88%: visually similar, flag for review


class EvidenceValidator:
    """
    Validates inspection evidence (photos) against integrity and duplication.
    """

    # ── Hash computations ─────────────────────────────────────────────────

    def compute_sha256(self, data: bytes) -> str:
        """Standard SHA-256 cryptographic digest."""
        return hashlib.sha256(data).hexdigest()

    def compute_dhash(self, data: bytes) -> Optional[str]:
        """
        64-bit Difference Hash (dHash) using PIL.
        Returns None if PIL unavailable or image is corrupt.
        Invariant to: scaling, JPEG compression, minor brightness changes.
        Not invariant to: rotation, cropping, color channel swap.
        """
        if not HAS_PIL:
            return None
        try:
            with Image.open(io.BytesIO(data)) as img:
                resized = img.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
                pixels = list(resized.getdata())
                diff = []
                for row in range(8):
                    for col in range(8):
                        diff.append(1 if pixels[row * 9 + col] > pixels[row * 9 + col + 1] else 0)
                decimal_val = 0
                for bit in diff:
                    decimal_val = (decimal_val << 1) | bit
                return f"{decimal_val:016x}"
        except Exception:
            return None

    def hamming_similarity(self, hash1: str, hash2: str) -> float:
        """
        Perceptual similarity from Hamming distance on two 64-bit hex hashes.
        Returns 0.0–100.0.
        """
        try:
            v1, v2 = int(hash1, 16), int(hash2, 16)
            hamming = bin(v1 ^ v2).count("1")
            return round((1.0 - hamming / 64.0) * 100.0, 1)
        except (ValueError, TypeError):
            return 0.0

    # ── MIME / magic byte validation ──────────────────────────────────────

    def validate_mime(self, data: bytes, filename: str) -> Tuple[bool, str]:
        """
        Validates file against magic bytes. Returns (is_valid, reason).
        Rejects mismatched extensions, non-image magic, oversized files.
        """
        if len(data) < MIN_FILE_SIZE_BYTES:
            return False, f"File too small ({len(data)} bytes). Not a valid image."
        if len(data) > MAX_FILE_SIZE_BYTES:
            return False, f"File too large ({len(data) // 1024}KB > {MAX_FILE_SIZE_BYTES // 1024}KB limit)."

        import os
        ext = os.path.splitext(filename.lower())[-1]

        for mime_type, (magic, allowed_exts) in ALLOWED_MIME_SIGNATURES.items():
            if data[:len(magic)] == magic:
                if ext not in allowed_exts and ext != "":
                    return False, (
                        f"File magic bytes match {mime_type} but extension is '{ext}'. "
                        f"Possible content/extension mismatch. Rejected."
                    )
                return True, mime_type

        return False, f"Unrecognized file signature. Only JPEG, PNG, WebP are accepted."

    # ── EXIF extraction ───────────────────────────────────────────────────

    def extract_exif(self, data: bytes) -> ExifMetadata:
        """
        Reads REAL EXIF metadata from image bytes.
        Returns honest status — never hardcodes GPS coordinates.
        """
        if not HAS_PIL:
            return ExifMetadata(
                captured_at=None,
                latitude=None,
                longitude=None,
                device_model=None,
                is_gps_valid=False,
                gps_status="EXIF_UNAVAILABLE",
                exif_available=False,
            )

        try:
            with Image.open(io.BytesIO(data)) as img:
                exif_raw = img._getexif()

                if not exif_raw:
                    return ExifMetadata(
                        captured_at=None,
                        latitude=None, longitude=None,
                        device_model=None,
                        is_gps_valid=False,
                        gps_status="NO_EXIF_DATA",
                        exif_available=False,
                    )

                # Build tag name mapping
                tags = {ExifTags.TAGS.get(k, k): v for k, v in exif_raw.items()}

                # DateTime
                dt_str = tags.get("DateTimeOriginal") or tags.get("DateTime")
                captured_at = str(dt_str) if dt_str else None

                # Device model
                device_model = tags.get("Model") or tags.get("Make")

                # GPS — IFD 34853
                gps_info = tags.get("GPSInfo") or exif_raw.get(34853)
                lat, lng = None, None
                gps_valid = False
                gps_status = "GPS_NOT_IN_IMAGE"

                if gps_info and isinstance(gps_info, dict):
                    try:
                        # Tag 2 = GPSLatitude, 4 = GPSLongitude
                        raw_lat = gps_info.get(2)
                        raw_lng = gps_info.get(4)
                        lat_ref = gps_info.get(1, "N")
                        lng_ref = gps_info.get(3, "E")

                        if raw_lat and raw_lng:
                            def dms_to_decimal(dms):
                                if hasattr(dms[0], 'numerator'):
                                    d = dms[0].numerator / dms[0].denominator
                                    m = dms[1].numerator / dms[1].denominator
                                    s = dms[2].numerator / dms[2].denominator
                                else:
                                    d, m, s = float(dms[0]), float(dms[1]), float(dms[2])
                                return d + m / 60 + s / 3600

                            lat = round(dms_to_decimal(raw_lat), 6)
                            lng = round(dms_to_decimal(raw_lng), 6)
                            if str(lat_ref) == "S":
                                lat = -lat
                            if str(lng_ref) == "W":
                                lng = -lng
                            gps_valid = True
                            gps_status = "GPS_FROM_EXIF"
                    except Exception:
                        gps_status = "GPS_PARSE_ERROR"

                return ExifMetadata(
                    captured_at=captured_at,
                    latitude=lat,
                    longitude=lng,
                    device_model=str(device_model) if device_model else None,
                    is_gps_valid=gps_valid,
                    gps_status=gps_status,
                    exif_available=True,
                )
        except Exception as e:
            return ExifMetadata(
                captured_at=None,
                latitude=None, longitude=None,
                device_model=None,
                is_gps_valid=False,
                gps_status="EXIF_READ_ERROR",
                exif_available=False,
            )

    # ── Main validation ───────────────────────────────────────────────────

    def validate_file(
        self,
        file_bytes: bytes,
        filename: str,
    ) -> EvidenceValidationResult:
        """
        Full evidence validation pipeline:
          1. MIME / magic byte check
          2. SHA-256 hash
          3. dHash (if PIL available)
          4. EXIF extraction (honest GPS)
          5. Duplicate comparison against historical database
        """
        import os
        safe_filename = os.path.basename(filename) if filename else "evidence"

        # ── 1. MIME validation ────────────────────────────────────────────
        mime_ok, mime_result = self.validate_mime(file_bytes, safe_filename)
        if not mime_ok:
            return EvidenceValidationResult(
                is_valid=False,
                file_name=safe_filename,
                file_size_kb=round(len(file_bytes) / 1024, 1),
                sha256_hash=self.compute_sha256(file_bytes),
                perceptual_hash=None,
                exif_telemetry=ExifMetadata(
                    is_gps_valid=False, gps_status="FILE_REJECTED", exif_available=False,
                ),
                duplicate_alert=DuplicateAlert(is_duplicate=False, similarity_pct=0.0),
                integrity_status="REJECTED",
                rejection_reason=mime_result,
            )

        # ── 2. Cryptographic hash ─────────────────────────────────────────
        sha256 = self.compute_sha256(file_bytes)

        # ── 3. Perceptual hash ────────────────────────────────────────────
        phash = self.compute_dhash(file_bytes)

        # ── 4. EXIF ───────────────────────────────────────────────────────
        exif = self.extract_exif(file_bytes)

        # ── 5. Duplicate detection ────────────────────────────────────────
        highest_sim = 0.0
        matched_record = None
        phash_available = phash is not None

        if phash_available:
            for record in HISTORICAL_EVIDENCE:
                sim = self.hamming_similarity(phash, record["phash"])
                if sim > highest_sim:
                    highest_sim = sim
                    matched_record = record if sim >= HIGH_SIMILARITY_THRESHOLD else None

        # ── 6. Determine integrity status ─────────────────────────────────
        is_duplicate = highest_sim >= HIGH_SIMILARITY_THRESHOLD
        is_exact     = highest_sim >= EXACT_DUPLICATE_THRESHOLD

        if is_exact:
            integrity_status = "EXACT_DUPLICATE"
            alert_msg = (
                f"ALERT: Image is {highest_sim:.1f}% similar to evidence from "
                f"{matched_record['institution_name']} "
                f"(date: {matched_record['date']}, inspector: {matched_record['inspector']}). "
                f"HIGH_VISUAL_SIMILARITY — requires human review."
            )
        elif is_duplicate:
            integrity_status = "HIGH_VISUAL_SIMILARITY"
            alert_msg = (
                f"CAUTION: Image has {highest_sim:.1f}% visual similarity to prior evidence from "
                f"{matched_record['institution_name']} ({matched_record['date']}). "
                f"Requires review — similarity does NOT confirm fraud."
            )
        elif not phash_available:
            integrity_status = "REQUIRES_REVIEW"
            alert_msg = "PIL not available — perceptual duplicate check skipped. Manual review required."
        else:
            integrity_status = "UNIQUE"
            alert_msg = None

        return EvidenceValidationResult(
            is_valid=not is_duplicate,
            file_name=safe_filename,
            file_size_kb=round(len(file_bytes) / 1024, 1),
            sha256_hash=sha256,
            perceptual_hash=phash,
            exif_telemetry=exif,
            duplicate_alert=DuplicateAlert(
                is_duplicate=is_duplicate,
                similarity_pct=highest_sim,
                matched_institution=matched_record["institution_name"] if matched_record else None,
                original_inspection_date=matched_record["date"] if matched_record else None,
                alert_message=alert_msg,
            ),
            integrity_status=integrity_status,
            rejection_reason=None,
        )
