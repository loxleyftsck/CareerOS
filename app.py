"""
app.py — CareerOS Entry Point
Run: streamlit run app.py
"""

import streamlit as st
from db import init_db

st.set_page_config(
    page_title="CareerOS",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS injection ────────────────────────────────────────────────────
st.markdown("""
<style>
/* Sidebar branding */
[data-testid="stSidebarNav"]::before {
    content: "🚀 CareerOS";
    display: block;
    font-size: 1.4rem;
    font-weight: 800;
    color: #00ff88;
    padding: 1rem 1rem 0.5rem;
    letter-spacing: 0.05em;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(0,255,136,0.15);
    border-radius: 12px;
    padding: 1rem;
}

/* Score badges */
.badge-high    { background:#00ff88; color:#000; padding:3px 10px; border-radius:20px; font-weight:700; font-size:0.75rem; }
.badge-mid     { background:#ffd700; color:#000; padding:3px 10px; border-radius:20px; font-weight:700; font-size:0.75rem; }
.badge-review  { background:#ff9500; color:#000; padding:3px 10px; border-radius:20px; font-weight:700; font-size:0.75rem; }
.badge-low     { background:#ff4b4b; color:#fff; padding:3px 10px; border-radius:20px; font-weight:700; font-size:0.75rem; }

/* Job cards */
.job-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    transition: border-color 0.2s;
}
.job-card:hover { border-color: rgba(0,255,136,0.35); }

/* Section headers */
.section-title {
    font-size: 0.75rem;
    font-weight: 600;
    color: #00ff88;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 0.4rem;
}

/* Skill chips */
.chip {
    display: inline-block;
    background: rgba(0,255,136,0.1);
    color: #00ff88;
    border: 1px solid rgba(0,255,136,0.25);
    padding: 2px 9px;
    border-radius: 20px;
    font-size: 0.75rem;
    margin: 2px;
    font-weight: 600;
}
.chip-gap {
    display: inline-block;
    background: rgba(255,75,75,0.1);
    color: #ff4b4b;
    border: 1px solid rgba(255,75,75,0.25);
    padding: 2px 9px;
    border-radius: 20px;
    font-size: 0.75rem;
    margin: 2px;
}

/* Hide Streamlit default footer */
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Database init ───────────────────────────────────────────────────────────
init_db()

# ── Navigation ───────────────────────────────────────────────────────────────
pg = st.navigation([
    st.Page("pages/dashboard.py",  title="Dashboard",        icon="🏠", default=True),
    st.Page("pages/profile.py",    title="My Profile",       icon="👤"),
    st.Page("pages/add_jobs.py",   title="Add Jobs",         icon="📥"),
    st.Page("pages/results.py",    title="Results & Ranking",icon="🎯"),
    st.Page("pages/tracker.py",    title="Job Tracker",      icon="📋"),
])
pg.run()
