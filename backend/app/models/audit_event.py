"""
Audit Event model — immutable, append-only, tamper-evident.

Every significant action in NirikshAi generates an AuditEvent.
Events are linked via a SHA-256 hash chain:
  event_hash = SHA256(previous_hash + canonical_json(event_fields))

This allows detection of record tampering, deletion, or reordering.
It is NOT a blockchain — it is a tamper-evident hash chain.

IMPORTANT: AuditEvents are never updated or deleted.
Use soft-delete or status flags on other models instead.
"""

from __future__ import annotations
import hashlib
import json
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text, func
from app.core.database import Base


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id            = Column(Integer, primary_key=True, index=True)
    event_id      = Column(String(36), unique=True, nullable=False, index=True)   # UUID
    event_type    = Column(String(80), nullable=False, index=True)
    actor_id      = Column(String(36), nullable=True)   # user_id or None for system
    actor_role    = Column(String(30), nullable=True)
    actor_name    = Column(String(200), nullable=True)
    entity_type   = Column(String(80), nullable=True)   # Institution | Inspection | Evidence
    entity_id     = Column(String(80), nullable=True)
    request_id    = Column(String(36), nullable=True)
    metadata_json = Column(Text, default="{}")           # JSON payload, no secrets
    previous_hash = Column(String(64), nullable=True)    # SHA-256 of previous event
    event_hash    = Column(String(64), nullable=False)   # SHA-256 of this event
    created_at    = Column(DateTime, default=func.now(), nullable=False)

    # ── Valid event types ────────────────────────────────────────────────
    # AUTH
    TYPE_LOGIN             = "LOGIN"
    TYPE_LOGOUT            = "LOGOUT"
    TYPE_LOGIN_FAILED      = "LOGIN_FAILED"
    # INSPECTION LIFECYCLE
    TYPE_INSPECTION_CREATED   = "INSPECTION_CREATED"
    TYPE_INSPECTION_ASSIGNED  = "INSPECTION_ASSIGNED"
    TYPE_INSPECTION_SUBMITTED = "INSPECTION_SUBMITTED"
    TYPE_INSPECTION_SYNCED    = "OFFLINE_SYNC"
    # EVIDENCE
    TYPE_EVIDENCE_UPLOADED  = "EVIDENCE_UPLOADED"
    TYPE_EVIDENCE_VALIDATED = "EVIDENCE_VALIDATED"
    TYPE_EVIDENCE_FLAGGED   = "EVIDENCE_FLAGGED"
    # GPS
    TYPE_GPS_VERIFIED       = "GPS_VERIFIED"
    TYPE_GPS_REJECTED       = "GPS_REJECTED"
    # RISK
    TYPE_RISK_RECALCULATED  = "RISK_RECALCULATED"
    TYPE_RISK_CONFIG_CHANGED = "RISK_CONFIG_CHANGED"
    # VC
    TYPE_VC_STARTED         = "VC_STARTED"
    TYPE_VC_COMPLETED       = "VC_COMPLETED"
    # ADMIN
    TYPE_ADMIN_ACTION       = "ADMIN_ACTION"

    @staticmethod
    def compute_event_hash(previous_hash: str | None, event_fields: dict) -> str:
        """
        Canonical hash for this event:
          SHA256(previous_hash + sorted_json(fields))
        This creates a tamper-evident chain: altering any field breaks all subsequent hashes.
        """
        canonical = json.dumps(event_fields, sort_keys=True, separators=(",", ":"),
                                default=str)
        prev = previous_hash or "GENESIS"
        digest_input = f"{prev}:{canonical}".encode("utf-8")
        return hashlib.sha256(digest_input).hexdigest()
