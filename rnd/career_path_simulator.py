"""
rnd/career_path_simulator.py
Experiment 1: Simulate the EV impact of acquiring a new skill.

Usage:
    python rnd/career_path_simulator.py --skill "Kubernetes"
    python rnd/career_path_simulator.py --skill "React" --top 10
"""

import os
import sys
import argparse

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from storage import db
from engine.scoring.fast_scoring import score_job
from engine.scoring.prep_advisor import get_market_pulse


def simulate_skill_acquisition(new_skill: str, top_n: int = 15):
    """
    Computes the delta EV/match_score when adding `new_skill` to the user profile.
    Returns a ranked list of jobs that benefit most from this new skill.
    """
    profile = db.get_profile()
    if not profile:
        print("[!] No profile found. Please set up your profile first.")
        return []

    jobs = db.get_all_jobs()
    if not jobs:
        print("[!] No jobs in database.")
        return []

    # Context for performance
    pulse = get_market_pulse()
    context = {
        "freqs": db.get_skill_frequencies(),
        "job_count": db.count_jobs(),
        "pulse": pulse
    }

    simulated_profile = dict(profile)
    existing_skills = list(profile.get("skills", []))

    # Avoid duplicate
    new_skill_lower = new_skill.lower().strip()
    if new_skill_lower in {s.lower().strip() for s in existing_skills}:
        print(f"[i] You already have '{new_skill}' in your profile.")
        return []

    simulated_profile["skills"] = existing_skills + [new_skill]

    deltas = []
    for job in jobs[:top_n]:
        # Score without the new skill
        score_before = score_job(profile, job, context=context)
        ev_before = score_before["ev"]
        ms_before = score_before["match_score"]

        # Score WITH the new skill
        score_after = score_job(simulated_profile, job, context=context)
        ev_after = score_after["ev"]
        ms_after = score_after["match_score"]

        delta_ev = ev_after - ev_before
        delta_ms = ms_after - ms_before

        if delta_ev != 0 or delta_ms != 0:
            deltas.append({
                "title": job["title"],
                "company": job["company"],
                "ev_before": round(ev_before, 2),
                "ev_after": round(ev_after, 2),
                "delta_ev": round(delta_ev, 2),
                "ms_before": round(ms_before, 1),
                "ms_after": round(ms_after, 1),
                "delta_ms": round(delta_ms, 1),
            })

    return sorted(deltas, key=lambda x: x["delta_ms"], reverse=True)


def main():
    parser = argparse.ArgumentParser(description="CareerOS Career Path Simulator")
    parser.add_argument("--skill", required=True, help="Skill to simulate acquiring")
    parser.add_argument("--top", type=int, default=15, help="Number of jobs to analyze")
    args = parser.parse_args()

    print(f"\n[~] Simulating: What if you learned '{args.skill}'?\n")
    db.init_db()
    results = simulate_skill_acquisition(args.skill, args.top)

    if not results:
        print("[!] No EV delta found — that skill may not be relevant to current jobs.")
        return

    total_delta_ms = sum(r["delta_ms"] for r in results)
    avg_delta = total_delta_ms / len(results)

    print(f"{'Job Title':<35} {'Company':<20} {'Before':>7} {'After':>7} {'Δ MS':>7}")
    print("-" * 80)
    for r in results:
        marker = "🔥" if r["delta_ms"] > 5 else "↑" if r["delta_ms"] > 0 else "─"
        print(f"{r['title'][:34]:<35} {r['company'][:19]:<20} {r['ms_before']:>6}% {r['ms_after']:>6}% {marker}{r['delta_ms']:>+5}pts")

    print("-" * 80)
    print(f"\n✅ Summary: Learning '{args.skill}' would improve your match score by an average of +{avg_delta:.1f} pts across {len(results)} relevant jobs.\n")


if __name__ == "__main__":
    main()
