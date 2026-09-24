"""
AuditLogger service — writes immutable, hash-chained AuditEvents.

Usage:
    from app.services.audit_logger import audit_logger, EventType
    audit_logger.log(db, EventType.INSPECTION_CREATED, actor=user, ...)
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent


class AuditLogger:
    """
    Writes append-only audit events with hash-chain integrity.
    Each event references the hash of the previous event, creating
    a tamper-evident chain. Altering any event breaks all subsequent hashes.
    """

    def _get_last_hash(self, db: Session) -> Optional[str]:
        """Fetch the hash of the most recent event (or None if first event)."""
        last = db.query(AuditEvent).order_by(AuditEvent.id.desc()).first()
        return last.event_hash if last else None

    def log(
        self,
        db: Session,
        event_type: str,
        *,
        actor_id: Optional[str] = None,
        actor_role: Optional[str] = None,
        actor_name: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> AuditEvent:
        """
        Create and persist one audit event.
        IMPORTANT: Never include passwords, tokens, or raw secrets in metadata.
        """
        event_id = str(uuid.uuid4())
        dt_now = datetime.now(timezone.utc).replace(microsecond=0)
        ts_str = dt_now.strftime("%Y-%m-%dT%H:%M:%SZ")
        prev_hash = self._get_last_hash(db)

        # Canonical payload for hash computation
        fields = {
            "event_id": event_id,
            "event_type": event_type,
            "actor_id": actor_id,
            "actor_role": actor_role,
            "entity_type": entity_type,
            "entity_id": str(entity_id) if entity_id is not None else None,
            "created_at": ts_str,
        }

        event_hash = AuditEvent.compute_event_hash(prev_hash, fields)

        import json
        sensitive_substrings = ("password", "secret", "bearer", "private_key", "credential")
        safe_metadata = {}
        if metadata:
            for k, v in metadata.items():
                key_lower = k.lower()
                if any(sub in key_lower for sub in sensitive_substrings):
                    continue
                safe_metadata[k] = v

        event = AuditEvent(
            event_id=event_id,
            event_type=event_type,
            actor_id=actor_id,
            actor_role=actor_role,
            actor_name=actor_name,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            request_id=request_id,
            metadata_json=json.dumps(safe_metadata, default=str),
            previous_hash=prev_hash,
            event_hash=event_hash,
            created_at=dt_now,
        )
        db.add(event)
        db.flush()  # Get ID without committing
        return event

    def verify_chain(self, db: Session) -> dict:
        """
        Walk the entire audit chain and verify hash integrity.
        Returns: {"valid": bool, "total_events": int, "broken_at_id": int | None}
        """
        events = db.query(AuditEvent).order_by(AuditEvent.id.asc()).all()
        prev_hash = None
        for event in events:
            dt = event.created_at
            if dt is not None and dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            ts_str = dt.strftime("%Y-%m-%dT%H:%M:%SZ") if dt else None

            fields = {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "actor_id": event.actor_id,
                "actor_role": event.actor_role,
                "entity_type": event.entity_type,
                "entity_id": event.entity_id,
                "created_at": ts_str,
            }
            expected = AuditEvent.compute_event_hash(prev_hash, fields)
            if expected != event.event_hash:
                return {
                    "valid": False,
                    "total_events": len(events),
                    "broken_at_id": event.id,
                    "broken_at_event_type": event.event_type,
                    "chain_status": "AUDIT_CHAIN_BROKEN",
                }
            prev_hash = event.event_hash

        return {
            "valid": True,
            "total_events": len(events),
            "broken_at_id": None,
            "chain_status": "AUDIT_CHAIN_VALID",
        }


# Singleton instance
audit_logger = AuditLogger()
