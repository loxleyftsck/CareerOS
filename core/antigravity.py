"""
antigravity.py — CareerOS Matching & Scoring Engine
Weighted multi-factor analysis: 50% skill / 20% exp / 15% location / 15% growth
"""

from typing import Dict, List, Optional
import numpy as np

# ── Company Prestige Map (Indonesian tech ecosystem) ─────────────────────────
COMPANY_PRESTIGE: Dict[str, float] = {
    "gojek": 0.95, "goto": 0.93, "tokopedia": 0.92, "traveloka": 0.90,
    "shopee": 0.90, "sea limited": 0.90, "grab": 0.88, "blibli": 0.82,
    "bukalapak": 0.80, "ovo": 0.78, "dana": 0.78, "tiket": 0.75,
    "ruangguru": 0.80, "zenius": 0.72, "xendit": 0.82, "privy": 0.70,
    "kalibrr": 0.60, "glints": 0.58, "google": 0.98, "meta": 0.96,
    "microsoft": 0.97, "aws": 0.95, "amazon": 0.95, "apple": 0.97,
}

# ── Location Score Map ────────────────────────────────────────────────────────
LOCATION_SCORES: Dict[str, float] = {
    "jakarta": 1.00, "dki jakarta": 1.00, "south jakarta": 1.00,
    "central jakarta": 1.00, "jakarta selatan": 1.00,
    "bandung": 0.75, "yogyakarta": 0.70, "surabaya": 0.72,
    "bali": 0.65, "semarang": 0.65, "medan": 0.62,
    "remote": 0.88, "wfh": 0.88, "work from home": 0.88, "hybrid": 0.82,
}

# ── Skills that signal high future demand ────────────────────────────────────
FUTURE_SKILLS = {
    "llm", "ai", "ml", "machine learning", "deep learning", "langchain",
    "langraph", "crewai", "fastapi", "vector", "embedding", "rag",
    "cloud", "aws", "gcp", "azure", "kubernetes", "docker", "mlops",
    "data engineering", "spark", "dbt", "airflow",
}


# ── Utilities ─────────────────────────────────────────────────────────────────

def _cosine(a: Optional[np.ndarray], b: Optional[np.ndarray]) -> float:
    if a is None or b is None:
        return 0.0
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def _keyword_overlap(user_skills: List[str], job_skills: List[str]) -> float:
    if not user_skills or not job_skills:
        return 0.0
    u = {s.lower().strip() for s in user_skills}
    j = {s.lower().strip() for s in job_skills}
    exact = len(u & j)
    partial = sum(
        0.5 for us in u for js in j
        if (us in js or js in us) and us != js
    )
    matched = min(exact + partial, len(j))
    return matched / len(j)


# ── Scoring Dimensions ────────────────────────────────────────────────────────

def compute_skill_score(
    user_emb: Optional[np.ndarray],
    job_emb: Optional[np.ndarray],
    user_skills: List[str],
    job_skills: List[str],
) -> float:
    """50% weight: semantic similarity + keyword overlap hybrid."""
    semantic = (_cosine(user_emb, job_emb) + 1) / 2  # shift [-1,1] → [0,1]
    keyword = _keyword_overlap(user_skills, job_skills)
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


def compute_growth_score(
    company: str,
    user_salary_min: int,
    job_salary_min: int,
    job_skills: List[str],
    rl_boost: float = 0.0,
) -> float:
    """15% weight: prestige + salary fit + future skills + RL boost."""
    cl = company.lower().strip()
    prestige = next(
        (v for k, v in COMPANY_PRESTIGE.items() if k in cl),
        0.50
    )

    if job_salary_min > 0 and user_salary_min > 0:
        ratio = job_salary_min / user_salary_min
        salary_score = min(1.0, max(0.3, ratio * 0.85))
    else:
        salary_score = 0.60

    skill_set = {s.lower() for s in job_skills}
    future_overlap = len(skill_set & FUTURE_SKILLS) / len(FUTURE_SKILLS)

    raw = (
        0.40 * prestige
        + 0.35 * salary_score
        + 0.15 * future_overlap
        + 0.10 * rl_boost
    )
    return round(raw * 100, 1)


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_recommendation(total: float, skill: float) -> str:
    if total >= 85 and skill >= 75:
        return "HIGH_PRIORITY_APPLY"
    elif total >= 70:
        return "CONSIDER_STRONGLY"
    elif total >= 55:
        return "REVIEW"
    else:
        return "LOW_PRIORITY"


