from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn
import os
import sys

# Ensure relative imports work if run directly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.storage import load_jobs
from matcher.embedding_matcher import FaissMatcher

app = FastAPI(title="CareerOS API", description="FastAPI interface for CareerOS AI Matcher")

matcher = FaissMatcher("all-MiniLM-L6-v2")
loaded = False

def init_matcher():
    global loaded
    if not loaded:
        jobs = load_jobs()
        if jobs:
            matcher.add_jobs(jobs)
        loaded = True

class ProfileReq(BaseModel):
    profile_text: str
    top_k: int = 5

@app.on_event("startup")
def startup_event():
    init_matcher()

@app.post("/match", summary="Match a profile text against scraped jobs")
def match_jobs(req: ProfileReq) -> Dict[str, Any]:
    init_matcher() # ensure loaded
    results = matcher.search(req.profile_text, top_k=req.top_k)
    return {"matches": results}

@app.get("/jobs", summary="Get all scraped jobs")
def get_jobs() -> Dict[str, Any]:
    jobs = load_jobs()
    return {"total": len(jobs), "jobs": jobs}

if __name__ == "__main__":
    print("[*] Starting CareerOS FastAPI Server on http://localhost:8000")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
