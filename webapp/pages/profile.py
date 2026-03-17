"""
pages/profile.py — User Profile Builder
"""

import streamlit as st
from core import db
from agents import cv_parser

st.title("👤 My Profile")
st.caption("Fill this manually, or upload your CV to auto-fill.")
st.divider()

# Load existing profile
profile = db.get_profile()

# ── CV Upload ────────────────────────────────────────────────────────────────
with st.expander("📄 Auto-fill from CV (PDF or DOCX)", expanded=False):
    uploaded_file = st.file_uploader("Upload your resume", type=["pdf", "docx"])
    
    if uploaded_file is not None:
        if st.button("Extract Data", type="primary"):
            with st.spinner("Parsing CV..."):
                try:
                    bytes_data = uploaded_file.getvalue()
                    if uploaded_file.name.endswith('.pdf'):
                        cv_text = cv_parser.extract_text_pdf(bytes_data)
                    else:
                        cv_text = cv_parser.extract_text_docx(bytes_data)
                    
                    parsed_data = cv_parser.parse_cv(cv_text)
                    
                    # Merge with existing profile or empty dict
                    if not profile:
                        profile = {"skills": [], "target_roles": [], "name": "", "experience_years": 0.0, "location_pref": "Jakarta", "salary_min": 0, "career_goals": ""}
                    
                    # Preserve existing skills not found, add newly found ones
                    existing_skills = set(profile.get("skills", []))
                    new_skills = set(parsed_data["skills"])
                    profile["skills"] = list(existing_skills | new_skills)
                    
                    if parsed_data["experience_years"] > 0:
                        profile["experience_years"] = parsed_data["experience_years"]
                        
                    st.session_state["profile_override"] = profile
                    st.success(f"✅ Extracted {len(new_skills)} skills and {parsed_data['experience_years']} years experience!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to parse CV: {e}")

# Apply overrides if they exist
if "profile_override" in st.session_state:
    profile = st.session_state["profile_override"]

# ── Form ─────────────────────────────────────────────────────────────────────
with st.form("profile_form"):
    st.markdown("#### 📋 Basic Info")
    name = st.text_input(
        "Your name",
        value=profile["name"] if profile else "",
        placeholder="e.g. Ahmad Farid",
    )

    st.markdown("#### 🛠️ Skills")
    st.caption("Separate skills with commas")
    raw_skills = st.text_area(
        "Your skills",
        value=", ".join(profile["skills"]) if profile else "",
        placeholder="Python, FastAPI, LangChain, Docker, PostgreSQL, LLM",
        height=80,
    )

    st.markdown("#### 🎯 Target Roles")
    raw_roles = st.text_input(
        "Roles you're targeting",
        value=", ".join(profile["target_roles"]) if profile else "",
        placeholder="AI Engineer, Backend Engineer, MLOps",
    )

    st.markdown("#### 📈 Experience & Preferences")
    col1, col2 = st.columns(2)
    with col1:
        exp_years = st.number_input(
            "Years of experience",
            min_value=0.0, max_value=30.0, step=0.5,
            value=float(profile["experience_years"]) if profile else 0.0,
        )
        location_pref = st.selectbox(
            "Preferred location",
            ["Jakarta", "Remote", "Bandung", "Yogyakarta", "Surabaya", "Bali", "Other"],
            index=["Jakarta", "Remote", "Bandung", "Yogyakarta", "Surabaya", "Bali", "Other"]
                  .index(profile["location_pref"])
                  if profile and profile["location_pref"] in
                     ["Jakarta", "Remote", "Bandung", "Yogyakarta", "Surabaya", "Bali", "Other"]
                  else 0,
        )
    with col2:
        salary_million = st.number_input(
            "Minimum salary (in juta Rp)",
            min_value=0, max_value=200, step=1,
            value=int(profile["salary_min"] // 1_000_000) if profile else 0,
        )

    st.markdown("#### 🌟 Career Goals")
    career_goals = st.text_area(
        "Describe your career goals",
        value=profile["career_goals"] if profile else "",
        placeholder=(
            "I want to become a senior AI engineer in a product company, "
            "working on LLM-powered applications..."
        ),
        height=80,
    )

    submitted = st.form_submit_button("💾 Save Profile", type="primary", use_container_width=True)

if submitted:
    skills_list  = [s.strip() for s in raw_skills.split(",") if s.strip()]
    roles_list   = [r.strip() for r in raw_roles.split(",") if r.strip()]
    salary_int   = salary_million * 1_000_000

    if not skills_list:
        st.error("Please enter at least one skill.")
    elif not name.strip():
        st.error("Please enter your name.")
    else:
        db.save_profile({
            "name": name.strip(),
            "skills": skills_list,
            "experience_years": exp_years,
            "target_roles": roles_list,
            "location_pref": location_pref,
            "salary_min": salary_int,
            "career_goals": career_goals.strip(),
            "raw_cv_text": profile.get("raw_cv_text", "") if profile else ""
        })
        # Invalidate cached analysis so results page re-runs
        st.session_state.pop("ranked_results", None)
        st.success(f"✅ Profile saved! {len(skills_list)} skills, {exp_years} yrs exp, Rp {salary_million}jt min salary.")
        st.balloons()

# ── Preview ───────────────────────────────────────────────────────────────────
if profile and not submitted:
    st.divider()
    st.markdown("#### 🔍 Current Profile Preview")
    skills_html = " ".join(f'<span class="chip">{s}</span>' for s in profile["skills"])
    st.markdown(f"**Skills:** {skills_html}", unsafe_allow_html=True)
    st.markdown(f"**Experience:** {profile['experience_years']} years")
    st.markdown(f"**Location:** {profile['location_pref']}  |  **Min Salary:** Rp {profile['salary_min']:,}")
    if profile.get("career_goals"):
        st.info(f"🎯 {profile['career_goals']}")
