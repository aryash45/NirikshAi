"""
Main application factory & entrypoint for NirikshAi.
"""

from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.router import api_v1_router
from app.websocket import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables exist on startup (idempotent; won't overwrite existing data)
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routers ────────────────────────────────────────────────────────────
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


# ── Health check ───────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {
        "service": f"{settings.PROJECT_NAME} API",
        "status":  "running",
        "version": settings.VERSION,
        "docs":    "/docs",
    }


# ── WebSocket: push risk-update events after inspection ───────────────────
@app.websocket("/ws/risk-updates")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; server pushes on POST /api/inspections
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
