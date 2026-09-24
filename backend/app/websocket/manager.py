"""
WebSocket connection manager for real-time risk updates.
"""

from __future__ import annotations
import json
from typing import List
from fastapi import WebSocket


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts risk updates."""

    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, message: dict):
        dead: List[WebSocket] = []
        for ws in self.active:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.append(ws)
        for ws in dead:
            if ws in self.active:
                self.active.remove(ws)


manager = ConnectionManager()
