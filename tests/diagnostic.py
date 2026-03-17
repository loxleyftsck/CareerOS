import sys
import os

# Ensure root is in path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from core import db, antigravity
from agents import clawbot, cv_parser
from utils import logging_util

logger = logging_util.get_logger("Diagnostic")

def run_diagnostics():
    print("--- CareerOS System Diagnostics ---")
    
    # 1. DB Check
    try:
        db.init_db()
        jobs = db.get_all_jobs()
        print(f"[✔] Database initialized. Jobs in DB: {len(jobs)}")
    except Exception as e:
        print(f"[✖] Database ERROR: {e}")

    # 2. Matcher Check
    try:
        dummy_profile = {"skills": ["Python"], "experience_years": 2}
        dummy_job = {"id": 1, "title": "Dev", "skills_required": ["Python"]}
        result = antigravity.score_job(dummy_profile, dummy_job)
        print(f"[✔] Antigravity Matcher: OK (Score: {result['match_score']}%)")
    except Exception as e:
        print(f"[✖] Matcher ERROR: {e}")

    # 3. CV Parser Check
    try:
        # Just check if we can call the parser function with empty data
        cv_parser.parse_cv("")
        print("[✔] CV Parser: OK (Logic loaded)")
    except Exception as e:
        print(f"[✖] CV Parser ERROR: {e}")

    # 4. Scraper Logic Check
    try:
        jobs = clawbot.MOCK_JOBS
        if len(jobs) > 0:
            print(f"[✔] Clawbot/Scraper: OK (Mock data available: {len(jobs)})")
        else:
            print("[✖] Clawbot ERROR: Mock data is empty")
    except Exception as e:
        print(f"[✖] Scraper ERROR: {e}")

if __name__ == "__main__":
    run_diagnostics()
