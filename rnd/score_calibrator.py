"""
rnd/score_calibrator.py
Experiment 5: Confidence-Weighted Score Calibration.

Re-calibrates match_score when match_confidence is low,
preventing misleading "APPLY NOW" recommendations on vague job descriptions.
"""

from typing import Dict

def calibrate_score(match_score: float, match_confidence: float) -> float:
    """
    Shrinks the match_score toward 50 when confidence is low.
    
    Formula:
        calibrated = match_score * (0.5 + 0.5 * confidence/100)
        + 50 * (1 - (0.5 + 0.5 * confidence/100))
    
    At confidence=100%: calibrated = match_score (no change)
    At confidence=50%:  calibrated = 75% of match_score + 12.5 (mild center pull)
    At confidence=0%:   calibrated = 50 (full center pull, maximum uncertainty)
    """
    conf_norm = min(max(match_confidence / 100.0, 0.0), 1.0)
    weight = 0.5 + 0.5 * conf_norm
    calibrated = match_score * weight + 50.0 * (1.0 - weight)
    return round(calibrated, 1)


def apply_calibration(result: Dict) -> Dict:
    """
    Applies confidence-weighted calibration to a score_job result dict.
    Adds 'calibrated_score' field without modifying the original match_score.
    """
    ms = result.get("match_score", 0)
    mc = result.get("match_confidence", 50)  # Default 50% if missing
    
    result["calibrated_score"] = calibrate_score(ms, mc)
    result["calibration_delta"] = round(result["calibrated_score"] - ms, 1)
    return result


# -- Smoke test ---------------------------------------------------------------
if __name__ == "__main__":
    test_cases = [
        # (match_score, match_confidence, expected behavior)
        (90, 100, "Score unchanged — confident job description"),
        (90, 50,  "Score pulled toward center — vague job description"),
        (90, 10,  "Score heavily pulled to ~50 — very vague job description"),
        (40, 100, "Low score, high confidence — stays low"),
        (40, 20,  "Low score, low confidence — gets pulled toward 50 (uncertainty)")
    ]

    print(f"\n{'Original':>10} {'Confidence':>12} {'Calibrated':>12} {'Delta':>8}  Notes")
    print("-" * 75)
    for ms, mc, note in test_cases:
        cal = calibrate_score(ms, mc)
        delta = round(cal - ms, 1)
        sign = "+" if delta >= 0 else ""
        print(f"{ms:>10}%  {mc:>10}%  {cal:>11}%  {sign}{delta:>+6}pt  {note}")
    print()
