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

# --- Engagement Rewards ---
REWARDS = {
    "click": 0.1,
    "apply": 1.0,
    "interview": 5.0, # + time bonus
    "offer": 15.0,
    "reject": -5.0,
    "skip": -2.0,
    "stale_penalty": -1.0
}

# --- Decision engine constants ---
MIN_SAMPLES_FOR_CALIBRATION = 5
DECAY_LAMBDA = 0.1 # For smooth exponential decay

ALPHA = 0.15
GAMMA = 0.5
EPSILON = 0.2 
KAPPA = 5.0    # Bayesian prior strength
SAT_LIMIT = 5  # Start penalizing after 5 pending apps

class CustomRL:
    """
    Refined RL engine for CareerOS.
    Features: Engagement-based rewards, Time-aware weighting, Skill-cluster boosting.
    """
    def __init__(self):
        self.weights_path = Path("storage/rl_weights.json")
        self.weights = self._load_weights()

    def _load_weights(self):
        if self.weights_path.exists():
            try: return json.loads(self.weights_path.read_text())
            except: pass
        return {
            "match_score": 0.5,
            "exp_fit": 0.2,
            "loc_fit": 0.15,
            "salary_fit": 0.15
        }

    def _save_weights(self):
        self.weights_path.write_text(json.dumps(self.weights))

    def get_cluster(self, job: Dict) -> str:
        """Deterministic skill clustering based on title keywords."""
        title = job.get("title", "").lower()
        if any(w in title for w in ["backend", "python", "go", "java", "node", "systems"]): return "backend"
        if any(w in title for w in ["frontend", "react", "javascript", "typescript", "ui", "ux"]): return "frontend"
        if any(w in title for w in ["data", "ml", "ai", "machine", "analytics"]): return "data"
        if any(w in title for w in ["devops", "sre", "cloud", "infrastructure", "platform"]): return "infrastructure"
        return "general"

    def get_state_key(self, job: Dict, profile: Dict) -> str:
        cluster = self.get_cluster(job)
        loc_match = "match" if profile.get("location_pref", "").lower() in job.get("location", "").lower() else "remote"
        return f"{cluster}:{loc_match}"

    def get_q_value(self, job: Dict, profile: Dict, action: str) -> float:
        """Encapsulated Q-value lookup."""
        state_key = self.get_state_key(job, profile)
        return db.get_q_value(f"{state_key}:{action}")

    def update_from_outcome(self, job_id: int, action: str):
        """High-level update called from UI/Pipeline."""
        job = db.get_job(job_id)
        profile = db.get_profile()
        if not job or not profile: return

        reward = REWARDS.get(action, 0.0)
        
        # 1. Update Career Memory (Persistence)
        try:
            days = 0
            fmt = "%Y-%m-%d %H:%M:%S"
            if job.get("applied_at") and job.get("created_at"):
                applied = datetime.strptime(job["applied_at"], fmt)
                if action == "interview" and job.get("interview_at"):
                    resp_time = datetime.strptime(job["interview_at"], fmt)
                    days = (resp_time - applied).days
            
            db.record_outcome({
                "job_id": job_id,
                "cluster_id": self.get_cluster(job),
                "stage_reached": action,
                "rejection_reason": "Market mismatch" if action == "reject" else None,
                "days_to_response": days,
                "feedback_tag": "high_ev" if job.get("ev", 0) > 20 else "normal"
            })
            logger.info(f"Career Memory updated for job {job_id}.")
        except Exception as e:
            logger.error(f"Failed to record outcome: {e}")

        # 2. Smooth exponential time-decay for interviews
        if action == "interview" and job.get("applied_at") and job.get("interview_at"):
            try:
                fmt = "%Y-%m-%d %H:%M:%S"
                applied = datetime.strptime(job["applied_at"], fmt)
                interviewed = datetime.strptime(job["interview_at"], fmt)
                days = max(0, (interviewed - applied).days)
                # Exponential decay: Bonus = 10 * exp(-lambda * days)
                time_bonus = 10.0 * np.exp(-DECAY_LAMBDA * days)
                reward += time_bonus
                logger.info(f"Time bonus (exp decay): +{time_bonus:.2f} for {days} days.")
            except Exception as e:
                logger.error(f"Time weighting failed: {e}")

        self._update_q(job, profile, action, reward)

    def get_interview_probability(self, job: Dict, profile: Dict) -> float:
        """Calibrates P(interview) using Bayesian smoothing (Career Memory Layer)."""
        cluster = self.get_cluster(job)
        
        # Determine strategy from Adaptive Crisp Framework
        history_count = db.count_outcomes()
        strategy = crisp_engine.decide_memory(history_count)
        job["memory_strategy"] = strategy
        
        # 1. Fetch historical evidence from Career Memory
        stats = db.get_cluster_stats(cluster)
        hits = stats["interviews"]
        total = stats["total_applies"]
        
        # 2. Bayesian Prior: Base match score as starting probability
        prior_p = job.get("match_score", 50) / 100.0 * 0.2 
        
        # 3. Bayesian Smooth: (Evidence + Kappa * Prior) / (Total + Kappa)
        # This uses LONG-TERM memory (outcomes) to ground the P.
        # If hits/total=0, it pulls P towards zero but anchored by Kappa.
        return (hits + KAPPA * prior_p) / (total + KAPPA)

    def get_saturation_penalty(self, job: Dict) -> float:
        """Prevents cluster fatigue: decays score if too many 'applied' jobs exist in cluster."""
        cluster = self.get_cluster(job)
        pending_jobs = db.get_all_jobs(status_filter='applied')
        cluster_pending = [j for j in pending_jobs if self.get_cluster(j) == cluster]
        
        n = len(cluster_pending)
        if n <= SAT_LIMIT:
            return 1.0
        
        # Smooth exponential decay after limit
        return np.exp(-0.3 * (n - SAT_LIMIT))

    def get_career_value(self, job: Dict, profile: Dict) -> float:
        """Estimates Value (V) based on Growth, Future Readiness, and Salary."""
        growth = job.get("growth_score", 0.5)
        future = job.get("future_score", 0.5)
        
        # Salary Utility: normalized relative to min request
        user_min = profile.get("salary_min", 0)
        job_min = job.get("salary_min", 0)
        salary_utility = 1.0
        if user_min > 0 and job_min > 0:
            salary_utility = min(1.5, job_min / user_min)
            
        # Career Value Formula: 40% Growth, 30% Future, 30% Salary
        return (growth * 0.4 + future * 0.3 + salary_utility * 0.3) * 100.0

    def _update_q(self, job: Dict, profile: Dict, action: str, reward: float):
        state_key = self.get_state_key(job, profile)
        full_key = f"{state_key}:{action}"
        
        current_q = db.get_q_value(full_key)
        new_q = current_q + ALPHA * (reward - current_q)
        db.set_q_value(full_key, round(new_q, 4))
        
        # Linear weight adjustment
        features = {
            "match_score": job.get("match_score", 50) / 100.0,
            "loc_fit": 1.0 if profile.get("location_pref", "").lower() in job.get("location", "").lower() else 0.5
        }
        for f in features:
            if f in self.weights:
                self.weights[f] += ALPHA * (reward - current_q) * features[f]
        self._save_weights()

    def recalibrate_daily(self):
        """Soft negative signal: penalty for applied jobs with no callback after 14 days."""
        logger.info("[#] RL Daily Recalibration...")
        applied_jobs = db.get_all_jobs(status_filter='applied')
        now = datetime.now()
        
        for job in applied_jobs:
            if not job.get("applied_at"): continue
            try:
                fmt = "%Y-%m-%d %H:%M:%S"
                applied = datetime.strptime(job["applied_at"], fmt)
                if (now - applied).days >= 14:
                    logger.warning(f"Stale Job Penalty: {job['title']} at {job['company']}")
                    self.update_from_outcome(job["id"], "stale_penalty")
            except: pass

    def get_cluster_boosts(self) -> Dict[str, float]:
        """Calculate interview rate per cluster as a boost factor."""
        # Simplified: scan feedback/jobs for (interviews/applies) ratio
        # Prototype: using Q-values of 'interview' action per state
        # Reality: we multiply score by (1 + interview_q_sum)
        boosts = {}
        for cluster in ["backend", "frontend", "data", "infrastructure", "general"]:
            q_val = db.get_q_value(f"{cluster}:match:interview")
            boosts[cluster] = max(1.0, 1.0 + q_val * 0.1)
        return boosts

    def choose_action(self, jobs: List[Dict], profile: Dict) -> List[Dict]:
        """Rank with 80/20 Exploit/Explore strategy using EV."""
        ranked = []
        
        for job in jobs:
            cluster = self.get_cluster(job)
            
            # 1. Base Calibrated EV (from scoring engine)
            base_ev = job.get("ev", 0)
            
            # 2. Exploitation: Add cluster historical boost
            # We use state-specific 'apply' likelihood
            q_apply = db.get_q_value(f"{self.get_state_key(job, profile)}:apply")
            exploit_score = base_ev * (1.0 + max(0, q_apply * 0.1))
            
            # 3. Guided Exploration: Boost jobs with low confidence (UCB-style)
            # This encourages applying to new niches to gather data
            conf = job.get("confidence_score", 1.0)
            explore_bonus = 5.0 * (1.0 - conf) if random.random() < EPSILON else 0.0
            
            job["rl_score"] = exploit_score + explore_bonus
            job["cluster"] = cluster
            ranked.append(job)
            
        return sorted(ranked, key=lambda x: x["rl_score"], reverse=True)

    def update(self, job: Dict, profile: Dict, action: str, reward: float = 0.0):
        """Compatibility layer for old update(job, profile, action, reward) calls."""
        # Use internal REWARDS if no specific reward is passed or override is needed
        final_reward = REWARDS.get(action, reward)
        self._update_q(job, profile, action, final_reward)

    def recalibrate_daily(self):
        """Re-scan all jobs and update stale application penalties."""
        now = datetime.now()
        fmt = "%Y-%m-%d %H:%M:%S"
        applied_jobs = db.get_all_jobs(status_filter='applied')
        
        for job in applied_jobs:
            if not job.get("applied_at"): continue
            try:
                dt = datetime.strptime(job["applied_at"], fmt)
                if (now - dt).days >= 14:
                    # Silence for 14 days in this cluster = soft negative signal
                    self.update_from_outcome(job["id"], "stale_penalty")
            except: continue

# Singleton instance
engine = CustomRL()
