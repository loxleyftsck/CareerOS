import sys
import os
from datetime import datetime, timedelta

# Add root to sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from storage import db
from engine.rl.custom_rl import engine as rl_engine

def test_rl_v4():
    print("[*] Starting RL Engine v4.0.3 Verification...")
    db.init_db()
    
    # 1. Setup Mock Job & Profile
    profile = db.get_profile() or {"id": 1, "name": "Test User"}
    db.save_profile(profile)
    
    job_id = db.insert_job({
        "title": "Senior Python Backend Engineer",
        "company": "TestCorp",
        "status": "applied",
        "applied_at": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
    })
    
    # 2. Test Fast Interview Reward (< 3 days)
    print("[*] Simulating Fast Interview (2 days)...")
    db.update_job_status(job_id, "interview")
    # Manually set interview_at
    conn = db.get_conn()
    conn.execute("UPDATE jobs SET interview_at = ? WHERE id = ?", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), job_id))
    conn.commit()
    
    rl_engine.update_from_outcome(job_id, "interview")
    q_val = db.get_q_value("1:backend:interview")
    print(f"Q-Value for Fast Interview: {q_val}")
    # Reward was 20. Alpha 0.15. New Q should be 0 + 0.15*(20-0) = 3.0
    if q_val >= 3.0:
        print("[OK] Fast Interview reward applied.")
    
    # 3. Test No Response Penalty (> 14 days)
    print("[*] Simulating Stale Job Penalty (15 days)...")
    stale_job_id = db.insert_job({
        "title": "Legacy Java Developer",
        "company": "OldCorp",
        "status": "applied",
        "applied_at": (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d %H:%M:%S")
    })
    rl_engine.recalibrate_daily()
    
    q_penalty = db.get_q_value("1:backend:no_response_penalty")
    print(f"Q-Value for No Response: {q_penalty}")
    if q_penalty < 0:
        print("[OK] No Response penalty applied.")

if __name__ == "__main__":
    test_rl_v4()
