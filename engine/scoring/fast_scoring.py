print(">>> DEBUG: importing fast_scoring.py")
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

import os
import sys
import json
import numpy as np
from typing import Dict, List, Optional

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from engine.decision_framework import engine as crisp_engine
from utils import logging_util
logger = logging_util.get_logger(__name__)
from storage import db

def get_skill_weight(skill: str, frequencies: Dict[str, int]) -> float:
    """Calculates weight based on demand frequency × importance factor."""
    s_low = skill.lower().strip()
    freq = frequencies.get(s_low, 1)
    
    import numpy as np
    print("🚀 DEBUG: np import successful")
    # Logarithmic scaling for frequency to avoid extreme outliers
    demand_weight = np.log1p(freq) / 5.0 # Max around 1.0-2.0 for 100+ jobs
    
    # Foundational skills have a higher baseline importance than hype skills
    factors = {
        "docker": 1.2, "kubernetes": 1.2, "sql": 1.2, "git": 1.1, "aws": 1.1,
        "python": 1.0, "fastapi": 1.0, "ci/cd": 1.1, "linux": 1.1,
    }
    importance = factors.get(s_low, 1.0)
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
    
    # -- Semantic Proximity --------------------------------------------------
    # If the user doesn't have the exact skill, we check if they have 
    # something 'very similar' (e.g. Flask if the job wants FastAPI)
    semantic_prox = 0.0
    remaining_j = j - u
    
    if remaining_j and user_emb is not None:
        # Simplified proximity: if the global job fit is high, 
        # we give a small 'domain competence' boost to missing keywords
        from utils.embedder import encode
        # In a production system, we'd embed every user skill individually,
        # but here we use a heuristics-based approach for performance.
        for missing in list(remaining_j)[:5]: # cap at 5 for speed
            # If the user has a long list of skills, 
            # we assume they have 'domain adjacency'
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
    
    # growth_score = 0.5 * (1 - skill_gap) + 0.5 * sample_confidence
    score = 0.5 * (1.0 - skill_gap) + 0.5 * sample_confidence
    return round(score * 100, 1)


def get_counterfactuals(profile: Dict, job: Dict) -> List[Dict]:
    """Simulate adding missing skills to see score impact."""
    u_skills = set(s.lower().strip() for s in profile.get("skills", []))
    j_skills = [s.lower().strip() for s in job.get("skills_required", [])]
    gaps = [s for s in j_skills if s not in u_skills]
    
    results = []
    # Base score for comparison (simplified internal call)
    base_fit = _keyword_overlap(list(u_skills), j_skills) * 100
    
    for skill in gaps[:3]: # Only top 3 gaps for performance
        sim_skills = list(u_skills | {skill})
        new_fit = _keyword_overlap(sim_skills, j_skills) * 100
        delta = new_fit - base_fit
        if delta > 0:
            results.append({
                "skill": skill,
                "delta": round(delta * 0.6, 1) # Weighted by 0.6 (job_fit_score contribution)
            })
    return sorted(results, key=lambda x: x["delta"], reverse=True)


def get_similar_roles(target_job: Dict, all_jobs: List[Dict], n: int = 3) -> List[Dict]:
    """Find top N similar roles based on skill vector overlap."""
    t_skills = set(s.lower().strip() for s in target_job.get("skills_required", []))
    if not t_skills:
        return []
        
    similarities = []
    for job in all_jobs:
        if job["id"] == target_job["id"]:
            continue
        j_skills = set(s.lower().strip() for s in job.get("skills_required", []))
        if not j_skills:
            continue
            
        # Jaccard/Overlap as proxy for cosine similarity if embeddings missing
        intersection = len(t_skills & j_skills)
        union = len(t_skills | j_skills)
        sim = intersection / union if union > 0 else 0
        
        similarities.append({
            "id": job["id"],
            "title": job["title"],
            "company": job["company"],
            "similarity": round(sim, 2)
        })
        
    return sorted(similarities, key=lambda x: x["similarity"], reverse=True)[:n]


