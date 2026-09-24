"""
CCTV analysis API endpoints.
"""

from __future__ import annotations
import os
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas import CctvAnalysisResult, OccupancyPoint
from app.services import CctvAnalyzer

router = APIRouter()
_analyzer = CctvAnalyzer()


@router.post("/analyze", response_model=CctvAnalysisResult)
async def analyze_cctv(video: UploadFile = File(...)):
    """
    Upload a video file (mp4/avi/mov) and get back a per-second occupancy count.
    Falls back to a deterministic mock if ultralytics is not installed.
    """
    allowed = {".mp4", ".avi", ".mov", ".mkv"}
    ext = os.path.splitext(video.filename or "video.mp4")[-1].lower()
    if ext not in allowed:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{ext}'. Use: {', '.join(allowed)}",
        )

    video_bytes = await video.read()
    if len(video_bytes) > 100 * 1024 * 1024:   # 100 MB guard
        raise HTTPException(status_code=413, detail="Video file must be < 100 MB")

    result = _analyzer.analyze(video_bytes, video.filename or "upload.mp4")

    return CctvAnalysisResult(
        occupancy_timeline=[
            OccupancyPoint(second=p.second, count=p.count)
            for p in result.occupancy_timeline
        ],
        peak_occupancy=result.peak_occupancy,
        avg_occupancy=result.avg_occupancy,
        frames_analyzed=result.frames_analyzed,
        is_mock=result.is_mock,
    )


@router.get("/mock", response_model=CctvAnalysisResult)
def get_mock_cctv():
    """
    Returns a pre-computed mock timeline for demo without video upload.
    Used during offline demo or when internet is unavailable.
    """
    result = _analyzer.analyze(b"", "demo_classroom.mp4")
    return CctvAnalysisResult(
        occupancy_timeline=[
            OccupancyPoint(second=p.second, count=p.count)
            for p in result.occupancy_timeline
        ],
        peak_occupancy=result.peak_occupancy,
        avg_occupancy=result.avg_occupancy,
        frames_analyzed=result.frames_analyzed,
        is_mock=True,
    )