def get_gaps(user_skills: List[str], job_skills: List[str]) -> List[str]:
    u = {s.lower() for s in user_skills}
    gaps = []
    for s in job_skills:
        sl = s.lower()
        if sl not in u and not any(sl in us or us in sl for us in u):
            gaps.append(s)
    return gaps[:5]


def get_matched(user_skills: List[str], job_skills: List[str]) -> List[str]:
    u = {s.lower() for s in user_skills}
    matched = []
    for s in job_skills:
        sl = s.lower()
        if sl in u or any(sl in us or us in sl for us in u):
            matched.append(s)
    return matched[:5]


def build_reasoning(
    title: str,
    company: str,
    skill_score: float,
    exp_score: float,
    location_score: float,
    growth_score: float,
    total_score: float,
    matched: List[str],
    gaps: List[str],
) -> str:
    parts = []
    if matched:
        parts.append(
            f"Skill match {skill_score:.0f}% — "
            f"{', '.join(matched[:3])} align with job requirements."
        )
    else:
        parts.append(f"Skill overlap low ({skill_score:.0f}%) — significant upskilling required.")

    if exp_score >= 95:
        parts.append("Experience level is a perfect fit.")
    elif exp_score >= 75:
        parts.append("Experience is within acceptable range.")
    elif exp_score < 55:
        parts.append(f"Experience gap detected (score {exp_score:.0f}%) — may be underprepared.")
    else:
        parts.append("Slightly overqualified — worth considering for growth.")

    if location_score >= 90:
        parts.append("Location/remote preference matches exactly.")
    elif location_score < 50:
        parts.append("Location mismatch — negotiate remote or consider relocation.")

    if growth_score >= 80:
        parts.append(f"{company} offers strong prestige + growth trajectory.")

    if gaps:
        parts.append(f"Gaps to bridge: {', '.join(gaps[:3])}.")

    return " ".join(parts)


# ── Main API ──────────────────────────────────────────────────────────────────

def score_job(
    profile: Dict,
    job: Dict,
    profile_emb: Optional[np.ndarray] = None,
    job_emb: Optional[np.ndarray] = None,
    rl_boost: float = 0.0,
) -> Dict:
    """Score a single job against the user profile. Returns full analysis dict."""
    u_skills = profile.get("skills", [])
    j_skills = job.get("skills_required", [])

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
    growth_score = compute_growth_score(
        job.get("company", ""),
        profile.get("salary_min", 0),
        job.get("salary_min", 0),
        j_skills,
        rl_boost,
    )

    total = round(
        0.50 * skill_score
        + 0.20 * exp_score
        + 0.15 * location_score
        + 0.15 * growth_score,
        1,
    )

    matched = get_matched(u_skills, j_skills)
    gaps = get_gaps(u_skills, j_skills)
    recommendation = get_recommendation(total, skill_score)
    reasoning = build_reasoning(
        job.get("title", ""),
        job.get("company", ""),
        skill_score, exp_score, location_score, growth_score, total,
        matched, gaps,
    )

    return {
        "job_id": job.get("id"),
        "title": job.get("title", ""),
        "company": job.get("company", ""),
        "location": job.get("location", ""),
        "match_score": total,
        "breakdown": {
            "skill_match": skill_score,
            "exp_match": exp_score,
            "location_match": location_score,
            "growth_potential": growth_score,
        },
        "recommendation": recommendation,
        "reasoning": reasoning,
        "gaps": gaps,
        "matched_skills": matched,
        "rl_utility": round(rl_boost, 3),
        "confidence": round(min(0.99, total / 100 + 0.05), 2),
    }


def rank_jobs(
    profile: Dict,
    jobs: List[Dict],
    profile_emb: Optional[np.ndarray] = None,
    job_embeddings: Optional[Dict[int, np.ndarray]] = None,
    rl_boosts: Optional[Dict[int, float]] = None,
) -> List[Dict]:
    """Rank all jobs, return sorted descending by match_score."""
    if rl_boosts is None:
        rl_boosts = {}
    if job_embeddings is None:
        job_embeddings = {}

    results = [
        score_job(
            profile, job,
            profile_emb,
            job_embeddings.get(job.get("id")),
            rl_boosts.get(job.get("id"), 0.0),
        )
        for job in jobs
    ]
    return sorted(results, key=lambda x: x["match_score"], reverse=True)
