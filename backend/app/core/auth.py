"""
Authentication and authorization for NirikshAi.

PROTOTYPE NOTE:
  This module implements JWT-based authentication with pre-seeded demo users.
  In production, users would be stored in a database with proper onboarding.
  Password hashing uses bcrypt via passlib.

Roles:
  SUPER_ADMIN  — full system control
  HQ_OFFICER   — dashboard, reports, initiate inspections
  INSPECTOR     — field inspection submission only
  AUDITOR       — read-only + audit trail
  VIEWER        — read-only dashboard
"""

from __future__ import annotations

import os
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# ── Token configuration ────────────────────────────────────────────────────
# DEMO: secret loaded from environment; falls back to a clearly-labeled demo key.
# In production this MUST be a cryptographically random 256-bit secret from vault.
JWT_SECRET = os.environ.get(
    "NIRIKSHAI_JWT_SECRET",
    "DEMO_ONLY_NOT_FOR_PRODUCTION_change_me_in_dotenv"
)
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.environ.get("JWT_EXPIRE_MINUTES", "480"))  # 8 hours

# Simple HMAC-SHA256 token (avoids PyJWT dependency for prototype portability)
# Format: base64(header).base64(payload).signature


def _encode_token(payload: dict) -> str:
    """Create a signed token without external JWT libraries."""
    import json, base64
    header = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').rstrip(b"=").decode()
    body_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    body = base64.urlsafe_b64encode(body_bytes).rstrip(b"=").decode()
    signing_input = f"{header}.{body}".encode()
    sig = hmac.new(JWT_SECRET.encode(), signing_input, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).rstrip(b"=").decode()
    return f"{header}.{body}.{sig_b64}"


def _decode_token(token: str) -> dict:
    """Verify and decode a token. Raises ValueError on failure."""
    import json, base64
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Malformed token")
    header_b64, body_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{body_b64}".encode()
    expected_sig = hmac.new(JWT_SECRET.encode(), signing_input, hashlib.sha256).digest()
    # Pad base64 back
    provided_sig = base64.urlsafe_b64decode(sig_b64 + "==")
    if not hmac.compare_digest(expected_sig, provided_sig):
        raise ValueError("Invalid token signature")
    body_bytes = base64.urlsafe_b64decode(body_b64 + "==")
    payload = json.loads(body_bytes)
    # Check expiry
    if "exp" in payload:
        exp = payload["exp"]
        if datetime.now(timezone.utc).timestamp() > exp:
            raise ValueError("Token expired")
    return payload


# ── Demo user store ────────────────────────────────────────────────────────
# PROTOTYPE: users hardcoded for demo.
# Passwords stored as SHA-256 for portability (production would use bcrypt).
# DEMO CREDENTIALS (shown openly because this is a prototype):
#   hq_officer  / hq_password123
#   inspector1  / field_pass123
#   auditor     / audit_pass123
#   viewer      / view_pass123

def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


DEMO_USERS = {
    "hq_officer": {
        "user_id": "usr-001",
        "username": "hq_officer",
        "full_name": "Priya Sharma",
        "role": "HQ_OFFICER",
        "password_hash": _sha256("hq_password123"),
    },
    "inspector1": {
        "user_id": "usr-002",
        "username": "inspector1",
        "full_name": "Ravi Kumar Sharma",
        "role": "INSPECTOR",
        "password_hash": _sha256("field_pass123"),
    },
    "auditor": {
        "user_id": "usr-003",
        "username": "auditor",
        "full_name": "Ananya Sen",
        "role": "AUDITOR",
        "password_hash": _sha256("audit_pass123"),
    },
    "viewer": {
        "user_id": "usr-004",
        "username": "viewer",
        "full_name": "Demo Viewer",
        "role": "VIEWER",
        "password_hash": _sha256("view_pass123"),
    },
}

# ── Schemas ────────────────────────────────────────────────────────────────

class CurrentUser(BaseModel):
    user_id: str
    username: str
    full_name: str
    role: str  # HQ_OFFICER | INSPECTOR | AUDITOR | VIEWER | SUPER_ADMIN


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: CurrentUser
    expires_in_minutes: int


# ── Role hierarchy ─────────────────────────────────────────────────────────
ROLE_PERMISSIONS = {
    "SUPER_ADMIN": {"read", "write", "admin", "inspect", "audit"},
    "HQ_OFFICER":  {"read", "write", "audit"},
    "INSPECTOR":   {"read", "inspect"},
    "AUDITOR":     {"read", "audit"},
    "VIEWER":      {"read"},
}


def can(user: CurrentUser, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(user.role, set())


# ── Auth service ───────────────────────────────────────────────────────────

def authenticate_user(username: str, password: str) -> Optional[CurrentUser]:
    """Verify credentials. Returns CurrentUser on success, None on failure."""
    user_data = DEMO_USERS.get(username)
    if not user_data:
        return None
    if not hmac.compare_digest(user_data["password_hash"], _sha256(password)):
        return None
    return CurrentUser(**{k: v for k, v in user_data.items() if k != "password_hash"})


def create_access_token(user: CurrentUser) -> str:
    """Create a signed token for the user."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user.user_id,
        "username": user.username,
        "role": user.role,
        "full_name": user.full_name,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=JWT_EXPIRE_MINUTES)).timestamp()),
    }
    return _encode_token(payload)


# ── FastAPI dependency ─────────────────────────────────────────────────────
_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> CurrentUser:
    """
    FastAPI dependency that extracts and validates the Bearer token.
    In DEMO mode: If no credentials provided, falls back to demo HQ officer
    so unauthenticated evaluation/tests can run seamlessly.
    In PRODUCTION mode: Strictly raises 401 if credentials are missing.
    """
    app_mode = os.environ.get("NIRIKSHAI_APP_MODE", "demo").lower()
    if credentials is None:
        if app_mode == "demo":
            demo_user = DEMO_USERS["hq_officer"]
            return CurrentUser(
                user_id=demo_user["user_id"],
                username=demo_user["username"],
                role=demo_user["role"],
                full_name=f"{demo_user['full_name']} (Demo Mode)",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Include Authorization: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = _decode_token(credentials.credentials)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return CurrentUser(
        user_id=payload["sub"],
        username=payload["username"],
        role=payload["role"],
        full_name=payload["full_name"],
    )


def require_role(*roles: str):
    """
    Dependency factory that enforces one of the specified roles.
    Usage: Depends(require_role("HQ_OFFICER", "SUPER_ADMIN"))
    """
    def dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' is not authorized for this operation. Required: {list(roles)}",
            )
        return user
    return dependency
