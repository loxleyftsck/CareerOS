#!/usr/bin/env python3
"""
careeros_cli.py — CareerOS Command Line Interface (PATCH v4.0.14)

Usage:
    python careeros_cli.py scout --skill "Python" --location "Jakarta" --limit 20
    python careeros_cli.py report [--weekly]
    python careeros_cli.py profiles [--activate 2] [--delete 3]
    python careeros_cli.py simulate --skill "Kubernetes"
    python careeros_cli.py benchmark
"""

import argparse
import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from storage import db


def cmd_scout(args):
    from engine.orchestrator import conductor
    db.init_db()
    profile = db.get_profile()
    if not profile:
        print("[!] No profile set. Run 'python careeros_cli.py profiles' to check.")
        return
    print(f"\n🔭 Scouting '{args.skill}' in '{args.location}' (limit={args.limit})...\n")
    results = conductor.scout_and_rank(profile, args.skill, args.location, args.limit)
    for i, r in enumerate(results[:args.limit], 1):
        rec = r.get("recommendation", "?")
        ev = r.get("ev", 0)
        ms = r.get("match_score", 0)
        cal = r.get("calibrated_score", ms)
        print(f"  {i:>2}. [{rec:<18}] EV={ev:>6.2f} | Match={ms:>5.1f}% | Cal={cal:>5.1f}% | {r['title']} @ {r['company']}")
    print(f"\n✅ {len(results)} results returned.\n")


def cmd_report(args):
    from engine.reporting.reports import save_report
    db.init_db()
    period = "Weekly" if args.weekly else "Daily"
    path = save_report(period)
    print(f"\n📋 {period} report saved to: {path}\n")


def cmd_profiles(args):
    db.init_db()
    if args.activate:
        db.set_active_profile(args.activate)
        print(f"✅ Profile {args.activate} is now active.")
        return
    if args.delete:
        db.delete_profile(args.delete)
        print(f"🗑️  Profile {args.delete} deleted.")
        return
    profiles = db.get_all_profiles()
    if not profiles:
        print("[!] No profiles found.")
        return
    print(f"\n{'ID':<5} {'Name':<25} {'Skills':<10} {'Active'}")
    print("-" * 55)
    for p in profiles:
        active = "★ ACTIVE" if p.get("is_active") else ""
        skills_count = len(p.get("skills", []))
        print(f"  {p['id']:<5}{p['name']:<25}{skills_count:<10}{active}")
    print()


def cmd_simulate(args):
    from rnd.career_path_simulator import simulate_skill_acquisition
    db.init_db()
    print(f"\n[~] Simulating: What if you learned '{args.skill}'?\n")
    results = simulate_skill_acquisition(args.skill, top_n=15)
    if not results:
        print("[!] No impact found for this skill.")
        return
    avg = sum(r["delta_ms"] for r in results) / len(results)
    print(f"{'Title':<35} {'Before':>7} {'After':>7} {'Δ':>7}")
    print("-" * 60)
    for r in results:
        m = "🔥" if r["delta_ms"] > 5 else "↑"
        print(f"  {r['title'][:33]:<35} {r['ms_before']:>6}% {r['ms_after']:>6}% {m}{r['delta_ms']:>+5}pts")
    print(f"\n✅ Avg boost: +{avg:.1f} pts | Tip: Add this skill to your profile!\n")


def cmd_benchmark(args):
    from tests.accuracy_benchmark import run_accuracy_benchmark
    db.init_db()
    run_accuracy_benchmark()


def main():
    parser = argparse.ArgumentParser(prog="careeros", description="CareerOS CLI v4.0")
    sub = parser.add_subparsers(dest="cmd")

    # scout
    p_scout = sub.add_parser("scout", help="Scout & rank jobs by skill")
    p_scout.add_argument("--skill", required=True)
    p_scout.add_argument("--location", default="Remote")
    p_scout.add_argument("--limit", type=int, default=10)

    # report
    p_report = sub.add_parser("report", help="Generate daily/weekly report")
    p_report.add_argument("--weekly", action="store_true")

    # profiles
    p_prof = sub.add_parser("profiles", help="List or manage profiles")
    p_prof.add_argument("--activate", type=int)
    p_prof.add_argument("--delete", type=int)

    # simulate
    p_sim = sub.add_parser("simulate", help="Simulate skill acquisition impact")
    p_sim.add_argument("--skill", required=True)

    # benchmark
    sub.add_parser("benchmark", help="Run accuracy benchmark")

    args = parser.parse_args()
    cmds = {
        "scout": cmd_scout,
        "report": cmd_report,
        "profiles": cmd_profiles,
        "simulate": cmd_simulate,
        "benchmark": cmd_benchmark,
    }
    fn = cmds.get(args.cmd)
    if fn:
        fn(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
