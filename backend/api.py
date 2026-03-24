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

from storage import db
from engine.scoring import fast_scoring as antigravity
from scraper.playwright_scraper import run_scraper
from agents.cv_parser import parser as cv_parser
from utils import logging_util
from fastapi import File, UploadFile
import shutil

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

from engine.orchestrator import conductor

@app.post("/scrape", summary="Trigger live Playwright scraping (Energy Optimized)")
async def trigger_scrape(req: ScrapeRequest):
    global scraping_status
    scraping_status["status"] = "running"
    try:
        # Load profile for context
        profile = db.get_profile() or {"skills": [], "experience_years": 0}
        
        logger.info(f"Orchestrating scout for {req.keyword}...")
        jobs = conductor.scout_and_rank(profile, req.keyword, req.location, req.limit)
        
        scraping_status = {
            "status": "completed",
            "last_run": str(logging_util.datetime.now()),
            "count": len(jobs)
        }
        return {"message": "Success", "jobs_found": len(jobs), "results": jobs}
    except Exception as e:
        scraping_status["status"] = "failed"
        logger.error(f"Orchestration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/match")
def match_all(profile: ProfileRequest):
    jobs = db.get_all_jobs()
    if not jobs:
        return {"matches": []}
    
    # Run Orchestrator's process logic directly
    ranked = conductor._process_jobs(jobs, profile.model_dump())
    return {"matches": ranked}

class FeedbackRequest(BaseModel):
    job_id: int
    action: str
    reward: float

@app.post("/feedback")
def record_feedback(req: FeedbackRequest):
    job = db.get_job(req.job_id)
    profile = db.get_profile()
    if not job or not profile:
        raise HTTPException(status_code=404, detail="Job or Profile not found")
        
    db.record_feedback(req.job_id, req.action, req.reward)
    conductor.rl_engine.update(job, profile, req.action, req.reward)
    return {"message": "Feedback recorded and RL engine updated"}

from fastapi.responses import StreamingResponse
import json

@app.get("/scrape/stream")
def stream_scrape(keyword: str, location: str = "Remote", limit: int = 5):
    """Event-stream for live scraper results."""
    profile = db.get_profile() or {"skills": [], "experience_years": 0}
    
    def generate():
        for job in conductor.scout_streaming(profile, keyword, location, limit):
            yield f"data: {json.dumps(job)}\n\n"
            
    return StreamingResponse(generate(), media_type="text/event-stream")

@app.post("/profile/upload", summary="Upload and parse CV (PDF/DOCX)")
async def upload_cv(file: UploadFile = File(...)):
    # Create temp directory
    temp_dir = os.path.join(ROOT_DIR, "data", "uploads")
    os.makedirs(temp_dir, exist_ok=True)
    
    file_path = os.path.join(temp_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        profile_data = cv_parser.parse(file_path)
        
        # Save to DB (Creates a new profile)
        profile_id = db.save_profile({
            "name": profile_data["name"],
            "skills": profile_data["skills"],
            "experience_years": profile_data["experience_years"],
            "raw_cv_text": profile_data["raw_text"]
        })
        
        return {
            "message": "CV uploaded and parsed successfully",
            "profile_id": profile_id,
            "profile": profile_data
        }
    except Exception as e:
        logger.error(f"CV Parsing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        pass

# ── Interview Coach Endpoint (v5.0) ──────────────────────────────────────────

@app.get("/coach", summary="Generate interview prep questions for a job")
def get_coaching_session(job_id: int):
    """Returns gap-based interview questions for the given job vs. active profile."""
    from engine.agents.interview_coach import coach_for_job
    profile = db.get_profile()
    if not profile:
        raise HTTPException(status_code=404, detail="No active profile")
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return coach_for_job(job, profile)


# ── Multi-Profile Endpoints (v4.0.9) ─────────────────────────────────────────

@app.get("/profiles", summary="List all saved profiles")
def list_profiles():
    profiles = db.get_all_profiles()
    return {"profiles": profiles, "count": len(profiles)}

@app.post("/profiles/{profile_id}/activate", summary="Switch active profile")
def activate_profile(profile_id: int):
    profile = db.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found")
    db.set_active_profile(profile_id)
    return {"message": f"Profile {profile_id} ({profile['name']}) is now active"}

@app.delete("/profiles/{profile_id}", summary="Delete a profile")
def remove_profile(profile_id: int):
    profile = db.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found")
    db.delete_profile(profile_id)
    return {"message": f"Profile {profile_id} deleted"}

@app.get("/profiles/active", summary="Get currently active profile")
def get_active_profile():
    profile = db.get_profile()
    if not profile:
        raise HTTPException(status_code=404, detail="No active profile")
    return profile


if __name__ == "__main__":
    db.init_db()
    uvicorn.run(app, host="0.0.0.0", port=8000)
