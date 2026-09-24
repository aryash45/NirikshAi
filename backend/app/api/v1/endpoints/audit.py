"""
Audit Trail endpoints — read audit events and verify chain integrity.

Access: AUDITOR role and above.
"""

from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.auth import CurrentUser, require_role
from app.models.audit_event import AuditEvent
from app.schemas.evidence import AuditEventOut, AuditChainVerification
from app.services.audit_logger import audit_logger

router = APIRouter()


@router.get("/events", response_model=List[AuditEventOut])
def list_audit_events(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: CurrentUser = Depends(require_role("HQ_OFFICER", "AUDITOR", "SUPER_ADMIN")),
    db: Session = Depends(get_db),
):
    """
    List audit events. Supports filtering by event type and entity.
    Access: AUDITOR, HQ_OFFICER, SUPER_ADMIN only.
    """
    q = db.query(AuditEvent).order_by(AuditEvent.id.desc())
    if event_type:
        q = q.filter(AuditEvent.event_type == event_type)
    if entity_type:
        q = q.filter(AuditEvent.entity_type == entity_type)
    return q.offset(offset).limit(limit).all()


@router.get("/verify-chain", response_model=AuditChainVerification)
def verify_audit_chain(
    current_user: CurrentUser = Depends(require_role("AUDITOR", "HQ_OFFICER", "SUPER_ADMIN")),
    db: Session = Depends(get_db),
):
    """
    Walk the entire audit event chain and verify SHA-256 hash integrity.
    Returns AUDIT_CHAIN_VALID or AUDIT_CHAIN_BROKEN with the event ID where chain breaks.
    """
    return audit_logger.verify_chain(db)
