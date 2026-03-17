import argparse
import sys
import os

# Ensure relative imports work if run directly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper.playwright_scraper import run_scraper
from matcher.embedding_matcher import FaissMatcher
from data.storage import save_jobs, load_jobs

def main():
    parser = argparse.ArgumentParser(description="CareerOS CLI - AI Job Matcher")
    parser.add_argument("--scrape", action="store_true", help="Scrape new jobs via Playwright")
    parser.add_argument("--keyword", type=str, default="Software Engineer", help="Job search keyword")
    parser.add_argument("--location", type=str, default="Remote", help="Job location")
    parser.add_argument("--profile", type=str, help="Your profile/skills to match against")
    
    args = parser.parse_args()
    
    if args.scrape:
        print(f"\n[*] Scraping jobs for '{args.keyword}' in '{args.location}' using Playwright...")
        new_jobs = run_scraper(args.keyword, args.location, limit=5)
        save_jobs(new_jobs)
        print(f"[+] Saved {len(new_jobs)} new jobs to local DB.")
        
    if args.profile:
        print("\n[*] Loading FAISS Matcher and extracting embeddings...")
        matcher = FaissMatcher("all-MiniLM-L6-v2")
        jobs = load_jobs()
        if not jobs:
            print("[-] No jobs in database. Run with --scrape first.")
            return
            
        print(f"[*] Indexing {len(jobs)} jobs into FAISS...")
        matcher.add_jobs(jobs)
        
        print(f"[*] Matching profile: '{args.profile}'\n")
        results = matcher.search(args.profile, top_k=5)
        
        print("Top Job Matches:")
        for i, res in enumerate(results):
            job = res['job']
            score = res['score']
            print(f"{i+1}. {job['title']} - Score: {score}%")
            print(f"   Company: {job['company']}")
            print(f"   URL: {job.get('url', 'N/A')}\n")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Prompt user if no arguments supplied
        print("CareerOS MVP - Command Line Interface")
        print("Run 'python main.py --help' for usage.")
        sys.exit(0)
    main()
