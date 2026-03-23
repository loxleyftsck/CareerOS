from typing import Dict, List
from engine.scoring.utils import _keyword_overlap
from engine.scoring.pulse import calculate_real_pulse

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
