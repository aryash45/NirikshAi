"""
Main application factory for NirikshAi.
Includes security middleware, CORS, and all routers.
"""

from __future__ import annotations
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.router import api_v1_router
from app.websocket import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure all tables exist (idempotent — won't overwrite existing data)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS Middleware ────────────────────────────────────────────────────────
# PROTOTYPE: allows localhost origins for development.
# PRODUCTION: restrict to specific deployed frontend domain(s).
CORS_ORIGINS = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)


# ── Security Headers Middleware ────────────────────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(self)"
    # CSP: allows API + WebSocket from same host only
    response.headers["Content-Security-Policy"] = (
        "default-src 'none'; "
        "connect-src 'self' ws: wss:; "
        "frame-ancestors 'none';"
    )
    # HSTS: only enable in production with HTTPS
    if os.environ.get("ENABLE_HSTS") == "true":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# ── Request ID Middleware ──────────────────────────────────────────────────
import uuid

@app.middleware("http")
async def attach_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# ── API Routers ────────────────────────────────────────────────────────────
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


# ── Health / Ready endpoints ───────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {
        "service":  f"{settings.PROJECT_NAME} API",
        "status":   "running",
        "version":  settings.VERSION,
        "docs":     "/docs",
        "app_mode": os.environ.get("APP_MODE", "demo"),
    }


@app.get("/health", tags=["Health"])
def health():
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/ready", tags=["Health"])
def ready():
    """Readiness probe — checks DB connectivity."""
    try:
        from app.core.database import SessionLocal
        db = SessionLocal()
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db.close()
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail=f"Database not ready: {e}")


# ── WebSocket: authenticated risk-update channel ───────────────────────────
@app.websocket("/ws/risk-updates")
async def websocket_endpoint(websocket: WebSocket):
    """
    Real-time risk update channel.
    PROTOTYPE NOTE: Token validation on WS connections requires upgrade.
    In this prototype, we accept connections but limit broadcast content.
    Production: validate Bearer token from query param or first message.
    """
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
