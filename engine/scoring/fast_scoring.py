import os
import sys
import numpy as np
from typing import Dict, List, Optional

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from engine.decision_framework import engine as crisp_engine
from utils import logging_util
from storage import db

# Import from refactored modules
from engine.scoring.utils import RUST_AVAILABLE, get_matched, get_gaps
from engine.scoring.dimensions import (
    compute_skill_score,
    compute_exp_score,
    compute_location_score,
    compute_future_readiness,
    compute_growth_score,
)
from engine.scoring.prep_advisor import (
    get_market_pulse,
    get_gap_advice,
    get_counterfactuals,
    get_similar_roles,
)

if RUST_AVAILABLE:
    import career_rust

logger = logging_util.get_logger(__name__)

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
    precalculated_rust_ratio: Optional[float] = None,
    context: Optional[Dict] = None,
) -> Dict:
    """EV-based Decision Engine: EV = P(interview) * V(career)."""
    
    u_skills = profile.get("skills", [])
    j_skills = job.get("skills_required", [])
    
    # Use context or fetch from DB
    if context:
        freqs = context.get("freqs", {})
        job_count = context.get("job_count", 0)
        pulse = context.get("pulse", {})
    else:
        freqs = db.get_skill_frequencies()
        job_count = db.count_jobs()
        pulse = get_market_pulse()

    # 1. Calculate Technical Fit (The Probability core)
    if precalculated_rust_ratio is not None:
        keyword_score = precalculated_rust_ratio
        if profile_emb is not None and job_emb is not None:
            # We defer to _cosine inside utils if we needed it directly, but here we just compute semantic inline
            # Or better, we should have imported _cosine. Since we didn't, we approximate:
            from engine.scoring.utils import _cosine
            semantic = (_cosine(profile_emb, job_emb) + 1) / 2
            skill_score = round((0.6 * semantic + 0.4 * keyword_score) * 100, 1)
        else:
            skill_score = round(keyword_score * 100, 1)
    else:
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
    strategy = crisp_engine.decide_matching(job_count, recall_score=1.0) 
    
    # Method C: Hybrid High-Precision Reranker simulation
    rerank_mult = 1.0
    if strategy == "C":
        if (0.6 * skill_score + 0.25 * exp_score) > 75:
              rerank_mult = 1.12
    
    # Base tech fit (0-100)
    tech_fit = ((0.6 * skill_score) + (0.25 * exp_score) + (0.15 * location_score)) * rerank_mult
    job["match_score"] = min(100, tech_fit) 
    job["strategy"] = strategy
    
    # 2. Market Signals & Probabilities
    future_data = compute_future_readiness(u_skills, j_skills, freqs)
    future_score = future_data["score"]
    
    sample_size = db.count_similar_jobs(job.get("title", ""))
    sample_confidence = min(1.0, sample_size / 20.0)
    growth_score = compute_growth_score(u_skills, j_skills, sample_confidence)
    
    job["growth_score"] = growth_score
    job["future_score"] = future_score
    
    p_interview = tech_fit / 100.0
    career_value = 100.0 
    saturation = 1.0     
    
    # Competitor Density Penalty & Warm Paths
    if job.get("is_warm_path", False):
        p_interview = min(0.95, p_interview * 3.0) 
        
    applicants = job.get("applicant_count", 0)
    if applicants > 50:
        comp_penalty = np.exp(-0.005 * (applicants - 50)) 
        p_interview *= max(0.2, comp_penalty)

    p_interview *= pulse.get("global_hiring_index", 1.0)
    
    title_low = job.get("title", "").lower()
    if any(k in title_low for k in ["ai", "ml", "learning", "data"]):
        p_interview = min(0.95, p_interview * pulse.get("ai_surge", 1.0))

    ev = p_interview * career_value * saturation
    
    # 4. Confidence (Data Quality)
    profile_completeness = min(1.0, (len(u_skills) / 10.0 + (1 if profile.get("raw_cv_text") else 0.5)) / 2.0)
    # Job specificity: vague jobs (no skills listed) have much lower confidence
    job_specificity = min(1.0, len(j_skills) / 5.0) if j_skills else 0.3
    confidence = (0.3 * profile_completeness) + (0.4 * sample_confidence) + (0.3 * job_specificity)
    
    matched = get_matched(u_skills, j_skills)
    gaps = get_gaps(u_skills, j_skills)
    
    # Decision
    decision = get_decision(ev, p_interview, confidence)

    # -- Generate Structured Application Prep --
    application_prep = []
    
    if matched:
        top_matches = ", ".join(matched[:3])
        application_prep.append({
            "type": "cv",
            "action": f"Highlight your experience in {top_matches} prominently in your resume summary and recent roles."
        })
    else:
        application_prep.append({
            "type": "cv",
            "action": "Focus on transferable skills and core competencies, as direct keyword matches are low."
        })
        
    if gaps:
        top_gaps = ", ".join(gaps[:2])
        application_prep.append({
            "type": "gap",
            "action": f"Prepare an explanation or learning plan for missing experience in {top_gaps}."
        })
        
    if confidence < 0.4:
         application_prep.append({
            "type": "strategy",
            "action": "Job description is vague. Prepare clarifying questions about the day-to-day tech stack for the interview."
        })
    elif exp_score < 70:
        application_prep.append({
            "type": "strategy",
            "action": "Acknowledge the experience gap but emphasize rapid learning ability and impactful past projects."
        })
    else:
        application_prep.append({
            "type": "strategy",
            "action": "Emphasize your strong overall alignment and readiness to contribute immediately."
        })

    conf_level = "high" if confidence >= 0.7 else "medium" if confidence >= 0.4 else "low"
    
    res_explanation = {
        "key_matches": matched,
        "gaps": gaps,
        "risk_assessment": "High saturation risk" if saturation < 0.8 else "Standard market conditions",
        "confidence_level": conf_level,
        "application_prep": application_prep,
        "coaching": get_gap_advice(gaps)
    }

    reasoning = f"{decision}. Confidence: {conf_level}. Gaps: {len(gaps)}. Matched: {len(matched)}."

    return {
        "job_id": job.get("id"),
        "title": job.get("title", ""),
        "company": job.get("company", ""),
        "match_score": tech_fit, 
        "match_confidence": round(confidence * 100, 1),
        "ev": round(ev, 2), 
        "p_interview": round(p_interview, 3), 
        "career_value": round(career_value, 1),
        "confidence_score": round(confidence, 2),
        "confidence": round(confidence, 2), 
        "saturation_factor": round(saturation, 2),
        "breakdown": {
            "skill_match": skill_score,
            "exp_match": exp_score,
            "location_match": location_score,
            "future_readiness": future_score,
            "growth_pathway": growth_score,
            "growth_potential": growth_score 
        },
        "explanation": res_explanation,
        "reasoning": reasoning,
        "recommendation": decision,
        "decision": decision,
        "gaps": gaps,
        "matched_skills": matched,
        "application_prep": application_prep,
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
    """Rank all jobs by Expected Value (EV), with confidence-weighted calibration."""
    from rnd.score_calibrator import apply_calibration

    bulk_rust_scores = {}
    if RUST_AVAILABLE:
        all_j_skills = [j.get("skills_required", []) for j in jobs]
        rust_ratios = career_rust.bulk_score_keywords(profile.get("skills", []), all_j_skills)
        bulk_rust_scores = {jobs[i]["id"]: rust_ratios[i] for i in range(len(jobs))}

    context = {
        "freqs": db.get_skill_frequencies(),
        "job_count": db.count_jobs(),
        "pulse": get_market_pulse()
    }

    results = []
    for job in jobs:
        r = score_job(
            profile, 
            job, 
            profile_emb, 
            job_embeddings.get(job.get("id")) if job_embeddings else None, 
            rl_boosts.get(job.get("id"), 0.0) if rl_boosts else 0.0,
            precalculated_rust_ratio=bulk_rust_scores.get(job.get("id")),
            context=context
        )
        # Apply confidence-weighted calibration (v4.0 R&D → Production)
        apply_calibration(r)
        results.append(r)
    
    for r in results:
        target_job = next((j for j in jobs if j["id"] == r["job_id"]), None)
        if target_job:
            r["similar_roles"] = get_similar_roles(target_job, jobs, n=3)
            
    return sorted(results, key=lambda x: x["ev"], reverse=True)
