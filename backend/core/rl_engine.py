"""
rl_engine.py — CARL-DTN Reinforcement Learning Q-Table
Tracks user preferences across sessions via SQLite persistence.

State: (skill_bucket, location, seniority_level)
Action: recommend job in that category
Reward: +2 (applied), +1 (interested), 0 (reviewed), -1 (skipped)
Update: Q(s,a) ← Q(s,a) + α[R + γ·max Q(s',a') − Q(s,a)]
"""

from typing import Dict, List
try:
    from . import db # Relative import when part of package
except ImportError:
    import db # Fallback for standalone tests if parent not in path

from utils import logging_util
logger = logging_util.get_logger(__name__)

ALPHA = 0.15   # learning rate
GAMMA = 0.90   # discount factor
MAX_BOOST = 1.0

REWARD_MAP = {
    "apply": 2.0,
    "interest": 1.0,
    "review": 0.0,
    "skip": -1.0,
}


def _state_key(job: Dict, profile: Dict) -> str:
    """
    Derive a discrete state string from job + profile context.
    Matches at skill-category × seniority × location granularity.
    """
    # Skill bucket
    skills = [s.lower() for s in job.get("skills_required", [])]
    if any(k in skills for k in ("python", "fastapi", "django", "flask")):
        skill_cat = "backend"
    elif any(k in skills for k in ("react", "vue", "nextjs", "frontend", "typescript")):
        skill_cat = "frontend"
    elif any(k in skills for k in ("llm", "ml", "ai", "langchain", "embedding")):
        skill_cat = "ai_ml"
    elif any(k in skills for k in ("docker", "kubernetes", "mlops", "devops", "ci/cd")):
        skill_cat = "devops"
    elif any(k in skills for k in ("data", "sql", "spark", "airflow", "dbt")):
        skill_cat = "data"
    else:
        skill_cat = "general"

    # Seniority bucket
    exp_min = job.get("experience_min", 0)
    if exp_min <= 1:
        seniority = "junior"
    elif exp_min <= 4:
        seniority = "mid"
    else:
        seniority = "senior"

    # Location bucket
    loc = job.get("location", "").lower()
    if "remote" in loc or "wfh" in loc:
        loc_bucket = "remote"
    elif "jakarta" in loc:
        loc_bucket = "jakarta"
    else:
        loc_bucket = "other"

    return f"{skill_cat}:{seniority}:{loc_bucket}"


def get_rl_boosts(jobs: List[Dict], profile: Dict) -> Dict[int, float]:
    """
    For each job, compute a normalised RL boost [0, 1] from the Q-table.
    Used as extra signal in the growth_score dimension.
    """
    boosts = {}
    for job in jobs:
        key = _state_key(job, profile)
        q = db.get_q_value(key)
        # Normalise Q into [0, 1] boost — Q values should stay in [-4, 4] range
        boost = max(0.0, min(MAX_BOOST, (q + 4) / 8))
        boosts[job["id"]] = boost
    return boosts


def update(job: Dict, profile: Dict, action: str):
    """
    Receive a user action and update the Q-table accordingly.
    Returns the new Q value.
    """
    reward = REWARD_MAP.get(action, 0.0)
    key = _state_key(job, profile)
    current_q = db.get_q_value(key)
    # For MVP: no next-state lookahead (γ·max Q' ≈ 0 — single-step)
    new_q = current_q + ALPHA * (reward + GAMMA * 0 - current_q)
    db.set_q_value(key, round(new_q, 4))
    return new_q
