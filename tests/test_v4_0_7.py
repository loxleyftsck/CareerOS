import sys
import os
import time
import numpy as np

# Add project root to path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from engine.scoring import fast_scoring

def benchmark_rank_jobs():
    print("[*] Starting PATCH v4.0.7: Bulk Rust Acceleration Benchmark")
    
    profile = {
        "skills": ["Python", "Docker", "Kubernetes", "PostgreSQL", "FastAPI", "AWS", "Git", "Linux", "CI/CD", "Redis"],
        "experience_years": 5.0,
        "location_pref": "Jakarta"
    }
    
    # Create 100 mock jobs
    jobs = []
    for i in range(100):
        jobs.append({
            "id": i,
            "title": f"Software Engineer {i}",
            "company": "Tech Corp",
            "skills_required": ["Python", "FastAPI", "SQL", "Docker"] if i % 2 == 0 else ["Java", "Spring", "AWS"],
            "experience_min": 2,
            "experience_max": 5,
            "location": "Jakarta"
        })
    
    print(f"[*] Benchmarking rank_jobs with {len(jobs)} jobs...")

    # 1. Baseline: Python
    fast_scoring.RUST_AVAILABLE = False
    start_py = time.time()
    for _ in range(100): # 100 ranking operations (10,000 total job scorings)
        fast_scoring.rank_jobs(profile, jobs)
    end_py = time.time()
    py_time = end_py - start_py
    print(f"Python Time (100 ranks of 100 jobs): {py_time:.4f}s")
    
    # 2. Rust Acceleration (Bulk)
    fast_scoring.RUST_AVAILABLE = True
    start_rust = time.time()
    for _ in range(100):
        fast_scoring.rank_jobs(profile, jobs)
    end_rust = time.time()
    rust_time = end_rust - start_rust
    print(f"Rust Time (100 ranks of 100 jobs):   {rust_time:.4f}s")
    
    speedup = py_time / rust_time if rust_time > 0 else float('inf')
    print(f"\n[>>>] BULK SPEEDUP: {speedup:.2f}x")
    
    assert speedup > 1.2, f"Bulk Rust should be significantly faster! Got {speedup:.2f}x"
    print("[OK] Bulk performance benchmark successful.")

def verify_correctness():
    print("\n[*] Verifying correctness of bulk integration...")
    profile = {"skills": ["Python", "Docker"]}
    jobs = [{"id": 1, "skills_required": ["Python", "Docker", "AWS"]}]
    
    # Python Baseline
    fast_scoring.RUST_AVAILABLE = False
    res_py = fast_scoring.rank_jobs(profile, jobs)[0]
    
    # Rust
    fast_scoring.RUST_AVAILABLE = True
    res_rust = fast_scoring.rank_jobs(profile, jobs)[0]
    
    print(f"Python Score: {res_py['ev']}")
    print(f"Rust Score:   {res_rust['ev']}")
    
    assert abs(res_py['ev'] - res_rust['ev']) < 0.1, "Score mismatch in bulk integration!"
    print("[OK] Correctness verified.")

if __name__ == "__main__":
    verify_correctness()
    benchmark_rank_jobs()
