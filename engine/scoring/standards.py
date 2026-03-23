"""
engine/scoring/standards.py — CareerOS Score Standardization Layer

Single source of truth for:
- Decision label thresholds (APPLY_NOW / CONSIDER / SKIP)
- Score quality tiers (Excellent / Good / Fair / Poor)
- Confidence quality levels
- EV minimum thresholds for each decision
"""

from typing import Dict, Tuple

# ── Decision Thresholds (EV-based) ──────────────────────────────────────────
# These are the canonical thresholds; all scoring modules must use this file.

EV_THRESHOLDS = {
    "APPLY_NOW": 25.0,   # High expected value — strong action signal
    "CONSIDER":  10.0,   # Moderate EV — worth investigating
    "SKIP":       0.0,   # Low EV — deprioritize
}

CONFIDENCE_THRESHOLDS = {
    "high":   0.70,   # Job desc is complete and specific
    "medium": 0.40,   # Some ambiguity in job description
    "low":    0.00,   # Vague listing — low data quality
}

# ── Match Score Tiers ────────────────────────────────────────────────────────

SCORE_TIERS = [
    (90, 100, "🟢 Excellent Match",   "Strong alignment across skills, experience, and location."),
    (70,  90, "🟡 Good Match",        "Solid fit with minor gaps that can be addressed."),
    (50,  70, "🟠 Fair Match",        "Partial alignment — notable gaps in key requirements."),
    (30,  50, "🔴 Weak Match",        "Significant misalignment — consider upskilling first."),
    ( 0,  30, "⚫ Poor Match",        "Very low overlap — unlikely to pass initial screening."),
]

# ── Breakdown Sub-Score Targets ──────────────────────────────────────────────
# These are the minimum "healthy" sub-scores per dimension.

DIMENSION_TARGETS = {
    "skill_match":    60.0,   # At least 60% skill overlap is considered healthy
    "exp_match":      70.0,   # Minimum 70% experience alignment
    "location_match": 70.0,   # Preferred location match
    "future_readiness": 50.0, # Market-weighted skill alignment
    "growth_pathway": 50.0,   # Growth opportunity score
}

# ── Public API ────────────────────────────────────────────────────────────────

def get_decision(ev: float, confidence: float) -> str:
    """Canonical decision function shared by all engine modules."""
    if confidence < CONFIDENCE_THRESHOLDS["medium"]:
        return "CONSIDER"  # Override to avoid high-confidence APPLY on vague jobs
    if ev >= EV_THRESHOLDS["APPLY_NOW"]:
        return "APPLY_NOW"
    elif ev >= EV_THRESHOLDS["CONSIDER"]:
        return "CONSIDER"
    return "SKIP"


def get_score_tier(score: float) -> Tuple[str, str]:
    """Returns (label, description) for a given match_score."""
    for low, high, label, desc in SCORE_TIERS:
        if low <= score <= high:
            return label, desc
    return "⚫ Unknown", "Score out of expected range."


def get_confidence_label(confidence_ratio: float) -> str:
    """Returns human-readable confidence level from a 0-1 ratio."""
    if confidence_ratio >= CONFIDENCE_THRESHOLDS["high"]:
        return "high"
    elif confidence_ratio >= CONFIDENCE_THRESHOLDS["medium"]:
        return "medium"
    return "low"


def get_dimension_health(breakdown: Dict) -> Dict[str, str]:
    """Evaluate each scoring dimension against minimum targets."""
    health = {}
    for dim, target in DIMENSION_TARGETS.items():
        actual = breakdown.get(dim, 0)
        if actual >= target:
            health[dim] = f"✅ {actual:.0f}% (target: {target:.0f}%)"
        else:
            health[dim] = f"⚠️  {actual:.0f}% (target: {target:.0f}%)"
    return health


def score_report(result: Dict) -> str:
    """Generate a compact standardized text report for a scored job."""
    tier_label, tier_desc = get_score_tier(result.get("match_score", 0))
    conf = get_confidence_label(result.get("confidence_score", 0))
    decision = result.get("decision", "SKIP")
    health = get_dimension_health(result.get("breakdown", {}))

    lines = [
        f"Job:        {result.get('title', '?')} @ {result.get('company', '?')}",
        f"Score:      {result.get('match_score', 0):.1f}% — {tier_label}",
        f"Confidence: {result.get('match_confidence', 0):.1f}% ({conf})",
        f"Decision:   {decision}  (EV={result.get('ev', 0):.2f})",
        f"Tier Note:  {tier_desc}",
        "Dimensions:",
    ]
    for dim, status in health.items():
        lines.append(f"  {dim:<20} {status}")

    return "\n".join(lines)
