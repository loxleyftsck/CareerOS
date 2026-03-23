"""
pages/dashboard.py — CareerOS Home Dashboard
"""

import streamlit as st
from storage import db

from engine.scoring.prep_advisor import get_market_pulse

st.title("🚀 CareerOS")
st.markdown("##### *AI-powered job matching engine — find your next role faster*")
st.divider()

# ── One-time mock data load ──────────────────────────────────────────────────
if "mock_loaded" not in st.session_state:
    try:
        from agents import clawbot
        inserted = clawbot.load_mock_data()
        if inserted > 0:
            st.toast(f"✅ Clawbot loaded {inserted} fresh job listings!", icon="🤖")
    except Exception:
        pass
    st.session_state["mock_loaded"] = True

# ── Stats row ────────────────────────────────────────────────────────────────
profile = db.get_profile()
all_jobs = db.get_all_jobs()
analyses = db.get_analyses()

total_jobs     = len(all_jobs)
analysed_count = len(analyses)
applied_count  = len(db.get_all_jobs(status_filter="applied"))
top_score      = max((a["match_score"] for a in analyses.values()), default=0)

c1, c2, c3, c4 = st.columns(4)
c1.metric("📥 Jobs in DB", total_jobs)
c2.metric("🎯 Analysed", analysed_count)
c3.metric("📨 Applied", applied_count)
c4.metric("⭐ Best Match", f"{top_score:.0f}%" if top_score else "—")

st.divider()

# ── Profile status ───────────────────────────────────────────────────────────
col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown("#### 👤 Profile Status")
    if not profile:
        st.warning("No profile found. Go to **My Profile** to set up your skills and preferences.")
        if st.button("→ Set up profile now", type="primary"):
            st.switch_page("pages/profile.py")
    else:
        skills_str = ", ".join(profile["skills"][:6]) + ("…" if len(profile["skills"]) > 6 else "")
        st.success(f"**{profile['name']}** — {profile['experience_years']} yrs exp")
        st.markdown(f"**Skills:** {skills_str}")
        st.markdown(f"**Location:** {profile['location_pref']}  |  **Min Salary:** Rp {profile['salary_min']:,}")
        if profile.get("career_goals"):
            st.caption(f"🎯 *{profile['career_goals'][:120]}*")

with col_right:
    st.markdown("#### 🏆 Top Matches")
    if not analyses:
        st.info("No job analysis yet. Go to **Results & Ranking** to run the AI engine.")
        if st.button("→ Run Antigravity now", type="primary"):
            st.switch_page("pages/results.py")
    else:
        # Sort analyses by score, show top 3
        top3 = sorted(analyses.values(), key=lambda x: x["match_score"], reverse=True)[:3]
        for i, a in enumerate(top3):
            job = db.get_job(a["job_id"])
            if not job:
                continue
            rec = a["recommendation"]
            badge_cls = {
                "HIGH_PRIORITY_APPLY": "badge-high",
                "CONSIDER_STRONGLY": "badge-mid",
                "REVIEW": "badge-review",
                "LOW_PRIORITY": "badge-low",
            }.get(rec, "badge-low")
            rec_label = rec.replace("_", " ")
            score = a["match_score"]
            st.markdown(
                f"""<div class="job-card">
                <strong>#{i+1} {job['title']}</strong> — {job['company']}<br>
                <span style="font-size:1.4rem;font-weight:800;color:#00ff88">{score:.0f}%</span>
                &nbsp;&nbsp;<span class="{badge_cls}">{rec_label}</span>
                </div>""",
                unsafe_allow_html=True,
            )

st.divider()

# ── Market Pulse ─────────────────────────────────────────────────────────────
try:
    pulse = get_market_pulse()
    ai_surge = pulse.get("ai_surge", 1.0)
    hiring_idx = round(pulse.get("global_hiring_index", 1.0) * 100, 1)
    pm_col1, pm_col2 = st.columns(2)
    pm_col1.metric("🌐 Hiring Market", f"{hiring_idx}%", help="Global hiring activity index")
    pm_col2.metric("🔥 AI Surge", f"×{ai_surge:.2f}", delta="Active" if ai_surge > 1.2 else "Stable")
except Exception:
    pass

st.divider()

# ── Quick actions ────────────────────────────────────────────────────────────
st.markdown("#### ⚡ Quick Actions")
qa1, qa2, qa3, qa4 = st.columns(4)
with qa1:
    if st.button("📥 Add a job listing", use_container_width=True):
        st.switch_page("pages/add_jobs.py")
with qa2:
    if st.button("🎯 Run AI analysis", use_container_width=True):
        st.switch_page("pages/results.py")
with qa3:
    if st.button("📋 Open Job Tracker", use_container_width=True):
        st.switch_page("pages/tracker.py")
with qa4:
    if st.button("📊 View Report", use_container_width=True):
        st.switch_page("pages/reports.py")
