from typing import List, Dict, Any, Optional
from storage import db
from engine.scoring import fast_scoring
from engine.rl.custom_rl import engine as rl_engine
from scraper.playwright_scraper import run_scraper, run_scraper_streaming
from utils import logging_util

logger = logging_util.get_logger("Orchestrator")

class Orchestrator:
    """
    Coordinates the pipeline: Cache -> Scraper -> Filter -> RL.
    Optimized for energy: skips heavy loads if cache is sufficient.
    """
    
    def __init__(self, use_cache: bool = True):
        self.use_cache = use_cache

    def scout_and_rank(self, profile: Dict, keyword: str, location: str = "Remote", limit: int = 5) -> List[Dict]:
        """
        Main execution flow.
        """
        logger.info(f"START scout_and_rank for '{keyword}'")
        
        # 1. Cache Check (Energy Optimization)
        energy_saved = False
        if self.use_cache:
            existing_jobs = db.get_all_jobs()
            relevant_cache = [
                j for j in existing_jobs 
                if keyword.lower() in j["title"].lower() or keyword.lower() in j["description"].lower()
            ]
            
            if len(relevant_cache) >= limit:
                logger.info(f"ENERGY SAVE: Found {len(relevant_cache)} jobs in cache. Skipping live scraper.")
                energy_saved = True
                results = self._process_jobs(relevant_cache[:limit * 2], profile)
                for r in results: r["_energy_saved"] = True
                return results

        # 2. Live Scraper (Fallback or insufficient cache)
        logger.info(f"PIPELINE: Triggering live boards for '{keyword}'...")
        live_jobs = run_scraper(keyword, location, limit)
        
        # 3. Store new jobs
        for job in live_jobs:
            db.insert_job(job)
            
        # 4. Filter & Rank
        all_relevant = db.get_all_jobs() # Get all including new ones
        results = self._process_jobs(all_relevant, profile, limit)
        for r in results: r["_energy_saved"] = energy_saved
        return results

    def scout_streaming(self, profile: Dict, keyword: str, location: str = "Remote", limit: int = 5):
        """Yield jobs one by one with preliminary scoring."""
        logger.info(f"START scout_streaming for '{keyword}'")
        
        # 1. Try Cache First
        if self.use_cache:
            existing_jobs = db.get_all_jobs()
            relevant_cache = [
                j for j in existing_jobs 
                if keyword.lower() in j["title"].lower() or keyword.lower() in j["description"].lower()
            ]
            if len(relevant_cache) >= limit:
                for job in relevant_cache[:limit]:
                    analysis = fast_scoring.score_job(profile, job)
                    job.update(analysis)
                    job["_energy_saved"] = True
                    yield job
                return

        # 2. Live Stream
        for raw_job in run_scraper_streaming(keyword, location, limit):
            # Save to DB
            job_id = db.insert_job(raw_job)
            raw_job["id"] = job_id
            
            # Fast score
            analysis = fast_scoring.score_job(profile, raw_job)
            raw_job.update(analysis)
            raw_job["_energy_saved"] = False
            
            # Note: Full RL re-ranking only works once we have a list.
            # For streaming, we yield fast-scored jobs immediately.
            yield raw_job

    def _process_jobs(self, jobs: List[Dict], profile: Dict, limit: int = 10) -> List[Dict]:
        """
        Two-tier processing:
        1. Fast Scoring (Linear sum)
        2. RL Re-ranking (Top-N only)
        """
        # Tier 1: Fast Scoring (Calculates match_score)
        scored_results = []
        for job in jobs:
            analysis = fast_scoring.score_job(profile, job)
            job.update(analysis) # merges scores into job dict
            scored_results.append(job)
            
        # Tier 2: RL Re-ranking & Calibrated Decision
        # Focus on top EV candidates. EV = P * V * Saturation
        top_candidates = sorted(scored_results, key=lambda x: x.get("ev", 0), reverse=True)[:limit*4]
        
        final_ranked = rl_engine.choose_action(top_candidates, profile)
        
        return final_ranked[:limit]

# Singleton instance
conductor = Orchestrator()
