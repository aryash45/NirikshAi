"""
RiskEngine — Pure-Python risk scoring logic.
No database or HTTP dependencies; fully unit-testable.

Formula (transparent to judges):
  risk_score = Σ(normalized_factor × weight)

  Factor weights:
    attendance_gap_pct  → 30%
    camera_downtime     → 25%
    past_findings       → 20%
    vc_failures         → 15%
    compliance_overdue  → 10%
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class RiskResult:
    institution: str
    risk_score: float           # 0.0–100.0
    risk_level: str             # LOW | MEDIUM | HIGH
    inspection_probability: int # 1 | 4 | 7 (multiplier over baseline)
    drivers: dict[str, float]   # per-factor contributions


class RiskEngine:
    """
    Stateless, deterministic risk scorer.
    All inputs must be normalised to a 0–100 scale before weighting.
    """

    WEIGHTS = {
        "attendance": 0.30,
        "camera":     0.25,
        "inspection": 0.20,
        "vc":         0.15,
        "compliance": 0.10,
    }

    # Normalisation parameters
    ATT_SCALE    = 4.0   # 1 % gap → 4 pts (so 25 % → 100)
    INSP_SCALE   = 25.0  # each unresolved finding → 25 pts (4 findings → 100)
    VC_SCALE     = 40.0  # each VC failure → 40 pts (3 failures → 100, capped)

    def calculate_risk(self, data: dict) -> RiskResult:
        """
        Args:
            data: {
                name                    : str,
                attendance_gap_pct      : float,   # % discrepancy, 0-100
                camera_uptime_pct       : float,   # uptime %, 0-100
                past_findings           : int,
                vc_failures             : int,
                compliance_days_overdue : int,
            }
        """
        name = data.get("name", "Unknown")

        # ── Normalise each signal to 0-100 ──────────────────────────────────
        att_score    = min(data.get("attendance_gap_pct",      0) * self.ATT_SCALE,  100.0)
        camera_score = max(0.0, 100.0 - data.get("camera_uptime_pct", 100.0))
        insp_score   = min(data.get("past_findings",           0) * self.INSP_SCALE, 100.0)
        vc_score     = min(data.get("vc_failures",             0) * self.VC_SCALE,   100.0)
        comp_score   = min(data.get("compliance_days_overdue", 0) * 1.0,             100.0)

        # ── Weighted aggregation ─────────────────────────────────────────────
        weighted = {
            "attendance_discrepancy": round(att_score    * self.WEIGHTS["attendance"], 2),
            "camera_issues":          round(camera_score * self.WEIGHTS["camera"],     2),
            "inspection_history":     round(insp_score   * self.WEIGHTS["inspection"], 2),
            "vc_verification":        round(vc_score     * self.WEIGHTS["vc"],         2),
            "compliance_overdue":     round(comp_score   * self.WEIGHTS["compliance"], 2),
        }

        total = min(sum(weighted.values()), 100.0)
        total = round(total, 1)

        # ── Categorise ───────────────────────────────────────────────────────
        if total >= 60:
            level, prob = "HIGH",   7
        elif total >= 30:
            level, prob = "MEDIUM", 4
        else:
            level, prob = "LOW",    1

        return RiskResult(
            institution=name,
            risk_score=total,
            risk_level=level,
            inspection_probability=prob,
            drivers=weighted,
        )
