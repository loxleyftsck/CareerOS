import numpy as np
from typing import Dict, List, Optional
from engine.scoring.utils import _cosine, _keyword_overlap, get_skill_weight, LOCATION_SCORES

# -- Scoring Dimensions --------------------------------------------------------

def compute_skill_score(
    user_emb: Optional[np.ndarray],
    job_emb: Optional[np.ndarray],
    user_skills: List[str],
    job_skills: List[str],
) -> float:
    """50% weight: semantic similarity + proximity overlap hybrid."""
    semantic = (_cosine(user_emb, job_emb) + 1) / 2  # shift [-1,1] → [0,1]
    keyword = _keyword_overlap(user_skills, job_skills, user_emb)
    
    if user_emb is not None and job_emb is not None:
        score = 0.60 * semantic + 0.40 * keyword
    else:
        score = keyword
    return round(score * 100, 1)


def compute_exp_score(
    user_exp: float,
    job_exp_min: float,
    job_exp_max: float,
) -> float:
    """20% weight: experience fit — penalize over/under qualification."""
    if job_exp_max <= 0:
        job_exp_max = job_exp_min + 2
    if job_exp_min <= user_exp <= job_exp_max:
        return 100.0
    elif user_exp < job_exp_min:
        gap = job_exp_min - user_exp
        return round(max(0.0, 100.0 - gap * 22), 1)
    else:
        gap = user_exp - job_exp_max
        return round(max(60.0, 100.0 - gap * 8), 1)


def compute_location_score(user_pref: str, job_location: str) -> float:
    """15% weight: location tier match."""
    jl = job_location.lower().strip()
    up = user_pref.lower().strip()
    # Remote is always a win
    if any(k in jl for k in ("remote", "wfh", "work from home")):
        return 88.0
    if up in jl or jl in up:
        return 100.0
    for key, val in LOCATION_SCORES.items():
        if key in jl:
            return round(val * 100, 1)
    return 40.0  # unknown location


def compute_future_readiness(
    user_skills: List[str],
    job_skills: List[str],
    all_frequencies: Dict[str, int]
) -> Dict:
    """Calculates Future Readiness based on trend alignment and demand."""
    u = {s.lower().strip() for s in user_skills}
    j = {s.lower().strip() for s in job_skills}
    
    weights = {s: get_skill_weight(s, all_frequencies) for s in j}
    total_weight = sum(weights.values()) or 1.0
    user_match_weight = sum(weights[s] for s in j if s in u)
    score = (user_match_weight / total_weight) * 100
    
    return {
        "score": round(score, 1),
        "weights": weights
    }


def compute_growth_score(
    user_skills: List[str],
    job_skills: List[str],
    sample_confidence: float
) -> float:
    """Calculates Growth Pathway score (15% weight)."""
    u = {s.lower().strip() for s in user_skills}
    j = {s.lower().strip() for s in job_skills}
    if not j:
        return 0.0
    
    matched_count = len([s for s in j if s in u])
    skill_gap = 1.0 - (matched_count / len(j))
    
    score = 0.5 * (1.0 - skill_gap) + 0.5 * sample_confidence
    return round(score * 100, 1)
