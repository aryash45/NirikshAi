"""
RiskEngine v2 — Explainable, weight-validated risk scoring.

ARCHITECTURE PRINCIPLE:
  Risk scores are computed from real data signals in the database.
  The engine is stateless, deterministic, and fully unit-testable.
  Every score comes with a per-factor breakdown so judges/users can see WHY.

Formula:
  risk_score = Σ(normalized_factor_score × factor_weight) × 100

Weight validation:
  Σ(weights) must equal 1.0 (within floating point tolerance).
  Weights must all be >= 0.
  Violation raises ValueError at startup — catches configuration errors early.

Response format (full explainability):
  {
    "risk_score": 73.4,
    "risk_level": "HIGH",
    "engine_version": "risk-v2",
    "calculated_at": "...",
    "weights": { ... },
    "factors": [
      {
        "name": "attendance_discrepancy",
        "raw_value": 0.31,
        "normalized_value": 0.78,
        "weight": 0.30,
        "contribution": 0.234,
        "human_label": "Attendance gap between MIS records and observed headcount"
      }
    ]
  }
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List


# ── Weight configuration ───────────────────────────────────────────────────

DEFAULT_WEIGHTS = {
    "attendance": 0.30,
    "camera":     0.25,
    "inspection": 0.20,
    "vc":         0.15,
    "compliance": 0.10,
}

# Normalisation parameters — documented so anyone can reproduce calculations
ATT_SCALE    = 4.0   # 1% gap → 4 pts on 0-100 scale (25% gap → 100)
INSP_SCALE   = 25.0  # each unresolved finding → 25 pts (4 findings → 100)
VC_SCALE     = 40.0  # each VC failure → 40 pts (3 failures → 100, capped)
COMP_SCALE   = 1.0   # 1 day overdue → 1 pt (100 days → 100, capped)


# ── Result schemas ─────────────────────────────────────────────────────────

@dataclass
class RiskFactor:
    name: str
    human_label: str
    raw_value: float          # Input value (gap %, days, count, etc.)
    normalized_value: float   # 0.0–1.0 after normalisation
    weight: float             # Configured weight for this factor
    contribution: float       # normalized_value × weight (pre-scaling)


@dataclass
class RiskResult:
    institution: str
    risk_score: float                # 0.0–100.0
    risk_level: str                  # LOW | MEDIUM | HIGH
    inspection_probability: int      # 1 | 4 | 7 (relative priority multiplier)
    factors: List[RiskFactor]
    engine_version: str = "risk-v2"
    calculated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    weights: Dict[str, float] = field(default_factory=dict)

    # Backward-compatible helpers
    @property
    def drivers(self) -> dict:
        """Legacy format for backward compatibility with existing schemas."""
        return {f.name: round(f.contribution * 100, 2) for f in self.factors}


# ── Engine ─────────────────────────────────────────────────────────────────

class RiskEngine:
    """
    Stateless, deterministic, explainable risk scorer.
    """

    def __init__(self, weights: Dict[str, float] | None = None):
        self.weights = weights or dict(DEFAULT_WEIGHTS)
        self._validate_weights()

    def _validate_weights(self) -> None:
        """
        Validates weight configuration at instantiation time.
        Fails loudly rather than silently computing wrong scores.
        """
        for name, w in self.weights.items():
            if w < 0:
                raise ValueError(f"Risk weight '{name}' = {w} is negative. All weights must be >= 0.")
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(
                f"Risk weights sum to {total:.4f}, not 1.0. "
                f"Weights: {self.weights}"
            )

    def _normalize(self, raw: float, scale: float, cap: float = 100.0) -> float:
        """Normalize a raw signal to 0.0–1.0."""
        return min(raw * scale, cap) / 100.0

    def calculate_risk(self, data: dict) -> RiskResult:
        """
        Args:
            data: {
                name                    : str,
                attendance_gap_pct      : float,   # MIS vs CCTV gap %
                camera_uptime_pct       : float,   # Camera availability %
                past_findings           : int,     # Unresolved adverse findings
                vc_failures             : int,     # Failed video verifications
                compliance_days_overdue : int,     # Days since compliance deadline
            }

        Returns:
            RiskResult with full per-factor breakdown.

        IMPORTANT: Attendance discrepancy ≠ proven fraud.
          High risk = "requires priority inspection"
          Only field inspection findings create confirmed findings.
        """
        name = data.get("name", "Unknown Institution")

        # ── Step 1: Compute normalised factor scores (0.0–1.0) ────────────
        att_pct      = float(data.get("attendance_gap_pct",      0))
        camera_pct   = float(data.get("camera_uptime_pct",    100))
        past_findings = int(data.get("past_findings",           0))
        vc_failures   = int(data.get("vc_failures",             0))
        comp_days     = int(data.get("compliance_days_overdue", 0))

        att_norm    = self._normalize(att_pct, ATT_SCALE)
        camera_norm = min(max(0.0, (100.0 - camera_pct)) / 100.0, 1.0)
        insp_norm   = self._normalize(float(past_findings), INSP_SCALE)
        vc_norm     = self._normalize(float(vc_failures), VC_SCALE)
        comp_norm   = self._normalize(float(comp_days), COMP_SCALE)

        # ── Step 2: Weighted contributions ────────────────────────────────
        factors = [
            RiskFactor(
                name="attendance_discrepancy",
                human_label="Attendance gap between MIS records and CCTV-observed headcount",
                raw_value=att_pct,
                normalized_value=round(att_norm, 4),
                weight=self.weights["attendance"],
                contribution=round(att_norm * self.weights["attendance"], 4),
            ),
            RiskFactor(
                name="camera_issues",
                human_label="CCTV camera downtime / low availability",
                raw_value=round(100.0 - camera_pct, 1),
                normalized_value=round(camera_norm, 4),
                weight=self.weights["camera"],
                contribution=round(camera_norm * self.weights["camera"], 4),
            ),
            RiskFactor(
                name="inspection_history",
                human_label="Unresolved adverse findings from previous inspections",
                raw_value=float(past_findings),
                normalized_value=round(insp_norm, 4),
                weight=self.weights["inspection"],
                contribution=round(insp_norm * self.weights["inspection"], 4),
            ),
            RiskFactor(
                name="vc_verification",
                human_label="Failed video-conference verification attempts",
                raw_value=float(vc_failures),
                normalized_value=round(vc_norm, 4),
                weight=self.weights["vc"],
                contribution=round(vc_norm * self.weights["vc"], 4),
            ),
            RiskFactor(
                name="compliance_overdue",
                human_label="Days past statutory compliance reporting deadline",
                raw_value=float(comp_days),
                normalized_value=round(comp_norm, 4),
                weight=self.weights["compliance"],
                contribution=round(comp_norm * self.weights["compliance"], 4),
            ),
        ]

        # ── Step 3: Aggregate ─────────────────────────────────────────────
        raw_total = sum(f.contribution for f in factors)   # 0.0–1.0
        total = round(min(raw_total * 100.0, 100.0), 1)   # 0.0–100.0

        # ── Step 4: Categorise ────────────────────────────────────────────
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
            factors=factors,
            weights=dict(self.weights),
        )
