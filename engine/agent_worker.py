import time
import schedule
import random
from storage import db
from engine.orchestrator import conductor
from engine.rl.custom_rl import engine as rl_engine
from engine.memory.memory_manager import MemoryManager
from utils import logging_util

logger = logging_util.get_logger("AgentWorker")

class CareerAgentWorker:
    """
    Autonomous background worker for CareerOS.
    Scouts jobs while the user sleeps. Updates RL expectations.
    """
    def __init__(self):
        self.mm = MemoryManager()
        
    def scout_all_targets(self):
        """Scout jobs with exploration vs exploitation and diversity guardrails."""
        profile = db.get_profile()
        if not profile:
            logger.warning("No profile found. Background scout aborted.")
            return

        targets = profile.get("target_roles", ["Software Engineer"])
        all_jobs = db.get_all_jobs(limit=500)
        
        # 1. Frequency Analysis for Diversity Guardrails
        role_counts = {}
        for j in all_jobs:
            title = j["title"].lower()
            for t in targets:
                if t.lower() in title:
                    role_counts[t] = role_counts.get(t, 0) + 1
        
        # 2. Exploration Logic: Pick a random 'niche' role occasionally
        if random.random() < 0.2: # 20% Exploration
            logger.info("[*] EXPLORATION MODE: Scouting for a diversified role...")
            targets = list(set(targets + ["Fullstack Developer", "DevOps Engineer", "Site Reliability Engineer"]))

        logger.info(f">>> STARTING AUTONOMOUS SCOUT for {len(targets)} roles.")
        
        scouted_urls = {j["url"] for j in all_jobs if j.get("url")}
        
        for role in targets:
            # 3. Penalty for Over-represented Roles
            current_count = role_counts.get(role, 0)
            if current_count > 50:
                logger.info(f"[!] DIVERSITY GUARDRAIL: Skipping '{role}' (Over-represented: {current_count})")
                continue

            try:
                # 4. Fetch Limit: strictly 5 per role per cycle
                results = conductor.scout_and_rank(profile, role, limit=5)
                
                # 5. De-duplication
                new_jobs = 0
                for res in results:
                    if res.get("url") not in scouted_urls:
                        # Job is already inserted by conductor.scout_and_rank if it fell back to scraper
                        # But we just log the unique count here
                        new_jobs += 1
                
                logger.info(f"[OK] Found {len(results)} matches for '{role}' ({new_jobs} unique)")
            except Exception as e:
                logger.error(f"[!] Scout for '{role}' failed: {e}")
            
            time.sleep(random.randint(5, 15))

    def morning_radar(self):
        """Proactive Push: Scan for high-EV matches every morning."""
        logger.info("[*] MORNING RADAR: Scanning for elite opportunities...")
        profile = db.get_profile()
        if not profile: return
        
        # Scout top 2 roles
        targets = profile.get("target_roles", [])[:2]
        for role in targets:
            results = conductor.scout_and_rank(profile, role, limit=10)
            high_ev = [r for r in results if r.get("ev", 0) >= 20]
            if high_ev:
                logger.warning(f"[!] RADAR ALERT: Found {len(high_ev)} High-EV opportunities for '{role}'!")
                for r in high_ev[:3]:
                    db.add_notification(
                        "radar",
                        f"Elite Match: {r['title']}",
                        f"High Expected Value opportunity at {r['company']} (EV: {r['ev']}). Apply before the trend shifts!",
                        r["job_id"]
                    )

    def perform_maintenance(self):
        """Keep the system lean and recalibrate RL daily."""
        logger.info("[#] RUNNING ENGINE MAINTENANCE...")
        self.mm.run_full_maintenance()
        rl_engine.recalibrate_daily()

    def run_cycle(self):
        """Continuous loop cycle."""
        logger.info("[>>>] CareerOS Agent Worker Cycle START.")
        # Morning Radar (Simulated trigger every 24h/cycle check)
        self.morning_radar()
        self.scout_all_targets()
        self.perform_maintenance()
        logger.info("[<<<] Cycle COMPLETE. Sleeping for 4 hours...")

def main():
    agent = CareerAgentWorker()
    
    # Run once at startup
    agent.run_cycle()
    
    # Schedule every 4 hours
    schedule.every(4).hours.do(agent.run_cycle)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
