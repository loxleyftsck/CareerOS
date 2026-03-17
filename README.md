# CareerOS - Structured AI Job Matching System

## 📂 Project Architecture
The project has been refactored into a modular, production-grade structure:

- **/core**: Main logic engines (`antigravity.py`, `db.py`, `rl_engine.py`, `embedding_matcher.py`).
- **/agents**: Collection of AI agents (`clawbot.py`, `cv_parser.py`, `playwright_scraper.py`).
- **/utils**: Helper modules (`embedder.py`, `logging_util.py`).
- **/webapp**: Streamlit-based graphical user interface.
- **/cli**: Command-line interface and FastAPI server.
- **/data**: Centralized database storage (`careeros.db`, `careeros_db.json`).
- **/tests**: Validation and diagnostic suites.
- **/logs**: Persistent runtime logs.

## 🚀 Getting Started

### 1. Installation
```bash
pip install -r webapp/requirements.txt
python -m playwright install chromium
python -m spacy download en_core_web_sm
```

### 2. Run Graphical Interface (Streamlit)
```bash
python -m streamlit run webapp/app.py
```

### 3. Run Command Line Interface (v2)
```bash
# Scrape
python cli/main.py --scrape
# Match
python cli/main.py --profile "Your profile text here"
```

### 4. Run System Health Check
```bash
python tests/diagnostic.py
```

## 🛠 Tech Stack
- **AI**: SentenceTransformers (bge-small), FAISS.
- **Scraping**: Playwright, BeautifulSoup.
- **Backend**: FastAPI, SQLite.
- **UI**: Streamlit.
- **Logging**: Structured local logging in `/logs`.
