"""
db.py — SQLite data layer for CareerOS
Zero-config, single file database.
"""

import sqlite3
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "careeros.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_conn()
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY DEFAULT 1,
            name TEXT,
            skills TEXT,
            experience_years REAL,
            target_roles TEXT,
            location_pref TEXT,
            salary_min INTEGER,
            career_goals TEXT,
            raw_cv_text TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if raw_cv_text exists (handle migrations manually)
    try:
        c.execute("ALTER TABLE profile ADD COLUMN raw_cv_text TEXT")
    except sqlite3.OperationalError:
        pass # Column exists

    c.executescript("""
    CREATE TABLE IF NOT EXISTS jobs (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        title           TEXT    NOT NULL,
        company         TEXT    DEFAULT '',
        description     TEXT    DEFAULT '',
        skills_required TEXT    DEFAULT '[]',
        experience_min  REAL    DEFAULT 0,
        experience_max  REAL    DEFAULT 5,
        salary_min      INTEGER DEFAULT 0,
        salary_max      INTEGER DEFAULT 0,
        location        TEXT    DEFAULT '',
        source          TEXT    DEFAULT 'manual',
        url             TEXT    DEFAULT '',
        status          TEXT    DEFAULT 'new',
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS analyses (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id          INTEGER UNIQUE,
        match_score     REAL    DEFAULT 0,
        skill_score     REAL    DEFAULT 0,
        exp_score       REAL    DEFAULT 0,
        location_score  REAL    DEFAULT 0,
        growth_score    REAL    DEFAULT 0,
        recommendation  TEXT    DEFAULT '',
        reasoning       TEXT    DEFAULT '',
        gaps            TEXT    DEFAULT '[]',
        matched_skills  TEXT    DEFAULT '[]',
        rl_utility      REAL    DEFAULT 0,
        analyzed_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS feedback (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id      INTEGER,
        action      TEXT,
        reward      REAL    DEFAULT 0,
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS rl_qtable (
        state_key   TEXT PRIMARY KEY,
        q_value     REAL    DEFAULT 0,
        visit_count INTEGER DEFAULT 0,
        updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()


# ── Profile ──────────────────────────────────────────────────────────────────

def get_profile() -> Optional[Dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["skills"] = json.loads(d["skills"])
    d["target_roles"] = json.loads(d["target_roles"])
    return d


def save_profile(data: Dict):
    conn = get_conn()
    conn.execute("""
        INSERT INTO profile (id, name, skills, experience_years, target_roles,
                             location_pref, salary_min, career_goals, updated_at)
        VALUES (1, :name, :skills, :experience_years, :target_roles,
                :location_pref, :salary_min, :career_goals, CURRENT_TIMESTAMP)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            skills = excluded.skills,
            experience_years = excluded.experience_years,
            target_roles = excluded.target_roles,
            location_pref = excluded.location_pref,
            salary_min = excluded.salary_min,
            career_goals = excluded.career_goals,
            raw_cv_text = excluded.raw_cv_text,
            updated_at = CURRENT_TIMESTAMP
    """, {
        "name": data.get("name", "User"),
        "skills": json.dumps(data.get("skills", [])),
        "experience_years": data.get("experience_years", 0),
        "target_roles": json.dumps(data.get("target_roles", [])),
        "location_pref": data.get("location_pref", "Jakarta"),
        "salary_min": data.get("salary_min", 0),
        "career_goals": data.get("career_goals", ""),
        "raw_cv_text": data.get("raw_cv_text", "")
    })
    conn.commit()
    conn.close()


# ── Jobs ─────────────────────────────────────────────────────────────────────

def get_all_jobs(status_filter: Optional[str] = None) -> List[Dict]:
    conn = get_conn()
    if status_filter:
        rows = conn.execute(
            "SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC", (status_filter,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
    conn.close()
    jobs = []
    for row in rows:
        d = dict(row)
        d["skills_required"] = json.loads(d.get("skills_required", "[]"))
        jobs.append(d)
    return jobs


def get_job(job_id: int) -> Optional[Dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["skills_required"] = json.loads(d.get("skills_required", "[]"))
    return d


def insert_job(job: Dict) -> int:
    conn = get_conn()
    cur = conn.execute("""
        INSERT INTO jobs (title, company, description, skills_required,
                          experience_min, experience_max, salary_min, salary_max,
                          location, source, url, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new')
    """, (
        job.get("title", ""),
        job.get("company", ""),
        job.get("description", ""),
        json.dumps(job.get("skills_required", [])),
        job.get("experience_min", 0),
        job.get("experience_max", 5),
        job.get("salary_min", 0),
        job.get("salary_max", 0),
        job.get("location", ""),
        job.get("source", "manual"),
        job.get("url", ""),
    ))
    job_id = cur.lastrowid
    conn.commit()
    conn.close()
    return job_id


def update_job_status(job_id: int, status: str):
    conn = get_conn()
    conn.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))
    conn.commit()
    conn.close()


def delete_job(job_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()


def count_jobs() -> int:
    conn = get_conn()
    n = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    conn.close()
    return n


# ── Analyses ─────────────────────────────────────────────────────────────────

def save_analysis(result: Dict):
    conn = get_conn()
    conn.execute("""
        INSERT INTO analyses (job_id, match_score, skill_score, exp_score,
                              location_score, growth_score, recommendation,
                              reasoning, gaps, matched_skills, rl_utility, analyzed_at)
        VALUES (:job_id, :match_score, :skill_score, :exp_score, :location_score,
                :growth_score, :recommendation, :reasoning, :gaps, :matched_skills,
                :rl_utility, CURRENT_TIMESTAMP)
        ON CONFLICT(job_id) DO UPDATE SET
            match_score    = excluded.match_score,
            skill_score    = excluded.skill_score,
            exp_score      = excluded.exp_score,
            location_score = excluded.location_score,
            growth_score   = excluded.growth_score,
            recommendation = excluded.recommendation,
            reasoning      = excluded.reasoning,
            gaps           = excluded.gaps,
            matched_skills = excluded.matched_skills,
            rl_utility     = excluded.rl_utility,
            analyzed_at    = CURRENT_TIMESTAMP
    """, {
        "job_id": result["job_id"],
        "match_score": result["match_score"],
        "skill_score": result["breakdown"]["skill_match"],
        "exp_score": result["breakdown"]["exp_match"],
        "location_score": result["breakdown"]["location_match"],
        "growth_score": result["breakdown"]["growth_potential"],
        "recommendation": result["recommendation"],
        "reasoning": result["reasoning"],
        "gaps": json.dumps(result.get("gaps", [])),
        "matched_skills": json.dumps(result.get("matched_skills", [])),
        "rl_utility": result.get("rl_utility", 0),
    })
    conn.commit()
    conn.close()


def get_analyses() -> Dict[int, Dict]:
    """Returns {job_id: analysis_dict}"""
    conn = get_conn()
    rows = conn.execute("SELECT * FROM analyses").fetchall()
    conn.close()
    result = {}
    for row in rows:
        d = dict(row)
        d["gaps"] = json.loads(d.get("gaps", "[]"))
        d["matched_skills"] = json.loads(d.get("matched_skills", "[]"))
        result[d["job_id"]] = d
    return result


# ── Feedback ─────────────────────────────────────────────────────────────────

def record_feedback(job_id: int, action: str, reward: float):
    conn = get_conn()
    conn.execute(
        "INSERT INTO feedback (job_id, action, reward) VALUES (?, ?, ?)",
        (job_id, action, reward)
    )
    conn.commit()
    conn.close()


def get_feedback_rewards() -> Dict[int, float]:
    """Returns {job_id: total_reward}"""
    conn = get_conn()
    rows = conn.execute(
        "SELECT job_id, SUM(reward) as total FROM feedback GROUP BY job_id"
    ).fetchall()
    conn.close()
    return {row["job_id"]: row["total"] for row in rows}


# ── RL Q-Table ───────────────────────────────────────────────────────────────

def get_q_value(state_key: str) -> float:
    conn = get_conn()
    row = conn.execute(
        "SELECT q_value FROM rl_qtable WHERE state_key = ?", (state_key,)
    ).fetchone()
    conn.close()
    return row["q_value"] if row else 0.0


def set_q_value(state_key: str, q_value: float):
    conn = get_conn()
    conn.execute("""
        INSERT INTO rl_qtable (state_key, q_value, visit_count, updated_at)
        VALUES (?, ?, 1, CURRENT_TIMESTAMP)
        ON CONFLICT(state_key) DO UPDATE SET
            q_value     = excluded.q_value,
            visit_count = visit_count + 1,
            updated_at  = CURRENT_TIMESTAMP
    """, (state_key, q_value))
    conn.commit()
    conn.close()
