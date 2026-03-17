"""
pages/add_jobs.py — Job Ingestion: manual paste, quick form, or Clawbot search
"""

import streamlit as st
import db
import clawbot

st.title("📥 Add Jobs")
st.caption("Add jobs by pasting a description, filling the form, or running Clawbot.")
st.divider()

tab1, tab2, tab3 = st.tabs(["📋 Paste JD", "✏️ Manual Form", "🤖 Clawbot Search"])

# ── Tab 1: Paste JD ───────────────────────────────────────────────────────────
with tab1:
    st.markdown("Paste a full job description — Antigravity will auto-extract what it can.")
    raw_jd = st.text_area(
        "Job Description",
        height=250,
        placeholder="Paste the full JD here — title, requirements, skills, salary...",
        key="raw_jd",
    )

    if raw_jd.strip():
        parsed = clawbot.parse_jd(raw_jd)
        st.markdown("#### ✏️ Review & Confirm")
        with st.form("jd_confirm_form"):
            c1, c2 = st.columns(2)
            with c1:
                title   = st.text_input("Job Title *", placeholder="e.g. AI Engineer")
                company = st.text_input("Company *", placeholder="e.g. Gojek")
                loc     = st.text_input("Location", value=parsed.get("location", ""))
                url     = st.text_input("Job URL (optional)", placeholder="https://...")
            with c2:
                raw_skills = st.text_input(
                    "Skills (comma-separated)",
                    value=", ".join(parsed.get("skills_required", [])),
                )
                exp_min = st.number_input("Min Experience (yrs)", value=float(parsed.get("experience_min", 0)), min_value=0.0, step=0.5)
                exp_max = st.number_input("Max Experience (yrs)", value=float(parsed.get("experience_max", 5)), min_value=0.0, step=0.5)
                sal_jt  = st.number_input(
                    "Min Salary (juta Rp)",
                    value=int(parsed.get("salary_min", 0) // 1_000_000),
                    min_value=0, step=1,
                )

            if st.form_submit_button("💾 Save Job", type="primary", use_container_width=True):
                if not title.strip() or not company.strip():
                    st.error("Title and Company are required.")
                else:
                    skills_list = [s.strip() for s in raw_skills.split(",") if s.strip()]
                    job_id = db.insert_job({
                        "title": title.strip(),
                        "company": company.strip(),
                        "description": raw_jd[:1000],
                        "skills_required": skills_list,
                        "experience_min": exp_min,
                        "experience_max": exp_max,
                        "salary_min": sal_jt * 1_000_000,
                        "salary_max": 0,
                        "location": loc.strip(),
                        "source": "manual_paste",
                        "url": url.strip(),
                    })
                    # Clear cached results so ranking re-runs
                    st.session_state.pop("ranked_results", None)
                    st.success(f"✅ Job saved (ID #{job_id})! Go to **Results & Ranking** to analyse.")

# ── Tab 2: Manual Form ────────────────────────────────────────────────────────
with tab2:
    st.markdown("Fill in the details manually for faster entry.")
    with st.form("manual_job_form"):
        c1, c2 = st.columns(2)
        with c1:
            m_title   = st.text_input("Job Title *", placeholder="AI Engineer")
            m_company = st.text_input("Company *", placeholder="Gojek")
            m_loc     = st.text_input("Location", placeholder="Jakarta / Remote")
            m_url     = st.text_input("Job URL", placeholder="https://...")
        with c2:
            m_skills  = st.text_input("Skills Required", placeholder="Python, FastAPI, LLM")
            m_exp_min = st.number_input("Min Experience (yrs)", min_value=0.0, step=0.5)
            m_exp_max = st.number_input("Max Experience (yrs)", value=3.0, min_value=0.0, step=0.5)
            m_sal     = st.number_input("Min Salary (juta Rp)", min_value=0, step=1)

        m_desc = st.text_area("Description (optional)", height=100)

        if st.form_submit_button("💾 Save Job", type="primary", use_container_width=True):
            if not m_title.strip() or not m_company.strip():
                st.error("Title and Company are required.")
            else:
                skills_list = [s.strip() for s in m_skills.split(",") if s.strip()]
                jid = db.insert_job({
                    "title": m_title.strip(),
                    "company": m_company.strip(),
                    "description": m_desc.strip(),
                    "skills_required": skills_list,
                    "experience_min": m_exp_min,
                    "experience_max": m_exp_max,
                    "salary_min": m_sal * 1_000_000,
                    "salary_max": 0,
                    "location": m_loc.strip(),
                    "source": "manual",
                    "url": m_url.strip(),
                })
                st.session_state.pop("ranked_results", None)
                st.success(f"✅ Job saved! (ID #{jid})")

# ── Tab 3: Clawbot ────────────────────────────────────────────────────────────
with tab3:
    st.markdown("🤖 **Clawbot** searches the job database for matching roles.")
    st.caption("Phase 1: Smart search over 15+ seeded Indonesian tech jobs. Phase 2: Live scraping from Glints/Kalibrr.")

    c1, c2 = st.columns([2, 1])
    with c1:
        keyword = st.text_input("Search keyword", placeholder="AI Engineer, Python, NLP...")
    with c2:
        loc_filter = st.selectbox("Location", ["All", "Jakarta", "Remote", "Bandung"])

    if st.button("🔍 Search with Clawbot", type="primary"):
        if not keyword.strip():
            st.warning("Enter a keyword to search.")
        else:
            results = clawbot.scrape_glints(keyword, loc_filter)
            if not results:
                st.info("No results found. Try a broader keyword.")
            else:
                st.success(f"Found {len(results)} jobs. Select which to import:")
                for job in results:
                    existing = db.get_all_jobs()
                    already_in = any(
                        j["title"] == job["title"] and j["company"] == job["company"]
                        for j in existing
                    )
                    col_info, col_btn = st.columns([4, 1])
                    with col_info:
                        st.markdown(
                            f"**{job['title']}** — {job['company']}  "
                            f"| {job['location']}  "
                            f"| Rp {job['salary_min'] // 1_000_000}jt+"
                        )
                    with col_btn:
                        if already_in:
                            st.caption("✅ Saved")
                        else:
                            if st.button(f"Import", key=f"import_{job['title']}_{job['company']}"):
                                db.insert_job(job)
                                st.session_state.pop("ranked_results", None)
                                st.toast(f"Imported: {job['title']} @ {job['company']}")
                                st.rerun()

    st.divider()
    if st.button("⚡ Load ALL mock jobs at once", help="Loads all 15 seeded jobs into DB"):
        n = clawbot.load_mock_data()
        if n > 0:
            st.success(f"✅ Loaded {n} new jobs.")
            st.session_state.pop("ranked_results", None)
        else:
            st.info("All mock jobs are already loaded.")

# ── Jobs in DB footer ─────────────────────────────────────────────────────────
st.divider()
total = db.count_jobs()
st.caption(f"📦 {total} jobs currently in database.")
