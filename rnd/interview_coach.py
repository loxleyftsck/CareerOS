"""
rnd/interview_coach.py
Experiment 6: AI Interview Coach — Generate targeted practice questions from skill gaps.

Usage:
    python rnd/interview_coach.py --job_id 42
    python rnd/interview_coach.py --job_title "Backend Engineer"
"""

import os
import sys
import re
import argparse
from typing import Dict, List

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from storage import db
from engine.scoring.utils import get_gaps


# -- Template Library ---------------------------------------------------------

BEHAVIORAL_TEMPLATES = [
    "Tell me about a time you had to learn {skill} quickly under pressure.",
    "How would you approach solving a complex problem using {skill}?",
    "Describe a project where {skill} was critical to success. What was your role?",
    "What's your experience level with {skill}, and how have you applied it professionally?",
    "If you were missing {skill} experience, how would you get up to speed in 2 weeks?",
]

TECHNICAL_TEMPLATES = {
    "docker":      ["What's the difference between an image and a container in Docker?",
                    "Explain multi-stage Docker builds and when you'd use them."],
    "kubernetes":  ["How does a Kubernetes Deployment differ from a StatefulSet?",
                    "Describe how you would handle a pod that keeps crashing (CrashLoopBackOff)."],
    "python":      ["Explain the GIL in Python and when it matters.",
                    "What are the differences between `@staticmethod` and `@classmethod`?"],
    "sql":         ["What's the difference between INNER JOIN and LEFT JOIN?",
                    "How do you optimize a slow SQL query? Walk me through your process."],
    "react":       ["Explain the virtual DOM and why React uses it.",
                    "When would you use `useMemo` vs `useCallback`?"],
    "aws":         ["What's the difference between an EC2 instance and a Lambda function?",
                    "How would you design a scalable, fault-tolerant architecture on AWS?"],
    "tensorflow":  ["Explain the difference between eager and graph execution in TensorFlow.",
                    "What are the key differences between `fit()` and custom training loops?"],
}


def generate_questions(gap: str, count: int = 2) -> List[str]:
    """Generate targeted interview questions for a specific skill gap."""
    gap_lower = gap.lower().strip()
    questions = []

    # Add technical questions if known
    if gap_lower in TECHNICAL_TEMPLATES:
        questions.extend(TECHNICAL_TEMPLATES[gap_lower][:count])
    
    # Pad with behavioral templates if needed
    import random
    behavioral = random.sample(BEHAVIORAL_TEMPLATES, min(count, len(BEHAVIORAL_TEMPLATES)))
    for template in behavioral:
        q = template.replace("{skill}", gap)
        if q not in questions:
            questions.append(q)

    return questions[:count]


def coach_for_job(job: Dict, profile: Dict) -> Dict:
    """Generate a full coaching session for a specific job."""
    u_skills = profile.get("skills", [])
    j_skills = job.get("skills_required", [])
    gaps = get_gaps(u_skills, j_skills)

    coaching_plan = []
    for gap in gaps[:4]:  # Focus on top 4 gaps
        questions = generate_questions(gap, count=2)
        coaching_plan.append({
            "skill": gap,
            "questions": questions,
            "preparation_tip": f"Review the fundamentals of {gap} on official docs or a 2-hour YouTube tutorial before the interview."
        })

    return {
        "job_title": job.get("title", ""),
        "company": job.get("company", ""),
        "gaps_targeted": gaps[:4],
        "coaching_plan": coaching_plan,
        "opening_statement": f"For {job.get('title', '')} at {job.get('company', '')}, focus on demonstrating transferable skills if you lack direct {', '.join(gaps[:2]) if gaps else 'any'} experience."
    }


def main():
    parser = argparse.ArgumentParser(description="CareerOS Interview Coach")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--job_id", type=int, help="Job ID from database")
    group.add_argument("--job_title", type=str, help="Search jobs by title keyword")
    args = parser.parse_args()

    db.init_db()
    profile = db.get_profile()
    if not profile:
        print("[!] No profile found.")
        return

    job = None
    if args.job_id:
        job = db.get_job(args.job_id)
    elif args.job_title:
        all_jobs = db.get_all_jobs()
        keyword = args.job_title.lower()
        matched = [j for j in all_jobs if keyword in j.get("title", "").lower()]
        if matched:
            job = matched[0]
    
    if not job:
        print("[!] Job not found.")
        return

    session = coach_for_job(job, profile)

    print(f"\n{'='*60}")
    print(f"🎯 INTERVIEW COACH: {session['job_title']} @ {session['company']}")
    print(f"{'='*60}")
    print(f"\n💡 {session['opening_statement']}\n")

    for plan in session["coaching_plan"]:
        print(f"┌── Skill Gap: [{plan['skill'].upper()}]")
        for i, q in enumerate(plan["questions"], 1):
            print(f"│  Q{i}: {q}")
        print(f"│  💡 Tip: {plan['preparation_tip']}")
        print(f"└{'─'*58}")
    print()


if __name__ == "__main__":
    main()
