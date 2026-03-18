# CareerOS: AI-Powered Career Matching Agent

CareerOS is an intelligent job matching and career development agent that leverages semantic understanding, reinforcement learning, and explainable AI to bridge the gap between job seekers and their ideal opportunities.

## 🎯 Vision
To become the most precise and transparent AI career agent—one that doesn't just find jobs, but understands careers.

## 🚀 Development Roadmap

### Phase 1: R&D (Research & Experiment)
*   Semantic kernel prototypes.
*   RL policy exploration for job matching.
*   High-performance scoring engines (Rust + Python).

### Phase 2: Development (Dev)
*   Modular engine implementation.
*   Autonomous scrapers (Clawbot).
*   FastAPI backend & React frontend integration.

### Phase 3: Staging (Pre-release)
*   Integration testing & performance tuning.
*   RL feedback loop calibration.
*   Global market pulse integration.

### Phase 4: Production (Stable)
*   Scalable deployment.
*   Continuous monitoring & RL recalibration.

## 🌳 Branching Strategy
*   `main`: Production-ready code (stable).
*   `staging`: Integration and pre-release testing.
*   `dev`: Active development and feature integration.
*   `rnd/*`: Experimental features and researchers' sandbox.
*   `feature/*`: New modular components.
*   `hotfix/*`: Emergency patches for the production line.

## 🧪 Commit Convention
We follow a structured commit lifecycle:
- `feat(scope)`: New features.
- `fix(scope)`: Bug fixes.
- `chore(scope)`: Setup/configuration.
- `rnd(scope)`: Experimental changes.

Scopes: `(rnd)`, `(dev)`, `(staging)`, `(prod)`.

## 🛠️ Suggested Tech Stack
- **Backend**: Python (FastAPI) for agility + Rust (PyO3) for high-performance ranking.
- **AI/RL Engine**: Custom implementation for maximum control over reward signals.
- **Storage**: SQLite (Local-first) for portable, high-speed profile & Q-table management.

---
Built with Antigravity & Clawbot.
