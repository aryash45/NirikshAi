"""
Core application configuration using Pydantic Settings / Environment variables.
"""

from __future__ import annotations
import os
from typing import List
from pydantic import BaseModel


class Settings(BaseModel):
    PROJECT_NAME: str = "NirikshAi"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = (
        "AI-assisted institutional monitoring and risk-based inspection platform.\n\n"
        "**Core flow:** CCTV Occupancy → Attendance Verification → Risk Scoring → "
        "Smart Inspector Dispatch → Closed-Loop Feedback."
    )
    API_V1_STR: str = "/api"
    
    # Path to SQLite database at project root so it survives restarts
    DB_PATH: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
        "demo.db"
    )
    
    # CORS Origins
    CORS_ORIGINS: List[str] = ["*"]
    
    @property
    def DATABASE_URL(self) -> str:
        return f"sqlite:///{self.DB_PATH}"


settings = Settings()
