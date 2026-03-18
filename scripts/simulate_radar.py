import sys
import os
import random

# Use absolute path directly
PROJECT_ROOT = "d:/CareerOS"
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

try:
    from storage import db
    from engine.scoring import fast_scoring as antigravity
except Exception as e:
    print(f"[!] Initial import failed: {e}")
    # Provide more context if it's a typical Windows terminal error
    if "charmap" in str(e):
        print("[!] Tip: Windows terminal encoding issue detected. Try: 'chcp 65001' or 'set PYTHONIOENCODING=utf-8'")
    sys.exit(1)

def simulate_morning_radar():
    print(">>> Simulating Morning Radar Scan...")
    db.init_db()

    profile = db.get_profile()
    if not profile:
        db.save_profile({
            "name": "Antigravity Pro User",
            "experience_years": 5,
            "skills": ["Python", "FastAPI", "React", "Docker", "PostgreSQL"],
            "target_roles": ["AI Engineer", "Backend Developer"],
            "location_pref": "Remote"
        })
        profile = db.get_profile()
        print("[*] Created dummy profile.")

    # 1. GENERATE MOCK JOBS DIRECTLY
    print("[+] Generating Execution Simulation Data...")
    scouted_jobs = []
    
    mock_titles = ["AI Engineer", "Senior Backend Developer", "Python Systems Architect", "MLOps Lead"]
    mock_cos = ["Gojek", "Tokopedia", "Traveloka", "Grab", "Shopee", "Xendit"]
    
    for i in range(5):
        job = {
            "title": random.choice(mock_titles),
            "company": random.choice(mock_cos),
            "description": "Building high-scale autonomous execution engines using Python and RL.",
            "location": "Remote",
            "url": f"https://example.com/job/{random.randint(1000,9999)}",
            "source": "SimulationRadar",
            "applicant_count": random.randint(5, 50),
            "is_warm_path": True if i == 0 else False # Force one warm path
        }
        job_id = db.insert_job(job)
        job["id"] = job_id
        scouted_jobs.append(job)
        print(f"   [+] Scouted: {job['title']} @ {job['company']}")

    # 2. Analyze
    print(f"[*] Analyzing {len(scouted_jobs)} jobs...")
    ranked = antigravity.rank_jobs(profile, scouted_jobs)
    
    for res in ranked:
        db.save_analysis(res)
        if res.get("match_score", 0) > 70:
             db.add_notification(
                 "radar",
                 f"High-EV Alert: {res['title']}",
                 f"Target acquired at {res['company']} (Match: {res['match_score']:.1f}). Execution priority high.",
                 job_id=res["job_id"]
             )

    # 3. Report
    print("[*] Generating Weekly Mission Report...")
    from engine.reporters.weekly_mission import WeeklyMissionReporter
    reporter = WeeklyMissionReporter()
    path = reporter.generate_report()
    print(f"[OK] Mission Report Generated at {path}")
    
    db.add_notification(
         "system",
         "Weekly Mission Ready",
         "Your consolidated Career Mission for the week has been generated. Check the Dashboard.",
         job_id=None
    )
                 
    print("[OK] Radar simulation complete. Check your Dashboard!")

if __name__ == "__main__":
    simulate_morning_radar()
