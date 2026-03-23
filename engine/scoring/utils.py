import numpy as np
import os
import sys
from typing import Dict, List, Optional

try:
    import career_rust
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False
    print(">>> WARNING: career_rust extension not found. Using Python fallback.")

# -- Industry Importance Factors ----------------------------------------------
IMPORTANCE_FACTORS = {
    "docker": 1.2, "kubernetes": 1.2, "sql": 1.2, "git": 1.1, "aws": 1.1,
    "python": 1.0, "fastapi": 1.0, "ci/cd": 1.1, "linux": 1.1,
}

# -- Location Score Map --------------------------------------------------------
LOCATION_SCORES = {
    "jakarta": 1.00, "dki jakarta": 1.00, "south jakarta": 1.00,
    "central jakarta": 1.00, "jakarta selatan": 1.00,
    "bandung": 0.75, "yogyakarta": 0.70, "surabaya": 0.72,
    "bali": 0.65, "semarang": 0.65, "medan": 0.62,
    "remote": 0.88, "wfh": 0.88, "work from home": 0.88, "hybrid": 0.82,
}

def get_skill_weight(skill: str, frequencies: Dict[str, int]) -> float:
    """Calculates weight based on demand frequency × importance factor."""
    s_low = skill.lower().strip()
    freq = frequencies.get(s_low, 1)
    
    # Logarithmic scaling for frequency to avoid extreme outliers
    demand_weight = np.log1p(freq) / 5.0 # Max around 1.0-2.0 for 100+ jobs
    importance = IMPORTANCE_FACTORS.get(s_low, 1.0)
    return demand_weight * importance


# -- Utilities -----------------------------------------------------------------

def _cosine(a: Optional[np.ndarray], b: Optional[np.ndarray]) -> float:
    if a is None or b is None:
        return 0.0
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def _keyword_overlap(user_skills: List[str], job_skills: List[str], user_emb: Optional[np.ndarray] = None) -> float:
    """Hybrid keyword + semantic proximity matching."""
    if not user_skills or not job_skills:
        return 0.0
    u = {s.lower().strip() for s in user_skills}
    j = {s.lower().strip() for s in job_skills}
    
    exact = len(u & j)
    
    # -- Rust Acceleration for Keyword Overlap ------------------------------
    if RUST_AVAILABLE:
        base_match_ratio = career_rust.fast_keyword_match(user_skills, job_skills)
        exact = base_match_ratio * len(j)
    
    # -- Semantic Proximity --------------------------------------------------
    semantic_prox = 0.0
    remaining_j = j - u
    
    if remaining_j and user_emb is not None:
        # Simplified proximity
        for missing in list(remaining_j)[:5]: 
            if len(u) > 15:
                semantic_prox += 0.3
            elif len(u) > 8:
                semantic_prox += 0.15

    matched = min(exact + semantic_prox, len(j))
    return matched / len(j)


def get_matched(u_skills: List[str], j_skills: List[str]) -> List[str]:
    """Returns list of skills that match between user and job."""
    u = {s.lower().strip() for s in u_skills}
    return [s for s in j_skills if s.lower().strip() in u]


def get_gaps(u_skills: List[str], j_skills: List[str]) -> List[str]:
    """Returns list of skills required by job but missing from user profile."""
    u = {s.lower().strip() for s in u_skills}
    return [s for s in j_skills if s.lower().strip() not in u]