# -- Coaching Layer (Gap-to-Action) ---------------------------------------------
SKILL_RESOURCES = {
    "kubernetes": "Learn K8s: Official Documentation, KodeKloud, or CKA certification track.",
    "docker": "Docker Mastery on Udemy or Official Get Started guide.",
    "python": "Fluent Python (Book) or Replit 100 Days of Code.",
    "aws": "AWS Certified Cloud Practitioner track or AWS Skill Builder.",
    "react": "React.dev documentation or Epic React by Kent C. Dodds.",
    "go": "A Tour of Go or 'Learn Go with Tests'.",
    "rust": "The Rust Programming Language (The Book).",
    "sql": "Mode Analytics SQL Tutorial or SQLZoo.",
    "postgresql": "Postgres Tutorial (postgresqltutorial.com).",
    "redis": "Redis University (free courses).",
    "kafka": "Confluent Developer courses.",
    "terraform": "HashiCorp Learn portal.",
}

from engine.scoring.pulse import calculate_real_pulse

def get_market_pulse() -> Dict:
    """Real Connection to Market Hiring Signals (derived from latest jobs)."""
    pulse = calculate_real_pulse()
    pulse["message"] = f"Market is currently at {pulse['global_hiring_index']*100:.0f}% capacity. "
    if pulse["ai_surge"] > 1.2:
        pulse["message"] += f"🔥 AI Surge Detected: {pulse['ai_surge']}x probability boost."
    return pulse

def get_gap_advice(gaps: List[str]) -> List[Dict]:
    """Translates missing skills into actionable learning paths."""
    advice = []
    for g in gaps:
        gl = g.lower().strip()
        resource = SKILL_RESOURCES.get(gl, "Explore community courses on Coursera/Udemy or official docs.")
        advice.append({
            "skill": g,
            "action": resource,
            "eta": "2-4 weeks focus"
        })
    return advice

# -- Decision Labels ----------------------------------------------------------
DECISION_LABELS = {
    "APPLY_NOW": "[!] APPLY NOW (High EV)",
    "CONSIDER":  "[*] CONSIDER (Mid EV)",
    "SKIP":      "[.] SKIP (Low EV / Risk)",
}

def get_decision(ev: float, p_interview: float, confidence: float) -> str:
    """Hierarchical decision flow."""
    if confidence < 0.4:
        return "CONSIDER"
    if ev >= 25: 
        return "APPLY_NOW"
    elif ev >= 10:
        return "CONSIDER"
    else:
        return "SKIP"

# -- Main API (Calibrated Decision Engine) -------------------------------------

