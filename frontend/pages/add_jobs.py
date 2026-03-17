import streamlit as st
import time
import requests
from core import db
from agents import clawbot

# --- Page Config ---
st.set_page_config(page_title="Scout Jobs | CareerOS", page_icon="📥", layout="wide")

# --- Custom CSS (LinkedIn/Glitch hybrid) ---
st.markdown("""
<style>
    .scout-header {
        background: linear-gradient(135deg, #001f3f 0%, #0074D9 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .search-container {
        max-width: 800px;
        margin: 0 auto;
        background: white;
        padding: 10px;
        border-radius: 50px;
        display: flex;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
    .stButton > button {
        border-radius: 30px !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .live-status {
        background: rgba(0,255,136,0.1);
        border-left: 5px solid #00ff88;
        padding: 1rem;
        margin: 1rem 0;
        font-family: 'Courier New', Courier, monospace;
        color: #00ff88;
        border-radius: 4px;
    }
    .job-preview-card {
        background: #1a1c24;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: transform 0.2s, border-color 0.2s;
    }
    .job-preview-card:hover {
        transform: translateY(-2px);
        border-color: #0074D9;
    }
    .source-tag {
        font-size: 10px;
        background: #30363d;
        color: #8b949e;
        padding: 2px 8px;
        border-radius: 10px;
        float: right;
    }
</style>
""", unsafe_allow_html=True)

# --- Logic ---
def trigger_live_scrape(keyword, location, limit):
    # Log movement
    st.write(f'<div class="live-status">[UI] Button clicked. Keywords: {keyword}</div>', unsafe_allow_html=True)
    
    with st.status(f"🚀 Scouting for '{keyword}' on live boards...", expanded=True) as status:
        st.write('<div class="live-status">[API] Requesting live scraper cluster...</div>', unsafe_allow_html=True)
        # Call the local scraper directly (simplifies for MVP, matches "Full-Live UI")
        # In a real distributed system, we'd hit the FastAPI endpoint
        from scraper.playwright_scraper import run_scraper
        
        st.write('<div class="live-status">[SCRAPER] Launching Playwright (Chromium Headless)...</div>', unsafe_allow_html=True)
        try:
            results = run_scraper(keyword, location, limit)
            st.write(f'<div class="live-status">[DATA] Found {len(results)} matches. Parsing & Normalizing...</div>', unsafe_allow_html=True)
            
            # Save to DB
            new_ids = []
            for job in results:
                jid = db.insert_job(job)
                new_ids.append(jid)
            
            st.write('<div class="live-status">[UI] Injection complete. Rendering results...</div>', unsafe_allow_html=True)
            status.update(label="✅ Scouting Complete!", state="complete", expanded=False)
            return results
        except Exception as e:
            st.error(f"Scraping failed: {e}")
            status.update(label="❌ Scouting Failed", state="error")
            return []

# --- Render ---
st.markdown("""
<div class="scout-header">
    <h1 style="color:white; margin:0;">🛰️ Live Job Scouting</h1>
    <p style="color:rgba(255,255,255,0.7);">Autonomous Playwright-powered engine searching the web for your next role.</p>
</div>
""", unsafe_allow_html=True)

# Main Action Area
col_k, col_l, col_btn = st.columns([2, 1, 1])
with col_k:
    keyword = st.text_input("What role are you looking for?", placeholder="e.g. AI Engineer, Python Backend...", label_visibility="collapsed")
with col_l:
    location = st.text_input("Where?", value="Remote", placeholder="Jakarta, Singapore...", label_visibility="collapsed")
with col_btn:
    btn_search = st.button("🛰️ Search & Import", use_container_width=True, type="primary")

if btn_search:
    if not keyword:
        st.warning("Please enter a keyword to search.")
    else:
        results = trigger_live_scrape(keyword, location, 5)
        if results:
            st.balloons()
            st.success(f"Successfully imported {len(results)} live listings!")
            
            # Preview Panel
            st.subheader("📋 Latest Live Scrapes")
            for job in results:
                with st.container():
                    st.markdown(f"""
                    <div class="job-preview-card">
                        <span class="source-tag">{job.get('source', 'Web')}</span>
                        <h3 style="margin:0; color:#58a6ff;">{job['title']}</h3>
                        <p style="margin:5px 0; color:#8b949e;">🏢 {job['company']} &nbsp;•&nbsp; 📍 {job['location']}</p>
                        <p style="font-size:13px; color:#c9d1d9;">{job['description'][:150]}...</p>
                        <a href="{job['url']}" target="_blank" style="color:#1f6feb; text-decoration:none; font-size:14px; font-weight:600;">View Original Listing →</a>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No new jobs found for this search. The engine might be blocked or the keyword is too specific.")

# Secondary Options
st.divider()
with st.expander("🛠️ Manual Input & Utility"):
    tab_paste, tab_form, tab_mock = st.tabs(["📋 Paste JD", "✏️ Manual Form", "🤖 Mock Data"])
    
    with tab_paste:
        raw_jd = st.text_area("Paste JD here...", height=200)
        if st.button("Parse & Import"):
            if raw_jd:
                parsed = clawbot.parse_jd(raw_jd)
                jid = db.insert_job({
                    "title": parsed.get("title", "Unknown"),
                    "company": parsed.get("company", "Unknown"),
                    "description": raw_jd,
                    "skills_required": parsed.get("skills_required", []),
                    "experience_min": parsed.get("experience_min", 0),
                    "location": parsed.get("location", "Remote"),
                    "source": "manual_paste"
                })
                st.success(f"Job #{jid} created!")
            
    with tab_form:
        st.info("Form moved to utility for clean Scouting UX.")
        # Simpler form here if needed
        
    with tab_mock:
        if st.button("Load 15 Mock Jobs"):
            n = clawbot.load_mock_data()
            st.success(f"Loaded {n} mock jobs.")

# Footer
st.caption(f"Backend Status: [FAST-API 2.0.0] Active | Storage: {db.count_jobs()} records")
