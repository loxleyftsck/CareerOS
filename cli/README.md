# CareerOS - CLI & FastAPI MVP

An AI-powered local job matching system built strictly per the required fixed tech stack: Python, FastAPI, Playwright, SentenceTransformers, and FAISS.

## 1. System Overview
CareerOS automates the job search pipeline entirely locally. 
- **Scraper**: Uses Playwright to asynchronously scrape job postings.
- **Matcher**: Uses `SentenceTransformers` to convert job descriptions and your CV profile into semantic vector embeddings. `FAISS` calculates instantaneous inner-product (cosine) similarity between your profile and thousands of jobs.
- **Storage**: Jobs are saved locally to `careeros_db.json`.
- **Interface**: Operates primarily as a CLI tool (`main.py`) with a secondary FastAPI REST server (`api.py`) for frontend integrations.

## 2. Project Structure
```text
/careeros/cli
├── api.py
├── main.py
├── requirements.txt
├── README.md
├── scraper/
│   └── playwright_scraper.py
├── matcher/
│   └── embedding_matcher.py
└── data/
    └── storage.py
```

## 3. How to Run

### Step 1: Install Dependencies
Open your terminal and navigate to this folder, then install the Python libraries:
```bash
pip install -r requirements.txt
```

### Step 2: Install Playwright Browser
Playwright requires browser binaries to run headless scraping:
```bash
playwright install chromium
```

### Step 3: Scrape Jobs (CLI)
Run the scraper to gather job listings on a specific keyword:
```bash
python main.py --scrape --keyword "Software Engineer" --location "Remote"
```

### Step 4: Match Profile (CLI)
Query the local FAISS index against your personal profile:
```bash
python main.py --profile "I am a backend developer experienced in Python, FastAPI, and Docker."
```

### Alternative: Run FastAPI Server
To run the REST backend:
```bash
python api.py
```
Navigate to `http://localhost:8000/docs` to use the Swagger UI.

## 4. Sample Output
```text
[*] Matching profile: 'I am a backend developer experienced in Python, FastAPI, and Docker.'

Top Job Matches:
1. Senior Software Engineer - Score: 87.5%
   Company: Tech Startup
   URL: https://news.ycombinator.com/jobs

2. Backend Developer - Score: 81.2%
   Company: Google
   URL: https://example.com/job
```
