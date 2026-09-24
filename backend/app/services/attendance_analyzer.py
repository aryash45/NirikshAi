"""
AttendanceAnalyzer — Pattern-based attendance discrepancy detection.
Key insight: ONE day's mismatch is noise. A PERSISTENT week-long gap is signal.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class AttendanceAnalysisResult:
    avg_reported:               float
    avg_observed:               float
    persistent_gap_percent:     float
    is_significant_discrepancy: bool
    daily_gaps:                 List[float]   # gap % for each day
    trend:                      str           # "WORSENING" | "IMPROVING" | "STABLE"


class AttendanceAnalyzer:
    DISCREPANCY_THRESHOLD = 20.0   # > 20% persistent gap triggers flag

    def analyze(
        self,
        reported_list: List[int],
        observed_list:  List[int],
        day_labels:     Optional[List[str]] = None,
    ) -> AttendanceAnalysisResult:
        """
        Compare MIS-reported attendance vs CCTV-observed occupancy over N days.
        Returns pattern metrics, not single-day snapshot.
        """
        if not reported_list or not observed_list:
            return AttendanceAnalysisResult(
                avg_reported=0.0, avg_observed=0.0,
                persistent_gap_percent=0.0, is_significant_discrepancy=False,
                daily_gaps=[], trend="STABLE",
            )

        n = min(len(reported_list), len(observed_list))
        reported = reported_list[:n]
        observed  = observed_list[:n]

        avg_rep  = sum(reported) / n
        avg_obs  = sum(observed)  / n

        if avg_rep == 0:
            gap_pct = 0.0
        else:
            gap_pct = ((avg_rep - avg_obs) / avg_rep) * 100

        # Per-day gaps (used to compute trend)
        daily_gaps = []
        for r, o in zip(reported, observed):
            if r == 0:
                daily_gaps.append(0.0)
            else:
                daily_gaps.append(round(((r - o) / r) * 100, 1))

        # Trend: compare first-half average vs second-half average
        half = n // 2
        if half >= 1:
            first_half_gap  = sum(daily_gaps[:half])  / half
            second_half_gap = sum(daily_gaps[half:])  / max(n - half, 1)
            delta = second_half_gap - first_half_gap
            if delta > 5:
                trend = "WORSENING"
            elif delta < -5:
                trend = "IMPROVING"
            else:
                trend = "STABLE"
        else:
            trend = "STABLE"

        return AttendanceAnalysisResult(
            avg_reported=round(avg_rep, 1),
            avg_observed=round(avg_obs, 1),
            persistent_gap_percent=round(gap_pct, 1),
            is_significant_discrepancy=gap_pct > self.DISCREPANCY_THRESHOLD,
            daily_gaps=daily_gaps,
            trend=trend,
        )
