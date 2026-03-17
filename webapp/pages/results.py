"""
pages/results.py — AI Job Ranking Engine (Antigravity)
Displays scored, ranked job cards with breakdown and feedback buttons.
"""

import streamlit as st
import plotly.graph_objects as go
from core import db, antigravity, rl_engine

# Try to import embedder (needs sentence-transformers installed)
try:
    from utils import embedder
    EMBEDDINGS_AVAILABLE = True
except Exception:
    EMBEDDINGS_AVAILABLE = False


# ── Helpers ───────────────────────────────────────────────────────────────────

BADGE = {
    "HIGH_PRIORITY_APPLY": ("🟢 HIGH PRIORITY — APPLY", "badge-high"),
    "CONSIDER_STRONGLY":   ("🟡 CONSIDER STRONGLY",     "badge-mid"),
    "REVIEW":              ("🟠 REVIEW",                 "badge-review"),
    "LOW_PRIORITY":        ("🔴 LOW PRIORITY",           "badge-low"),
}

SCORE_COLOR = {
    "HIGH_PRIORITY_APPLY": "#00ff88",
    "CONSIDER_STRONGLY":   "#ffd700",
    "REVIEW":              "#ff9500",
    "LOW_PRIORITY":        "#ff4b4b",
}


def score_gauge(score: float, recommendation: str) -> go.Figure:
    color = SCORE_COLOR.get(recommendation, "#888")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"suffix": "%", "font": {"size": 28, "color": color}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#444"},
            "bar": {"color": color, "thickness": 0.7},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 55],  "color": "rgba(255,75,75,0.08)"},
                {"range": [55, 70], "color": "rgba(255,149,0,0.08)"},
                {"range": [70, 85], "color": "rgba(255,215,0,0.08)"},
                {"range": [85, 100],"color": "rgba(0,255,136,0.08)"},
            ],
            "threshold": {"line": {"color": color, "width": 3}, "thickness": 0.8, "value": score},
        },
    ))
    fig.update_layout(
        height=160, margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#e2e8f0"},
    )
    return fig


def breakdown_chart(breakdown: dict) -> go.Figure:
    labels = ["Skill Match", "Exp Fit", "Location", "Growth"]
    values = [
        breakdown["skill_match"],
        breakdown["exp_match"],
        breakdown["location_match"],
        breakdown["growth_potential"],
    ]
    colors = ["#00ff88" if v >= 70 else "#ffd700" if v >= 55 else "#ff4b4b" for v in values]
    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker_color=colors,
        text=[f"{v:.0f}%" for v in values],
        textposition="inside",
        textfont={"color": "#000", "size": 11, "family": "sans-serif"},
    ))
    fig.update_layout(
        height=140,
        margin=dict(l=0, r=10, t=10, b=10),
        xaxis={"range": [0, 100], "showgrid": False, "showticklabels": False},
        yaxis={"showgrid": False},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#e2e8f0", "size": 11},
    )
    return fig


# ── Main Page ──────────────────────────────────────────────────────────────────

st.title("🎯 Results & Ranking")
st.caption("Antigravity scores every job against your profile. UTILITY = 50% skill + 20% exp + 15% location + 15% growth")
st.divider()

profile = db.get_profile()
jobs    = db.get_all_jobs()

# Guard: need profile + jobs
if not profile:
    st.warning("⚠️ No profile found. Set up your profile first.")
    if st.button("→ Go to My Profile"):
        st.switch_page("pages/profile.py")
    st.stop()

if not jobs:
    st.warning("⚠️ No jobs in database. Add jobs first.")
    if st.button("→ Add Jobs"):
        st.switch_page("pages/add_jobs.py")
    st.stop()

# ── Run analysis ──────────────────────────────────────────────────────────────
run_col, filter_col = st.columns([2, 2])
with run_col:
    run_analysis = st.button("⚡ Run Antigravity Analysis", type="primary", use_container_width=True)
with filter_col:
    show_filter = st.selectbox(
        "Show",
        ["All", "HIGH_PRIORITY_APPLY", "CONSIDER_STRONGLY", "REVIEW", "LOW_PRIORITY"],
        key="rec_filter"
    )

if run_analysis or "ranked_results" not in st.session_state:
    with st.spinner("🧠 Antigravity analysing all jobs..."):
        # Compute embeddings if available
        profile_emb = None
        job_embeddings = {}
        if EMBEDDINGS_AVAILABLE:
            try:
                profile_emb = embedder.encode_profile(profile)
                for job in jobs:
                    job_embeddings[job["id"]] = embedder.encode_job(job)
            except Exception as e:
                st.toast(f"⚠️ Embedding skipped: {e}", icon="⚠️")

        # Get RL boosts
        rl_boosts = rl_engine.get_rl_boosts(jobs, profile)

        # Rank jobs
        ranked = antigravity.rank_jobs(profile, jobs, profile_emb, job_embeddings, rl_boosts)

        # Persist analyses
        for r in ranked:
            db.save_analysis(r)

        st.session_state["ranked_results"] = ranked
        st.toast(f"✅ Analysed {len(ranked)} jobs!", icon="🎯")

