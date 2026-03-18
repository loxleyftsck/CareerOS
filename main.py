import sys
import os
import time
from datetime import datetime
from storage import db
from engine.orchestrator import conductor
from engine.decision_framework import engine as crisp_engine

# --- Constant Setup ---
VERSION = "4.0.1"

def initialize_system():
    """Initial local-first system alignment."""
    print(f"[*] Initializing CareerOS [PATCH v{VERSION}]...")
    db.init_db()
    # Check if profile exists; if not, suggest upload
    profile = db.get_profile()
    if not profile:
        print("[!] No profile found in storage. Recommendation: Use '/profile/upload' API or update db manually.")
    else:
        print(f"[OK] CareerOS loaded for user: {profile.get('name', 'Unknown')}")

def heartbeat():
    """Main system lifecycle loop (local context)."""
    print(f"\n[>>>] CareerOS v{VERSION} Heartbeat Active.")
    print(f"[TIME] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. State Scan (Memory Sync)
    job_count = len(db.get_all_jobs())
    print(f"[STATE] Jobs in Cache: {job_count}")
    
    # 2. Crisp Decision Path
    # Decide if we need to expand search (matching)
    mode = crisp_engine.decide_matching(job_count)
    print(f"[DECISION] Current Search Strategy: {mode}")
    
    # 3. Execution (Simulated for v4.0.1)
    if mode == "A":
        print("[*] Strategy A: Local matching sufficient.")
    else:
        print("[!] Strategy B/C: Suggesting background scout (Phase 2).")

def main():
    initialize_system()
    
    try:
        while True:
            heartbeat()
            # Loop delay (e.g. 60s for local monitoring)
            print("\n" + "-"*40)
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n\n[<<<] CareerOS Shutting Down gracefully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
