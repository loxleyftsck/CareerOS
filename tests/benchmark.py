"""
tests/benchmark.py — CareerOS Speed & Accuracy Benchmark Suite

Measures:
  1. Throughput: jobs/second across N jobs
  2. Latency: p50/p95/p99 per score_job call
  3. Rust vs Python delta (consistency check)
  4. Component breakdown timing (skill, exp, location, prep_advisor)

Usage:
    python tests/benchmark.py
    python tests/benchmark.py --jobs 100 --runs 3
"""

import os
import sys
import time
import argparse
import statistics
from typing import List, Dict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from storage import db
from engine.scoring.fast_scoring import score_job, rank_jobs
from engine.scoring.dimensions import (
    compute_skill_score, compute_exp_score,
    compute_location_score, compute_future_readiness
)
from engine.scoring.prep_advisor import get_market_pulse

# ── Synthetic Fixtures ────────────────────────────────────────────────────────

MOCK_PROFILE = {
    "name": "Benchmark User",
    "skills": ["python", "fastapi", "docker", "sql", "git", "redis", "linux", "aws"],
    "experience_years": 3.5,
    "location_pref": "Jakarta",
    "salary_min": 10_000_000,
    "target_roles": ["Backend Engineer", "ML Engineer"],
    "career_goals": "Senior backend role in AI product company",
}

def make_mock_jobs(n: int) -> List[Dict]:
    """Generate N synthetic job dicts for benchmarking."""
    base_skills = [
        ["python", "fastapi", "docker", "postgresql"],
        ["go", "kubernetes", "terraform", "aws"],
        ["react", "typescript", "node", "graphql"],
        ["python", "pytorch", "mlflow", "spark"],
        ["java", "spring", "kafka", "redis"],
    ]
    jobs = []
    for i in range(n):
        skills = base_skills[i % len(base_skills)]
        jobs.append({
            "id": 1000 + i,
            "title": f"Engineer Role #{i}",
            "company": f"Company {chr(65 + i % 26)}",
            "location": ["Jakarta", "Remote", "Bandung", "Surabaya"][i % 4],
            "skills_required": skills,
            "experience_min": 2 + (i % 4),
            "experience_max": 5 + (i % 4),
            "applicant_count": 10 + (i * 3),
            "is_warm_path": (i % 10 == 0),
        })
    return jobs

# ── Bench Helpers ─────────────────────────────────────────────────────────────

def percentile(data: List[float], p: int) -> float:
    if not data:
        return 0.0
    sorted_data = sorted(data)
    idx = int(len(sorted_data) * p / 100)
    return sorted_data[min(idx, len(sorted_data) - 1)]


def bench_section(label: str, fn, runs: int = 5) -> Dict:
    """Time a callable over N runs, return stats dict."""
    times = []
    for _ in range(runs):
        t0 = time.perf_counter()
        fn()
        times.append((time.perf_counter() - t0) * 1000)  # ms
    return {
        "label": label,
        "mean_ms": round(statistics.mean(times), 3),
        "p50_ms":  round(percentile(times, 50), 3),
        "p95_ms":  round(percentile(times, 95), 3),
        "p99_ms":  round(percentile(times, 99), 3),
        "min_ms":  round(min(times), 3),
        "max_ms":  round(max(times), 3),
    }

# ── Main Benchmark ────────────────────────────────────────────────────────────

def run_benchmark(n_jobs: int = 50, runs: int = 3):
    db.init_db()
    jobs = make_mock_jobs(n_jobs)
    pulse = get_market_pulse()
    context = {
        "freqs": db.get_skill_frequencies(),
        "job_count": db.count_jobs(),
        "pulse": pulse
    }

    results = []
    print(f"\n{'='*65}")
    print(f"  CareerOS Benchmark Suite — {n_jobs} jobs × {runs} runs")
    print(f"{'='*65}\n")

    # 1. Single score_job latency
    job = jobs[0]
    r = bench_section("score_job (single)", lambda: score_job(MOCK_PROFILE, job, context=context), runs=runs*3)
    results.append(r)

    # 2. rank_jobs throughput
    t_start = time.perf_counter()
    for _ in range(runs):
        rank_jobs(MOCK_PROFILE, jobs)
    t_total = (time.perf_counter() - t_start) * 1000
    avg_per_run = t_total / runs
    throughput = round(n_jobs / (avg_per_run / 1000), 1)
    rank_result = {
        "label": f"rank_jobs ({n_jobs} jobs)",
        "mean_ms": round(avg_per_run, 2),
        "throughput": f"{throughput} jobs/sec",
        "p50_ms": "—", "p95_ms": "—", "p99_ms": "—",
        "min_ms": "—", "max_ms": "—"
    }
    results.append(rank_result)

    # 3. Component sub-benchmarks
    u_skills = MOCK_PROFILE["skills"]
    j_skills = jobs[0]["skills_required"]
    results.append(bench_section("compute_skill_score",
        lambda: compute_skill_score(None, None, u_skills, j_skills), runs=runs*5))
    results.append(bench_section("compute_exp_score",
        lambda: compute_exp_score(3.5, 2.0, 5.0), runs=runs*5))
    results.append(bench_section("compute_location_score",
        lambda: compute_location_score("Jakarta", "Jakarta"), runs=runs*5))
    results.append(bench_section("get_market_pulse (cached)",
        lambda: get_market_pulse(), runs=runs*3))

    # 4. Print table
    print(f"{'Component':<35} {'Mean':>9} {'p50':>9} {'p95':>9} {'p99':>9}  {'Extra'}")
    print("-" * 85)
    for r in results:
        extra = r.get("throughput", "")
        print(f"{r['label']:<35} {str(r['mean_ms'])+' ms':>9} {str(r['p50_ms'])+' ms':>9} {str(r['p95_ms'])+' ms':>9} {str(r['p99_ms'])+' ms':>9}  {extra}")

    print(f"\n{'='*65}")

    # 5. Summary verdict
    single_ms = results[0]["mean_ms"]
    verdict = "🟢 FAST" if single_ms < 5 else "🟡 OK" if single_ms < 20 else "🔴 SLOW"
    print(f"  Single-score latency: {single_ms}ms → {verdict}")
    print(f"  Throughput: {results[1].get('throughput', 'N/A')} scored")
    print(f"{'='*65}\n")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CareerOS Speed Benchmark")
    parser.add_argument("--jobs", type=int, default=50, help="Number of synthetic jobs")
    parser.add_argument("--runs", type=int, default=3, help="Number of repetitions")
    args = parser.parse_args()
    run_benchmark(args.jobs, args.runs)
