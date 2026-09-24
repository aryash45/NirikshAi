"""
CCTV analysis schemas.
"""

from __future__ import annotations
from pydantic import BaseModel, Field


class OccupancyPoint(BaseModel):
    second: int
    count:  int


class CctvAnalysisResult(BaseModel):
    occupancy_timeline: list[OccupancyPoint]
    peak_occupancy:     int
    avg_occupancy:      float
    frames_analyzed:    int
    is_mock:            bool = Field(
        False,
        description="True when YOLO is unavailable and deterministic mock is used",
    )
