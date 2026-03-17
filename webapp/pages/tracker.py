"""
pages/tracker.py — Job Application Kanban Tracker
Statuses: new → saved → applied → interview → offer / rejected
"""

import streamlit as st
from core import db

st.title("📋 Job Tracker")
st.caption("Track every application through the pipeline. Click buttons to move jobs between stages.")
st.divider()

STATUS_COLUMNS = ["saved", "applied", "interview", "offer", "rejected"]
STATUS_ICONS = {
    "saved":    "🔖 Saved",
    "applied":  "📨 Applied",
    "interview":"💬 Interview",
    "offer":    "🏆 Offer",
    "rejected": "❌ Rejected",
}
STATUS_TRANSITIONS = {
    "saved":    ["applied"],
    "applied":  ["interview", "rejected"],
    "interview":["offer", "rejected"],
    "offer":    [],
    "rejected": [],
}

# ── Fetch & group jobs ────────────────────────────────────────────────────────
all_jobs = db.get_all_jobs()
analyses = db.get_analyses()

# Only show jobs that have been moved out of 'new'
tracked = [j for j in all_jobs if j["status"] in STATUS_COLUMNS]
by_status = {s: [] for s in STATUS_COLUMNS}
for job in tracked:
    by_status[job["status"]].append(job)

# ── Summary bar ───────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
for col, status in zip([c1, c2, c3, c4, c5], STATUS_COLUMNS):
    col.metric(STATUS_ICONS[status], len(by_status[status]))

st.divider()

# ── Kanban board ──────────────────────────────────────────────────────────────
cols = st.columns(len(STATUS_COLUMNS))

for col, status in zip(cols, STATUS_COLUMNS):
    with col:
        st.markdown(f"#### {STATUS_ICONS[status]}")
        jobs_in_col = by_status[status]

        if not jobs_in_col:
            st.caption("*Empty*")
        else:
            for job in jobs_in_col:
                analysis = analyses.get(job["id"])
                score_text = f"**{analysis['match_score']:.0f}%**" if analysis else ""

                with st.container():
                    st.markdown(
                        f"""<div class="job-card">
                        <strong>{job['title']}</strong><br>
                        <span style="color:#aaa;font-size:0.85rem">{job['company']}</span><br>
                        <span style="font-size:0.8rem">{job.get('location','')}</span>
                        </div>""",
                        unsafe_allow_html=True,
                    )
                    if score_text:
                        st.markdown(f"Match: {score_text}", unsafe_allow_html=True)

                    # Show next-step buttons
                    for next_status in STATUS_TRANSITIONS.get(status, []):
                        btn_label = {
                            "applied":  "📨 Mark Applied",
                            "interview":"💬 Got Interview!",
                            "offer":    "🏆 Got Offer!",
                            "rejected": "❌ Rejected",
                        }.get(next_status, f"→ {next_status}")

                        if st.button(btn_label, key=f"{job['id']}_{status}_{next_status}", use_container_width=True):
                            db.update_job_status(job["id"], next_status)
                            if next_status == "applied":
                                db.record_feedback(job["id"], "apply", 2.0)
                            st.rerun()

                    if st.button("🗑️", key=f"del_{job['id']}_{status}", help="Remove from tracker"):
                        db.update_job_status(job["id"], "new")
                        st.rerun()
                    st.write("")

st.divider()

# ── Untracked jobs (status='new') that can be added to tracker ────────────────
new_jobs = [j for j in all_jobs if j["status"] == "new"]
if new_jobs:
    st.markdown("#### 📥 Add to Tracker")
    st.caption(f"{len(new_jobs)} untracked jobs — save the ones you're interested in.")
    for job in new_jobs[:10]:
        analysis = analyses.get(job["id"])
        score_str = f" | Match: **{analysis['match_score']:.0f}%**" if analysis else ""
        col_info, col_save = st.columns([5, 1])
        with col_info:
            st.markdown(f"**{job['title']}** — {job['company']} · {job.get('location','')}{score_str}")
        with col_save:
            if st.button("Save", key=f"save_new_{job['id']}"):
                db.update_job_status(job["id"], "saved")
                st.rerun()
