# CareerOS 🚀

**AI-powered local job matching engine. Runs on your laptop. Finds your next job faster.**

---

## ⚡ Quick Start (2 commands)

```bash
pip install -r requirements.txt
streamlit run app.py
```

Opens at → **http://localhost:8501**

---

## 📁 Structure

```
careeros/
├── app.py              ← Streamlit entry + navigation
├── antigravity.py      ← AI scoring engine (50/20/15/15 weights)
├── rl_engine.py        ← CARL-DTN Q-table (reinforcement learning)
├── embedder.py         ← bge-small-en-v1.5 embedding model
├── clawbot.py          ← Job scraper + 15 mock Indonesian tech jobs
├── db.py               ← SQLite data layer
├── pages/
│   ├── dashboard.py    ← Stats + top matches
│   ├── profile.py      ← Set your skills, exp, salary prefs
│   ├── add_jobs.py     ← Paste JD / manual form / Clawbot search
│   ├── results.py      ← AI ranked jobs with gauge charts
│   └── tracker.py      ← Kanban: Saved → Applied → Interview → Offer
├── careeros.db         ← Auto-created SQLite file
├── requirements.txt
└── .streamlit/config.toml  ← Dark neon theme
```

---

## 🧠 How Antigravity Scores Jobs

```
UTILITY = 0.50 × skill_match
        + 0.20 × experience_fit
        + 0.15 × location_match
        + 0.15 × growth_potential
```

- **Skill Match**: cosine similarity (bge-small embeddings) + keyword overlap
- **Experience Fit**: gap penalty (under/overqualified)
- **Location Match**: tiered map (Jakarta=1.0, Remote=0.88, etc.)
- **Growth Potential**: company prestige + salary fit + future skills + RL boost

### Recommendation Tiers
| Score | Label |
|---|---|
| ≥85% | 🟢 HIGH_PRIORITY_APPLY |
| 70–85% | 🟡 CONSIDER_STRONGLY |
| 55–70% | 🟠 REVIEW |
| <55% | 🔴 LOW_PRIORITY |

---

## 🔄 CARL-DTN RL Loop

Every time you click **Applied / Interested / Skip**, the RL engine updates its Q-table:

```
Q(s,a) ← Q(s,a) + α[R + γ·max Q(s',a') − Q(s,a)]
α=0.15, γ=0.90
Rewards: Apply=+2, Interest=+1, Skip=−1
```

Similar jobs get ranked higher/lower on the next analysis run.

---

## 🔧 Requirements

- Python 3.11+
- `sentence-transformers` (downloads bge-small on first run, ~130MB)
- `PyMuPDF`, `python-docx`, `spacy` (for CV Parsing)
- Everything else is in `requirements.txt`

### Initial Setup
```bash
pip install -r requirements.txt
pip install PyMuPDF python-docx spacy
python -m spacy download en_core_web_sm
streamlit run app.py
```

---

## 🤖 Clawbot

Phase 1 (now): 15 seeded Indonesian tech jobs (Gojek, GoTo, Tokopedia, Traveloka, Xendit…)  
Phase 2: Real scraping via `requests + BeautifulSoup` targeting Glints/Kalibrr

---

## 💡 Sample Output

```
#1  AI Engineer @ Gojek                        92.4%   🟢 HIGH_PRIORITY_APPLY
    Skills: Python/FastAPI/LangChain match 95%.
    Experience perfect fit. Jakarta ideal. Gojek prestige 0.95.

#2  LangGraph/AI Agent Engineer @ Zenius       85.1%   🟢 HIGH_PRIORITY_APPLY
    LangGraph + CrewAI exact match. Remote-friendly.

#3  Junior AI Engineer @ Kalibrr              74.3%   🟡 CONSIDER_STRONGLY
    Core Python/ML match. Gaps: Docker (learnable in 2 weeks).
```
