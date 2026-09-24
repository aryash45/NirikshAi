"""
CctvAnalyzer — YOLOv8 person-detection wrapper with deterministic mock fallback.

Strategy:
  1. Try to import ultralytics (YOLO). If available, run real detection.
  2. If ultralytics is not installed OR model download fails, fall back to a
     deterministic mock that generates realistic occupancy curves.
     The mock is seeded by the filename so it is reproducible across calls.

This guarantees the demo works even without internet or a GPU.
"""

from __future__ import annotations
import hashlib
import math
import os
import tempfile
from dataclasses import dataclass
from typing import List


@dataclass
class OccupancyPoint:
    second: int
    count:  int


@dataclass
class CctvAnalysisResult:
    occupancy_timeline: List[OccupancyPoint]
    peak_occupancy:     int
    avg_occupancy:      float
    frames_analyzed:    int
    is_mock:            bool = False


# ── Real YOLO path ─────────────────────────────────────────────────────────

def _analyze_with_yolo(video_bytes: bytes, filename: str) -> CctvAnalysisResult:
    """Run YOLOv8 nano on every 30th frame (~1 sample/sec at 30 fps)."""
    try:
        import cv2
        from ultralytics import YOLO
    except ImportError:
        raise RuntimeError("ultralytics / opencv not installed")

    model = YOLO("yolov8n.pt")   # nano: fastest, CPU-friendly

    # Write bytes to temp file so OpenCV can open it
    suffix = os.path.splitext(filename)[-1] or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(video_bytes)
        tmp_path = tmp.name

    try:
        cap = cv2.VideoCapture(tmp_path)
        fps          = cap.get(cv2.CAP_PROP_FPS) or 30
        sample_every = max(1, int(fps))   # 1 sample per second
        timeline: List[OccupancyPoint] = []
        frame_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % sample_every == 0:
                results = model.predict(frame, classes=[0], verbose=False, conf=0.4)
                count   = len(results[0].boxes) if results else 0
                timeline.append(OccupancyPoint(
                    second=frame_idx // sample_every,
                    count=count,
                ))
            frame_idx += 1

        cap.release()
    finally:
        os.unlink(tmp_path)

    if not timeline:
        timeline = [OccupancyPoint(second=0, count=0)]

    counts = [p.count for p in timeline]
    return CctvAnalysisResult(
        occupancy_timeline=timeline,
        peak_occupancy=max(counts),
        avg_occupancy=round(sum(counts) / len(counts), 1),
        frames_analyzed=frame_idx,
        is_mock=False,
    )


# ── Mock fallback ──────────────────────────────────────────────────────────

def _generate_mock_timeline(filename: str, duration_seconds: int = 30) -> CctvAnalysisResult:
    """
    Deterministic mock: produces a realistic sinusoidal occupancy curve.
    Seeded by filename hash so repeated calls return identical data.
    Produces numbers that look real (15–45 people with activity spikes).
    """
    seed = int(hashlib.md5(filename.encode()).hexdigest(), 16) % 10_000
    base_occupancy = 20 + (seed % 25)     # 20-45 people
    timeline: List[OccupancyPoint] = []

    for s in range(duration_seconds):
        # Sinusoidal variation + small random-looking noise (deterministic)
        noise = math.sin(s * 0.7 + seed) * 3 + math.cos(s * 1.3) * 2
        count = max(0, int(base_occupancy + noise))
        timeline.append(OccupancyPoint(second=s, count=count))

    counts = [p.count for p in timeline]
    return CctvAnalysisResult(
        occupancy_timeline=timeline,
        peak_occupancy=max(counts),
        avg_occupancy=round(sum(counts) / len(counts), 1),
        frames_analyzed=duration_seconds * 30,
        is_mock=True,
    )


# ── Public API ─────────────────────────────────────────────────────────────

class CctvAnalyzer:
    def analyze(self, video_bytes: bytes, filename: str) -> CctvAnalysisResult:
        """
        Attempt real YOLO analysis; fall back to mock on any failure.
        The caller can inspect `result.is_mock` to show a UI badge.
        """
        if not video_bytes:
            return _generate_mock_timeline(filename or "empty")

        try:
            return _analyze_with_yolo(video_bytes, filename)
        except Exception:
            # Graceful degradation: demo stays functional
            return _generate_mock_timeline(filename)