ranked_results = st.session_state.get("ranked_results", [])

# Apply filter
if show_filter != "All":
    displayed = [r for r in ranked_results if r["recommendation"] == show_filter]
else:
    displayed = ranked_results

st.markdown(f"**{len(displayed)} jobs** | sorted by match score")
st.divider()

# ── Job Cards ─────────────────────────────────────────────────────────────────
if not displayed:
    st.info("No jobs match this filter.")
else:
    for i, result in enumerate(displayed):
        job = db.get_job(result["job_id"])
        if not job:
            continue

        rec   = result["recommendation"]
        score = result["match_score"]
        label, badge_cls = BADGE.get(rec, ("UNKNOWN", "badge-low"))

        with st.container():
            # Card header
            h1, h2 = st.columns([5, 2])
            with h1:
                st.markdown(
                    f"### {i+1}. {result['title']}\n"
                    f"**{result['company']}** · {job.get('location','—')}"
                )
                if job.get("salary_min"):
                    st.caption(f"💰 Rp {job['salary_min'] // 1_000_000:,}jt+ /month")
                st.markdown(f'<span class="{badge_cls}">{label}</span>', unsafe_allow_html=True)
            with h2:
                st.plotly_chart(
                    score_gauge(score, rec),
                    use_container_width=True,
                    key=f"gauge_{result['job_id']}_{i}",
                )

            # Details expander
            with st.expander("📊 Full breakdown & Explainable AI Reasoning", expanded=True):
                col_a, col_b = st.columns([3, 2])
                with col_a:
                    st.plotly_chart(
                        breakdown_chart(result["breakdown"]),
                        use_container_width=True,
                        key=f"bar_{result['job_id']}_{i}",
                    )
                    st.markdown('<p class="section-title">💡 Antigravity Reasoning</p>', unsafe_allow_html=True)
                    # Convert reasoning into bullet points for better scannability
                    reasoning_bullets = "<ul>" + "".join([f"<li>{r.strip()}</li>" for r in result["reasoning"].split("—") if r.strip()]) + "</ul>"
                    st.markdown(reasoning_bullets, unsafe_allow_html=True)

                with col_b:
                    if result.get("matched_skills"):
                        st.markdown('<p class="section-title">✅ Matched Skills</p>', unsafe_allow_html=True)
                        chips = " ".join(f'<span class="chip">{s}</span>' for s in result["matched_skills"])
                        st.markdown(chips, unsafe_allow_html=True)

                    if result.get("gaps"):
                        st.markdown('<p class="section-title">⚠️ Gaps</p>', unsafe_allow_html=True)
                        gap_chips = " ".join(f'<span class="chip-gap">{g}</span>' for g in result["gaps"])
                        st.markdown(gap_chips, unsafe_allow_html=True)

                    st.markdown('<p class="section-title">🤖 CARL-DTN</p>', unsafe_allow_html=True)
                    st.caption(f"RL utility boost: `{result['rl_utility']:.3f}` · confidence: `{result['confidence']:.2f}`")

                    if job.get("url"):
                        st.link_button("🔗 Open Job Listing", job["url"])

            # Feedback row
            fb_col1, fb_col2, fb_col3, fb_col4 = st.columns(4)
            with fb_col1:
                if st.button("✅ Applied", key=f"apply_{result['job_id']}_{i}"):
                    db.record_feedback(result["job_id"], "apply", 2.0)
                    db.update_job_status(result["job_id"], "applied")
                    rl_engine.update(job, profile, "apply")
                    st.toast(f"Marked as Applied! +2 reward → RL updated 🎓")
                    st.session_state.pop("ranked_results", None)
                    st.rerun()
            with fb_col2:
                if st.button("👍 Interested", key=f"int_{result['job_id']}_{i}"):
                    db.record_feedback(result["job_id"], "interest", 1.0)
                    db.update_job_status(result["job_id"], "saved")
                    rl_engine.update(job, profile, "interest")
                    st.toast("Saved as Interested! +1 reward 🎯")
                    st.rerun()
            with fb_col3:
                if st.button("👎 Skip", key=f"skip_{result['job_id']}_{i}"):
                    db.record_feedback(result["job_id"], "skip", -1.0)
                    rl_engine.update(job, profile, "skip")
                    st.toast("Skipped. −1 reward → similar jobs ranked lower.")
                    st.rerun()
            with fb_col4:
                if st.button("🗑️ Delete", key=f"del_{result['job_id']}_{i}"):
                    db.delete_job(result["job_id"])
                    st.session_state.pop("ranked_results", None)
                    st.rerun()

            st.divider()
