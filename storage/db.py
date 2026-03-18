"""
db.py — SQLite data layer for CareerOS
Zero-config, single file database.
"""

import sqlite3
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).parent / "careeros.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_conn()
    c = conn.cursor()

    # Core Tables
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
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        applied_at      TIMESTAMP,
        interview_at    TIMESTAMP,
        applicant_count INTEGER DEFAULT 0,
        is_warm_path    BOOLEAN DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS application_outcomes (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id          INTEGER UNIQUE,
        cluster_id      TEXT,
        stage_reached   TEXT,
        rejection_reason TEXT,
        days_to_response INTEGER,
        feedback_tag    TEXT,
        timestamp       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS analyses (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id          INTEGER UNIQUE,
        ev              REAL    DEFAULT 0,
        p_interview     REAL    DEFAULT 0,
        career_value    REAL    DEFAULT 0,
        confidence_score REAL   DEFAULT 0,
        saturation_factor REAL  DEFAULT 1.0,
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
        updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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

    CREATE TABLE IF NOT EXISTS notifications (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        type        TEXT, -- 'radar', 'coaching', 'system'
        title       TEXT,
        message     TEXT,
        job_id      INTEGER,
        is_read     BOOLEAN DEFAULT 0,
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(job_id) REFERENCES jobs(id)
    );
    """)

    # Manual Column Migrations (Robustness)
    MIGRATIONS = [
        ("profile", "raw_cv_text", "TEXT"),
        ("jobs", "applied_at", "TIMESTAMP"),
        ("jobs", "interview_at", "TIMESTAMP"),
        ("jobs", "applicant_count", "INTEGER DEFAULT 0"),
        ("jobs", "is_warm_path", "BOOLEAN DEFAULT 0"),
        ("analyses", "ev", "REAL DEFAULT 0"),
        ("analyses", "p_interview", "REAL DEFAULT 0"),
        ("analyses", "career_value", "REAL DEFAULT 0"),
        ("analyses", "confidence_score", "REAL DEFAULT 0"),
        ("analyses", "saturation_factor", "REAL DEFAULT 1.0")
    ]
    for table, col, col_type in MIGRATIONS:
        try:
            c.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
        except sqlite3.OperationalError: pass

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

def get_all_jobs(status_filter: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
    conn = get_conn()
    query = "SELECT * FROM jobs"
    params = []
    if status_filter:
        query += " WHERE status = ?"
        params.append(status_filter)
    query += " ORDER BY created_at DESC"
    if limit:
        query += " LIMIT ?"
        params.append(limit)
        
    rows = conn.execute(query, params).fetchall()
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
                          location, source, url, status, applicant_count, is_warm_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', ?, ?)
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
        job.get("applicant_count", 0),
        job.get("is_warm_path", 0)
    ))
    job_id = cur.lastrowid
    conn.commit()
    conn.close()
    return job_id


def update_job_field(job_id: int, field: str, value: Any):
    conn = get_conn()
    conn.execute(f"UPDATE jobs SET {field} = ? WHERE id = ?", (value, job_id))
    conn.commit()
    conn.close()


def update_job_status(job_id: int, status: str):
    conn = get_conn()
    now_ts = "CURRENT_TIMESTAMP"
    extra_field = ""
    if status == 'applied':
        extra_field = ", applied_at = CURRENT_TIMESTAMP"
    elif status == 'interview':
        extra_field = ", interview_at = CURRENT_TIMESTAMP"
        
    conn.execute(f"UPDATE jobs SET status = ?, updated_at = CURRENT_TIMESTAMP {extra_field} WHERE id = ?", (status, job_id))
    conn.commit()
    conn.close()


def get_pipeline_stats() -> Dict[str, int]:
    """Returns counts of jobs in each pipeline stage."""
    conn = get_conn()
    rows = conn.execute("SELECT status, COUNT(*) as count FROM jobs GROUP BY status").fetchall()
    conn.close()
    return {row["status"]: row["count"] for row in rows}


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
        INSERT INTO analyses (job_id, ev, p_interview, career_value, confidence_score,
                              saturation_factor, match_score, skill_score, exp_score,
                              location_score, growth_score, recommendation,
                              reasoning, gaps, matched_skills, rl_utility, analyzed_at)
        VALUES (:job_id, :ev, :p_interview, :career_value, :confidence_score,
                :saturation_factor, :match_score, :skill_score, :exp_score, :location_score,
                :growth_score, :recommendation, :reasoning, :gaps, :matched_skills,
                :rl_utility, CURRENT_TIMESTAMP)
        ON CONFLICT(job_id) DO UPDATE SET
            ev             = excluded.ev,
            p_interview    = excluded.p_interview,
            career_value   = excluded.career_value,
            confidence_score = excluded.confidence_score,
            saturation_factor = excluded.saturation_factor,
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
        "ev": result.get("ev", 0),
        "p_interview": result.get("p_interview", 0),
        "career_value": result.get("career_value", 0),
        "confidence_score": result.get("confidence", 0),
        "saturation_factor": result.get("saturation_factor", 1.0),
        "match_score": result["match_score"],
        "skill_score": result["breakdown"].get("skill_match", 0),
        "exp_score": result["breakdown"].get("exp_match", 0),
        "location_score": result["breakdown"].get("location_match", 0),
        "growth_score": result["breakdown"].get("growth_potential", 0),
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

def get_rl_stats() -> Dict:
    """Returns summarized RL health metrics."""
    conn = get_conn()
    row = conn.execute("SELECT COUNT(*) FROM rl_qtable").fetchone()
    total_states = row[0] if row else 0
    row = conn.execute("SELECT SUM(visit_count) FROM rl_qtable").fetchone()
    total_visits = row[0] if row else 0
    row = conn.execute("SELECT AVG(q_value) FROM rl_qtable").fetchone()
    avg_q = row[0] if row else 0.0
    conn.close()
    return {
        "total_states": total_states,
        "total_visits": total_visits or 0,
        "average_q": round(avg_q or 0.0, 4)
    }

def batch_update_q_values(updates: List):
    """Optimized batch update for maintenance."""
    conn = get_conn()
    conn.executemany(
        "UPDATE rl_qtable SET q_value = ? WHERE state_key = ?",
        updates
    )
    conn.commit()
    conn.close()

def get_skill_frequencies() -> Dict[str, int]:
    """Returns frequency of skills across all jobs in DB."""
    conn = get_conn()
    rows = conn.execute("SELECT skills_required FROM jobs").fetchall()
    conn.close()
    
    freqs = {}
    for row in rows:
        try:
            skills = json.loads(row["skills_required"] or "[]")
            for s in skills:
                s_low = s.lower().strip()
                if s_low:
                    freqs[s_low] = freqs.get(s_low, 0) + 1
        except:
            continue
    return freqs

def get_popular_skills_by_role(role_title: str, limit: int = 10) -> List[str]:
    """Dynamically identifies 'hot skills' for a role from the local market database."""
    conn = get_conn()
    rows = conn.execute("SELECT skills_required FROM jobs WHERE title LIKE ?", (f"%{role_title}%",)).fetchall()
    conn.close()
    
    freqs = {}
    for row in rows:
        try:
            skills = json.loads(row["skills_required"] or "[]")
            for s in skills:
                s_low = s.lower().strip()
                if s_low:
                    freqs[s_low] = freqs.get(s_low, 0) + 1
        except: continue
        
    sorted_skills = sorted(freqs.items(), key=lambda x: x[1], reverse=True)
    return [s[0] for s in sorted_skills[:limit]]

def count_similar_jobs(role_title: str) -> int:
    """Returns number of similar job samples for confidence scoring."""
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM jobs WHERE title LIKE ?", (f"%{role_title}%",)).fetchone()[0]
    conn.close()
    return count

def count_jobs() -> int:
    """Returns total number of jobs for context-axis switching."""
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    conn.close()
    return count
def record_outcome(data: Dict):
    """Persists long-term career outcome data."""
    conn = get_conn()
    conn.execute("""
        INSERT OR REPLACE INTO application_outcomes 
        (job_id, cluster_id, stage_reached, rejection_reason, days_to_response, feedback_tag)
        VALUES (:job_id, :cluster_id, :stage_reached, :rejection_reason, :days_to_response, :feedback_tag)
    """, data)
    conn.commit()
    conn.close()

def count_outcomes() -> int:
    """Returns total number of historical application outcomes for context axis."""
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM application_outcomes").fetchone()[0]
    conn.close()
    return count

def add_notification(ntype: str, title: str, message: str, job_id: int = None):
    conn = get_conn()
    conn.execute("""
        INSERT INTO notifications (type, title, message, job_id)
        VALUES (?, ?, ?, ?)
    """, (ntype, title, message, job_id))
    conn.commit()
    conn.close()

def get_notifications(limit: int = 10) -> List[Dict]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM notifications ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_cluster_stats(cluster_id: str) -> Dict[str, int]:
    """Retrieves success stats from Career Memory (Outcomes table)."""
    conn = get_conn()
    cursor = conn.cursor()
    # Number of applications that reached 'interview' or better
    interviews = cursor.execute(
        "SELECT COUNT(*) FROM application_outcomes WHERE cluster_id = ? AND stage_reached IN ('interview', 'offer')",
        (cluster_id,)
    ).fetchone()[0]
    
    # Total applications in this cluster
    total = cursor.execute(
        "SELECT COUNT(*) FROM application_outcomes WHERE cluster_id = ? AND stage_reached NOT IN ('click')",
        (cluster_id,)
    ).fetchone()[0]
    
    conn.close()
    return {"interviews": interviews, "total_applies": total}
