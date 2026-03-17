from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import os
import sys
import logging

# Ensure project root and backend are in path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)
    sys.path.append(os.path.join(ROOT_DIR, "backend"))

from core import db, antigravity
from scraper.playwright_scraper import run_scraper
from utils import logging_util

logger = logging_util.get_logger("BackendAPI")

app = FastAPI(
    title="CareerOS Backend",
    description="Live AI Job Scouting & Matching Engine",
    version="2.0.0"
)

# --- Models ---
class ScrapeRequest(BaseModel):
    keyword: str
    location: str = "Remote"
    limit: int = 5

class ProfileRequest(BaseModel):
    name: str
    skills: List[str]
    experience_years: float
    salary_min: int = 0
    location_pref: str = "Remote"

# --- State ---
scraping_status = {"status": "idle", "last_run": None, "count": 0}

# --- Endpoints ---

@app.get("/health")
def health():
    return {"status": "healthy", "database": db.DB_PATH.name}

@app.post("/scrape", summary="Trigger live Playwright scraping")
async def trigger_scrape(req: ScrapeRequest):
    global scraping_status
    scraping_status["status"] = "running"
    try:
        logger.info(f"Triggering live scrape for {req.keyword} in {req.location}")
        jobs = run_scraper(req.keyword, req.location, req.limit)
        
        # Save to DB
        new_count = 0
        for job in jobs:
            db.insert_job(job)
            new_count += 1
            
        scraping_status = {
            "status": "completed",
            "last_run": str(logging_util.datetime.now()),
            "count": new_count
        }
        return {"message": "Scraping completed", "jobs_found": new_count, "results": jobs}
    except Exception as e:
        scraping_status["status"] = "failed"
        logger.error(f"Scrape failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/scrape/status")
def get_scrape_status():
    return scraping_status

@app.get("/jobs")
def list_jobs(status: Optional[str] = None):
    return db.get_all_jobs(status_filter=status)

@app.post("/match")
def match_all(profile: ProfileRequest):
    jobs = db.get_all_jobs()
    if not jobs:
        return {"matches": []}
    
    # Run ranking engine
    ranked = antigravity.rank_jobs(profile.model_dump(), jobs)
    return {"matches": ranked}

if __name__ == "__main__":
    db.init_db()
    uvicorn.run(app, host="0.0.0.0", port=8000)
