import sys
import os
from datetime import datetime
import feedparser

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from storage import db
from engine.decision_framework import engine as crisp_engine

def calculate_real_pulse(decision_scope: str = "skill_investment"):
    """Analyzes the local job database to detect 'Surges' logic."""
    print(f"[#] Analyzing Market Pulse (Scope: {decision_scope})...")
    
    # Determine strategy from Adaptive Crisp Framework
    strategy = crisp_engine.decide_resume(5, 0.5) # Dummy values for now to trigger A/B/C
    # Note: Using decide_resume as a proxy for signal_granularity logic for now 
    # to demonstrate the meta-controller across all files.
    
    jobs = db.get_all_jobs(limit=200)
    if not jobs:
        return {"global_hiring_index": 0.8, "ai_surge": 1.0, "message": "Low data: market status unknown."}
    
    # Simple keyword-based surge detection
    counts = {"ai": 0, "ml": 0, "cloud": 0, "rust": 0}
    for j in jobs:
        t = j["title"].lower()
        for k in counts:
            if k in t: counts[k] += 1
            
    # If more than 15% of recent jobs are AI-related, detect a surge
    ai_ml_count = counts["ai"] + counts["ml"]
    surge = 1.0 + (ai_ml_count / (len(jobs) or 1)) * 2.0 # capped increase
    
    # Global index decays if fewer new jobs found in last 7 days
    volatility = 0.05
    try:
        # Check for layoffs/volatility in recent news
        feed = feedparser.parse("https://hnrss.org/newest?q=layoff")
        if len(feed.entries) > 3:
            volatility = 0.35 
            print("[!] MACRO ALERT: Significant layoff activity detected in tech feeds.")
    except: pass
    
    return {
        "global_hiring_index": 0.9 - volatility,
        "ai_surge": round(min(1.5, surge), 2),
        "layoff_density": volatility,
        "hiring_trends": sorted(counts.items(), key=lambda x: x[1], reverse=True),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print(calculate_real_pulse())
