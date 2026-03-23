import sys
import os

ROOT_DIR = os.getcwd()
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from engine.scoring import fast_scoring

def verify():
    profile = {"skills": ["Python", "Docker"]}
    jobs = [{"id": 1, "skills_required": ["Python", "Docker", "AWS"]}]
    
    # Python Baseline
    fast_scoring.RUST_AVAILABLE = False
    res_py = fast_scoring.rank_jobs(profile, jobs)[0]
    
    # Rust
    fast_scoring.RUST_AVAILABLE = True
    res_rust = fast_scoring.rank_jobs(profile, jobs)[0]
    
    print(f"PY: {res_py['ev']}, RUST: {res_rust['ev']}")
    if abs(res_py['ev'] - res_rust['ev']) < 0.1:
        print("VERIFICATION SUCCESS")
    else:
        print("VERIFICATION FAILURE")

if __name__ == "__main__":
    verify()
