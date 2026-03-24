<div align="center">

# 🚀 CareerOS

### AI-Powered Career Matching Agent — Find Jobs That Match *You*, Not Just Your Keywords

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![Rust](https://img.shields.io/badge/Rust-PyO3%20Accelerated-orange?logo=rust)](https://www.rust-lang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status: Active](https://img.shields.io/badge/Status-Active%20Development-brightgreen)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen.svg)](CONTRIBUTING.md)

</div>

---

> **CareerOS** is a local-first AI job matching engine that uses Reinforcement Learning, semantic scoring, and Explainable AI to connect developers with opportunities that truly fit their trajectory — not just their resume keywords.

<!-- DEMO PLACEHOLDER -->
> 📸 *Demo GIF / Screenshot coming soon — run `streamlit run frontend/app.py` to see it live*

---

## 🎯 Overview & Key Features

**Why CareerOS?**

Most job boards rank jobs by recency. CareerOS ranks them by **Expected Value (EV)** — a composite score that accounts for skill fit, experience alignment, market signals, and your historical outcomes.

| Feature | Description |
|---|---|
| 🧠 **RL Job Ranking** | Q-table RL engine learns from your apply/skip/interview history |
| 🦀 **Rust-Accelerated Scoring** | `compute_exp_score`, `compute_tech_fit` via PyO3 — 10x faster bulk scoring |
| 📊 **Explainable AI** | Every score has `key_matches`, `gaps`, `risk_assessment`, `application_prep` |
| 🎭 **Multi-Profile Support** | Manage multiple career personas & resumes side-by-side |
| 🔍 **Live Scraping** | Resilient Playwright scraper with exponential backoff + multi-board fallback |
| 📋 **Auto Reports** | Daily/weekly markdown reports with cluster heat maps |
| 🧪 **Career Path Simulator** | "What if I learned Kubernetes?" — see delta EV across all your jobs |
| 🗣️ **Interview Coach** | Gap-based Q&A prep generated from each job's skill requirements |
| 🩺 **Accuracy Benchmark** | 6-category automated test suite for scoring engine health |

---

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.10+, Rust toolchain (for Rust-Core)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### Installation

```bash
# 1. Clone
git clone https://github.com/loxleyftsck/CareerOS.git
cd CareerOS

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Build Rust-Core extension (optional, falls back to Python)
cd rust_core
pip install maturin
maturin develop --release
cd ..

# 5. Initialize database
python -c "from storage.db import init_db; init_db()"
```

### Run

```bash
# Streamlit Dashboard (recommended)
streamlit run frontend/app.py

# FastAPI Backend
python backend/api.py

# CLI
python careeros_cli.py --help
```

---

## 🏗️ Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **Scoring Engine** | Python + Rust (PyO3) | Pure python for flexibility, Rust for hot-path performance |
| **RL Engine** | Custom Q-table | Full control over reward shaping & state representation |
| **Scraping** | Playwright (async) | Handles JS-heavy job boards; resilient with retry & UA rotation |
| **Backend API** | FastAPI + Uvicorn | Async-first, auto-generated OpenAPI docs |
| **Frontend** | Streamlit | Rapid UI iteration; ships as single Python file per page |
| **Database** | SQLite | Local-first; zero-config, portable, fast |
| **CV Parsing** | spaCy + PyMuPDF | Indonesian-aware skill extraction from PDF/DOCX |
| **Reporting** | Markdown + Plotly | Human-readable reports + interactive dashboard charts |

---

## 📋 Development Roadmap

| Phase | Status | Goal |
|---|---|---|
| **v1.0** — Foundation | ✅ Done | Scraper + basic scoring + SQLite schema |
| **v2.0** — Intelligence | ✅ Done | RL engine + semantic matching + full dashboard |
| **v4.0** — Precision | 🚧 Active | Rust-core, multi-profile, auto-reports, CLI, benchmark |
| **v5.0** — Scale | 📅 Q2 2025 | Cloud deploy, embedding search, Telegram bot |
| **v6.0** — Community | 📅 Q3 2025 | Plugin API, custom RL policies, contributor SDK |

### v4.0 Patch Log
- `[PATCH v4.0.1]` Main entry + structure alignment
- `[PATCH v4.0.2]` CrispDecisionEngine (hysteresis + cooldown)
- `[PATCH v4.0.3]` RL Engine — `user:cluster` states, reward schedule
- `[PATCH v4.0.4]` Matching Engine EV formula
- `[PATCH v4.0.5–6]` Memory system + Indonesian CV parser
- `[PATCH v4.0.7]` Rust-Core acceleration
- `[PATCH v4.0.8–9]` Scraper resilience + multi-profile
- `[PATCH v4.0.10–14]` Reporting, eval schema, CLI, cluster heat map

---

## 📁 Project Structure

```
CareerOS/
├── agents/                  # CV parser, Interview Coach
├── backend/                 # FastAPI API layer
├── engine/
│   ├── scoring/             # fast_scoring, dimensions, utils
│   ├── rl/                  # Q-table RL engine
│   ├── memory/              # ShortTermMemory, LongTermMemory
│   ├── reporting/           # Auto-report generator
│   └── orchestrator.py      # Main workflow coordinator
├── frontend/
│   ├── app.py               # Streamlit entry point
│   └── pages/               # Dashboard, Profile, Results, Tracker, Reports
├── rust_core/               # PyO3 Rust extension (compute_exp_score etc.)
├── scraper/                 # Playwright async scraper
├── storage/                 # SQLite db.py
├── tests/                   # Accuracy benchmark + unit tests
├── rnd/                     # R&D sandbox (career path simulator etc.)
└── careeros_cli.py          # CLI entry point
```

---

## 🌐 API Endpoints (FastAPI)

```
GET  /health                    — System health check
POST /scrape                    — Trigger live Playwright job scraping
GET  /scrape/stream             — SSE stream of live scraping results
POST /match                     — Rank all DB jobs against a profile
POST /feedback                  — Record outcome + update RL engine
POST /profile/upload            — Upload & parse CV (PDF/DOCX)
GET  /profiles                  — List all profiles
POST /profiles/{id}/activate    — Switch active profile
DELETE /profiles/{id}           — Delete a profile
```

Full interactive docs: `http://localhost:8000/docs`

---

## 🌳 Branching Strategy

```
main        ← Production-ready (stable)
staging     ← Integration & pre-release testing
dev         ← Active development & feature integration
rnd/*       ← Experimental sandbox (not merged until proven)
feature/*   ← New modular components
hotfix/*    ← Emergency patches
```

---

## 🤝 Contributing

We welcome contributions of all sizes — bug fixes, new scrapers, improved RL policies, or documentation.

### Getting Started

```bash
# Fork → clone → create branch
git checkout -b feature/your-feature-name

# Make changes, test
python tests/accuracy_benchmark.py

# Commit using convention
git commit -m "feat(scoring): add salary_fit dimension"

# Push & open PR
git push origin feature/your-feature-name
```

### Commit Convention

```
feat(scope)    — New feature
fix(scope)     — Bug fix
chore(scope)   — Config / setup
rnd(scope)     — Experimental, not production-ready
patch(scope)   — Incremental improvement
```

**Scopes:** `scoring`, `rl`, `scraper`, `frontend`, `api`, `memory`, `reporting`, `cli`, `rnd`, `db`

### PR Checklist

- [ ] `python tests/accuracy_benchmark.py` passes (score ≥ 80%)
- [ ] `python verify_rust.py` parity check passes (if touching scoring)
- [ ] Follows commit convention above
- [ ] Patch/PR description explains *why*, not just *what*

---

## 🧪 Testing

```bash
# Full accuracy benchmark (6 categories, must score ≥ 80%)
python tests/accuracy_benchmark.py

# Rust/Python parity check
python verify_rust.py

# Specific patch test
python tests/test_v4_0_11.py
```

---

## ⚡ CLI Reference

```bash
python careeros_cli.py scout    --skill "Python" --location "Jakarta" --limit 20
python careeros_cli.py report   [--weekly]
python careeros_cli.py profiles [--activate 2] [--delete 3]
python careeros_cli.py simulate --skill "Kubernetes"
python careeros_cli.py benchmark
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with Antigravity** 🛸

⭐ Star this repo if you find it useful — it helps more developers discover CareerOS!

[🐛 Report Bug](https://github.com/loxleyftsck/CareerOS/issues) · [💡 Request Feature](https://github.com/loxleyftsck/CareerOS/issues) · [📖 Wiki](https://github.com/loxleyftsck/CareerOS/wiki)

</div>
