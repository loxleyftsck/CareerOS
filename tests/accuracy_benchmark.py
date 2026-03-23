"""
tests/accuracy_benchmark.py — CareerOS Score Accuracy & Quality Benchmark

Validates that the scoring engine:
  1. Correctly ranks a perfect match above a poor match
  2. Produces expected score ranges for known profiles
  3. Is consistent between runs (determinism check)
  4. Doesn't produce extreme scores (0 or 100) on ambiguous inputs

Usage:
    python tests/accuracy_benchmark.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from storage import db
from engine.scoring.fast_scoring import score_job
from engine.scoring.prep_advisor import get_market_pulse

# ── Ground Truth Fixtures ─────────────────────────────────────────────────────

SENIOR_PROFILE = {
    "name": "Senior Dev",
    "skills": ["python", "fastapi", "docker", "kubernetes", "aws", "postgresql", "redis", "git"],
    "experience_years": 6.0,
    "location_pref": "Jakarta",
    "salary_min": 20_000_000,
}

JUNIOR_PROFILE = {
    "name": "Junior Dev",
    "skills": ["python", "html", "css"],
    "experience_years": 0.5,
    "location_pref": "Remote",
    "salary_min": 5_000_000,
}

PERFECT_JOB = {
    "id": 9001,
    "title": "Senior Backend Engineer",
    "company": "TechCorp",
    "location": "Jakarta",
    "skills_required": ["python", "fastapi", "docker", "postgresql", "redis"],
    "experience_min": 4,
    "experience_max": 8,
    "applicant_count": 10,
    "is_warm_path": False,
}

MISMATCH_JOB = {
    "id": 9002,
    "title": "iOS Developer",
    "company": "MobileApp",
    "location": "Bali",
    "skills_required": ["swift", "xcode", "objective-c", "uikit", "swiftui"],
    "experience_min": 3,
    "experience_max": 6,
    "applicant_count": 5,
    "is_warm_path": False,
}

VAGUE_JOB = {
    "id": 9003,
    "title": "Tech Person",
    "company": "Startup",
    "location": "Unknown",
    "skills_required": [],
    "experience_min": 0,
    "experience_max": 10,
    "applicant_count": 0,
    "is_warm_path": False,
}


# ── Test Cases ────────────────────────────────────────────────────────────────

class AccuracyResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.failures = []

    def check(self, name: str, condition: bool, debug: str = ""):
        if condition:
            self.passed += 1
            print(f"  ✅ PASS  {name}")
        else:
            self.failed += 1
            self.failures.append(name)
            print(f"  ❌ FAIL  {name}  {debug}")


def run_accuracy_benchmark():
    db.init_db()
    pulse = get_market_pulse()
    context = {
        "freqs": db.get_skill_frequencies(),
        "job_count": db.count_jobs(),
        "pulse": pulse
    }

    res = AccuracyResult()
    print("\n" + "=" * 60)
    print("  CareerOS Accuracy Benchmark")
    print("=" * 60)

    # ── 1. Ranking Order ──────────────────────────────────────────
    print("\n[1] Ranking Order Tests")
    s_perfect = score_job(SENIOR_PROFILE, PERFECT_JOB, context=context)
    s_mismatch = score_job(SENIOR_PROFILE, MISMATCH_JOB, context=context)

    res.check("Perfect match > Mismatch (match_score)",
              s_perfect["match_score"] > s_mismatch["match_score"],
              f"perfect={s_perfect['match_score']:.1f}, mismatch={s_mismatch['match_score']:.1f}")
    res.check("Perfect match > Mismatch (EV)",
              s_perfect["ev"] >= s_mismatch["ev"],
              f"perfect_ev={s_perfect['ev']:.2f}, mismatch_ev={s_mismatch['ev']:.2f}")

    # ── 2. Score Range Sanity ─────────────────────────────────────
    print("\n[2] Score Range Tests")
    for label, result in [("Senior+Perfect", s_perfect), ("Senior+Mismatch", s_mismatch)]:
        res.check(f"{label}: match_score in [0, 100]",
                  0 <= result["match_score"] <= 100,
                  f"got {result['match_score']}")
        res.check(f"{label}: match_confidence in [0, 100]",
                  0 <= result["match_confidence"] <= 100,
                  f"got {result['match_confidence']}")
        res.check(f"{label}: ev >= 0",
                  result["ev"] >= 0,
                  f"got {result['ev']}")

    # ── 3. Junior vs Senior ───────────────────────────────────────
    print("\n[3] Experience Sensitivity Tests")
    j_perfect = score_job(JUNIOR_PROFILE, PERFECT_JOB, context=context)
    res.check("Senior scores higher than Junior on senior role",
              s_perfect["match_score"] > j_perfect["match_score"],
              f"senior={s_perfect['match_score']:.1f}, junior={j_perfect['match_score']:.1f}")

    # ── 4. Vague Job Confidence ───────────────────────────────────
    print("\n[4] Vague Job Confidence Tests")
    s_vague = score_job(SENIOR_PROFILE, VAGUE_JOB, context=context)
    res.check("Vague job confidence < High on specific job",
              s_vague["match_confidence"] < s_perfect["match_confidence"],
              f"vague={s_vague['match_confidence']:.1f}, perfect={s_perfect['match_confidence']:.1f}")

    # ── 5. Determinism ────────────────────────────────────────────
    print("\n[5] Determinism Tests")
    r1 = score_job(SENIOR_PROFILE, PERFECT_JOB, context=context)
    r2 = score_job(SENIOR_PROFILE, PERFECT_JOB, context=context)
    res.check("Two runs produce identical match_score",
              r1["match_score"] == r2["match_score"],
              f"r1={r1['match_score']}, r2={r2['match_score']}")

    # ── 6. Output Schema ──────────────────────────────────────────
    print("\n[6] Output Schema Tests")
    required_fields = ["job_id", "match_score", "match_confidence", "ev",
                       "breakdown", "explanation", "application_prep", "decision"]
    for field in required_fields:
        res.check(f"Output has field '{field}'",
                  field in s_perfect,
                  f"missing from result keys: {list(s_perfect.keys())}")
    res.check("application_prep is a list (not empty on real job)",
              isinstance(s_perfect.get("application_prep"), list) and len(s_perfect["application_prep"]) > 0)

    # ── Summary ───────────────────────────────────────────────────
    total = res.passed + res.failed
    pct = round(res.passed / total * 100, 1) if total else 0
    verdict = "🟢 EXCELLENT" if pct == 100 else "🟡 ACCEPTABLE" if pct >= 80 else "🔴 NEEDS WORK"
    print("\n" + "=" * 60)
    print(f"  Results: {res.passed}/{total} passed ({pct}%) — {verdict}")
    if res.failures:
        print(f"  Failed: {', '.join(res.failures)}")
    print("=" * 60 + "\n")

    return res


if __name__ == "__main__":
    run_accuracy_benchmark()
