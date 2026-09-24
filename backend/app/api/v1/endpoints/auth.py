"""
Authentication endpoints — login, logout, current user.

PROTOTYPE NOTE:
  Uses pre-seeded demo users (see app/core/auth.py).
  Credentials are visible in the codebase because this is a demo.
  Production: replace with proper user database + bcrypt.

Demo credentials:
  hq_officer  / hq_password123  → HQ_OFFICER
  inspector1  / field_pass123   → INSPECTOR
  auditor     / audit_pass123   → AUDITOR
  viewer      / view_pass123    → VIEWER
"""

from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    CurrentUser,
    LoginRequest,
    LoginResponse,
    JWT_EXPIRE_MINUTES,
)
from app.services.audit_logger import audit_logger
from app.models.audit_event import AuditEvent

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate with username and password.
    Returns a Bearer token valid for {JWT_EXPIRE_MINUTES} minutes.
    """
    user = authenticate_user(payload.username, payload.password)

    if not user:
        # Log failed attempt (no sensitive data in log)
        audit_logger.log(
            db,
            AuditEvent.TYPE_LOGIN_FAILED,
            actor_name=payload.username,
            metadata={"username": payload.username, "reason": "Invalid credentials"},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user)

    audit_logger.log(
        db,
        AuditEvent.TYPE_LOGIN,
        actor_id=user.user_id,
        actor_role=user.role,
        actor_name=user.full_name,
        metadata={"username": user.username},
    )
    db.commit()

    return LoginResponse(
        access_token=token,
        user=user,
        expires_in_minutes=JWT_EXPIRE_MINUTES,
    )


@router.get("/me", response_model=CurrentUser)
def get_me(current_user: CurrentUser = Depends(get_current_user)):
    """Returns the currently authenticated user's profile."""
    return current_user


@router.post("/logout")
def logout(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Logout. Records audit event.
    Note: Token invalidation requires a blocklist in production.
    This prototype relies on token expiry.
    """
    audit_logger.log(
        db,
        AuditEvent.TYPE_LOGOUT,
        actor_id=current_user.user_id,
        actor_role=current_user.role,
        actor_name=current_user.full_name,
    )
    db.commit()
    return {"message": "Logged out. Discard the Bearer token on the client."}