@logging_util.time_it
def score_job(
    profile: Dict,
    job: Dict,
    profile_emb: Optional[np.ndarray] = None,
    job_emb: Optional[np.ndarray] = None,
    rl_boost: float = 0.0,
) -> Dict:
    """EV-based Decision Engine: EV = P(interview) * V(career)."""
    from engine.rl.custom_rl import engine as rl_engine
    
    u_skills = profile.get("skills", [])
    j_skills = job.get("skills_required", [])
    freqs = db.get_skill_frequencies()

    # 1. Calculate P(interview) - The Probability
    # Derived from technical fit + RL calibrated history
    skill_score = compute_skill_score(profile_emb, job_emb, u_skills, j_skills)
    exp_score = compute_exp_score(
        profile.get("experience_years", 0),
        job.get("experience_min", 0),
        job.get("experience_max", 5),
    )
    location_score = compute_location_score(
        profile.get("location_pref", "Jakarta"),
        job.get("location", ""),
    )
    
    # Determine Strategy based on Adaptive Crisp Framework
    job_count = db.count_jobs()
    strategy = crisp_engine.decide_matching(job_count, recall_score=1.0) 
    
    # Method C: Hybrid High-Precision Reranker simulation (O(N^2) pseudo-implementation)
    rerank_mult = 1.0
    if strategy == "C":
        # Simulate cross-encoder: roles with high baseline tech fit get precise recalibration boost
        if (0.6 * skill_score + 0.25 * exp_score) > 75:
              rerank_mult = 1.12
    
    # Base tech fit (0-100)
    tech_fit = ((0.6 * skill_score) + (0.25 * exp_score) + (0.15 * location_score)) * rerank_mult
    job["match_score"] = min(100, tech_fit) 
    job["strategy"] = strategy
    
    p_interview = rl_engine.get_interview_probability(job, profile)
    
    # 2. Calculate V(career) - The Value
    future_data = compute_future_readiness(u_skills, j_skills, freqs)
    future_score = future_data["score"]
    
    sample_size = db.count_similar_jobs(job.get("title", ""))
    sample_confidence = min(1.0, sample_size / 20.0)
    growth_score = compute_growth_score(u_skills, j_skills, sample_confidence)
    
    job["growth_score"] = growth_score
    job["future_score"] = future_score
    career_value = rl_engine.get_career_value(job, profile)
    
    # 3. Expected Value (EV) with Market Signals
    p_interview = rl_engine.get_interview_probability(job, profile)
    career_value = rl_engine.get_career_value(job, profile)
    saturation = rl_engine.get_saturation_penalty(job)
    
    # NEW: Market Signals (Competitor Density & Warm Path)
    # Warm Path (Referral) increases P significantly
    if job.get("is_warm_path", False):
        p_interview = min(0.95, p_interview * 3.0) 
        
    # Competitor Density Penalty (Saturation adjustment)
    # If 200+ applicants, apply exponential penalty to P
    applicants = job.get("applicant_count", 0)
    if applicants > 50:
        comp_penalty = np.exp(-0.005 * (applicants - 50)) 
        p_interview *= max(0.2, comp_penalty)

    # NEW: Market Pulse Integration
    pulse = get_market_pulse()
    p_interview *= pulse.get("global_hiring_index", 1.0) # Overall market tightening
    
    # AI Surge Boost: if role/title implies AI/ML
    title_low = job.get("title", "").lower()
    if any(k in title_low for k in ["ai", "ml", "learning", "data"]):
        p_interview = min(0.95, p_interview * pulse.get("ai_surge", 1.0))

    # Corrected EV: EV = P * V * Saturation
    ev = p_interview * career_value * saturation
    
    # 4. Confidence (Data Quality)
    profile_completeness = min(1.0, (len(u_skills) / 10.0 + (1 if profile.get("raw_cv_text") else 0.5)) / 2.0)
    confidence = (0.4 * profile_completeness) + (0.6 * sample_confidence)
    
    matched = get_matched(u_skills, j_skills)
    gaps = get_gaps(u_skills, j_skills)
    
    # Decision
    decision = get_decision(ev, p_interview, confidence)

    res_explanation = {
        "ev_reason": f"EV {ev:.1f} = {p_interview:.1%} prob * {career_value:.0f} value (Sat: {saturation:.1f})",
        "p_reason": "Calibrated based on technical fit and cluster interview history.",
        "v_reason": "Growth potential + Future trend alignment.",
        "saturation_alert": "HIGH" if saturation < 0.8 else "Low",
        "what_if": [f"If you learn {c['skill']} -> +{c['delta']}% match" for c in get_counterfactuals(profile, job)],
        "coaching": get_gap_advice(gaps)
    }

    # Flatten explanation for DB reasoning field
    reasoning = f"{decision}: {res_explanation['ev_reason']}. {res_explanation['p_reason']}. {res_explanation['v_reason']}."

    return {
        "job_id": job.get("id"),
        "title": job.get("title", ""),
        "company": job.get("company", ""),
        "ev": round(ev, 2),
        "p_interview": round(p_interview, 3),
        "career_value": round(career_value, 1),
        "match_score": tech_fit, 
        "confidence_score": round(confidence, 2),
        "confidence": round(confidence, 2), # Compatibility with current db.py
        "saturation_factor": round(saturation, 2),
        "breakdown": {
            "skill_match": skill_score,
            "exp_match": exp_score,
            "location_match": location_score,
            "future_readiness": future_score,
            "growth_pathway": growth_score,
            "growth_potential": growth_score # Compatibility with current db.py
        },
        "explanation": res_explanation,
        "reasoning": reasoning,
        "recommendation": decision,
        "decision": decision,
        "gaps": gaps,
        "matched_skills": matched,
        "requires_manual_review": ev >= 20 and confidence < 0.5
    }

@logging_util.time_it
def rank_jobs(
    profile: Dict,
    jobs: List[Dict],
    profile_emb: Optional[np.ndarray] = None,
    job_embeddings: Optional[Dict[int, np.ndarray]] = None,
    rl_boosts: Optional[Dict[int, float]] = None,
) -> List[Dict]:
    """Rank all jobs by Expected Value (EV)."""
    results = [
        score_job(
            profile, 
            job, 
            profile_emb, 
            job_embeddings.get(job.get("id")) if job_embeddings else None, 
            rl_boosts.get(job.get("id"), 0.0) if rl_boosts else 0.0
        )
        for job in jobs
    ]
    
    # Fairness + Similarity logic remains same but uses EV
    for r in results:
        target_job = next((j for j in jobs if j["id"] == r["job_id"]), None)
        if target_job:
            r["similar_roles"] = get_similar_roles(target_job, jobs, n=3)
            
    return sorted(results, key=lambda x: x["ev"], reverse=True)
