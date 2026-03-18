import random
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import numpy as np
from storage import db
from utils import logging_util
from engine.decision_framework import engine as crisp_engine

logger = logging_util.get_logger("CustomRL")

# --- v4.0 Engagement Rewards ---
REWARDS = {
    "click": 0.1,
    "apply": 1.0,
    "interview": 10.0,       # v4.0 Standard Interview
    "fast_interview": 20.0,  # v4.0 < 3 days bonus
    "reject": -5.0,
    "skip": -2.0,
    "no_response_penalty": -5.0 # v4.0 > 14 days
}

# --- Decision engine constants ---
ALPHA = 0.15
GAMMA = 0.5
EPSILON = 0.2 
SAT_LIMIT = 5 
DECAY_LAMBDA = 0.1

class CustomRL:
    """
    CareerOS v4.0 Reinforcement Learning Engine.
    State: (user_id, job_cluster)
    Actions: apply / skip / prioritize
    Rewards: interview (10), fast interview (20), penalty (-5)
    """
    def __init__(self):
        self.weights_path = Path("storage/rl_weights.json")
        self.weights = self._load_weights()

    def _load_weights(self):
        if self.weights_path.exists():
            try: return json.loads(self.weights_path.read_text())
            except: pass
        return {"match_score": 0.5, "exp_fit": 0.2, "loc_fit": 0.15, "salary_fit": 0.15}

    def _save_weights(self):
        self.weights_path.write_text(json.dumps(self.weights))

    def get_cluster(self, job: Dict) -> str:
        title = job.get("title", "").lower()
        if any(w in title for w in ["backend", "python", "go", "java", "node"]): return "backend"
        if any(w in title for w in ["frontend", "react", "javascript", "typescript", "ui"]): return "frontend"
        if any(w in title for w in ["data", "ml", "ai", "machine"]): return "data"
        if any(w in title for w in ["devops", "sre", "cloud", "infra"]): return "infrastructure"
        return "general"

    def get_state_key(self, job: Dict, profile: Dict) -> str:
        user_id = profile.get("id", 1)
        cluster = self.get_cluster(job)
        return f"{user_id}:{cluster}"

    def get_q_value(self, job: Dict, profile: Dict, action: str) -> float:
        state_key = self.get_state_key(job, profile)
        return db.get_q_value(f"{state_key}:{action}")

    def update_from_outcome(self, job_id: int, action: str):
        """v4.0 Outcome Logic."""
        job = db.get_job(job_id)
        profile = db.get_profile()
        if not job or not profile: return

        reward = REWARDS.get(action, 0.0)
        
        # 1. Fast Interview Check (< 3 days)
        if action == "interview" and job.get("applied_at") and job.get("interview_at"):
            try:
                fmt = "%Y-%m-%d %H:%M:%S"
                applied = datetime.strptime(job["applied_at"], fmt)
                interviewed = datetime.strptime(job["interview_at"], fmt)
                days = (interviewed - applied).days
                if days < 3:
                    reward = REWARDS["fast_interview"]
                    logger.info(f"FAST INTERVIEW detected ({days} days). High reward triggered.")
            except Exception as e:
                logger.error(f"Time calculation failed: {e}")

        # 2. Record to Memory
        db.record_outcome({
            "job_id": job_id,
            "cluster_id": self.get_cluster(job),
            "stage_reached": action,
            "rejection_reason": None,
            "days_to_response": 0,
            "feedback_tag": "v4.0_automated"
        })

        self._update_q(job, profile, action, reward)

    def _update_q(self, job: Dict, profile: Dict, action: str, reward: float):
        state_key = self.get_state_key(job, profile)
        full_key = f"{state_key}:{action}"
        
        current_q = db.get_q_value(full_key)
        new_q = current_q + ALPHA * (reward - current_q)
        db.set_q_value(full_key, round(new_q, 4))
        
        # Adjust feature weights based on reward
        match_score = job.get("match_score", 50) / 100.0
        if "match_score" in self.weights:
            self.weights["match_score"] += ALPHA * (reward - current_q) * match_score
        self._save_weights()

    def recalibrate_daily(self):
        """v4.0 No Response Penalty (> 14 days)."""
        logger.info("[#] RL v4.0 Daily Recalibration...")
        applied_jobs = db.get_all_jobs(status_filter='applied')
        now = datetime.now()
        
        for job in applied_jobs:
            if not job.get("applied_at"): continue
            try:
                fmt = "%Y-%m-%d %H:%M:%S"
                applied = datetime.strptime(job["applied_at"], fmt)
                if (now - applied).days >= 14:
                    logger.warning(f"No Response Penalty: {job['title']} at {job['company']}")
                    self.update_from_outcome(job["id"], "no_response_penalty")
            except: continue

    def choose_action(self, jobs: List[Dict], profile: Dict) -> List[Dict]:
        """v4.0 Exploit/Explore with RL Boosts."""
        ranked = []
        for job in jobs:
            base_ev = job.get("ev", 0)
            q_apply = self.get_q_value(job, profile, "apply")
            
            # RL Score = Base EV + (Q-Value * factor)
            job["rl_score"] = base_ev + (q_apply * 2.0)
            job["cluster"] = self.get_cluster(job)
            ranked.append(job)
            
        return sorted(ranked, key=lambda x: x.get("rl_score", 0), reverse=True)

    def update(self, job: Dict, profile: Dict, action: str, reward: float = 0.0):
        """Standard update wrapper."""
        final_reward = REWARDS.get(action, reward)
        self._update_q(job, profile, action, final_reward)

# Singleton instance
engine = CustomRL()
