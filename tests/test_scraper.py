import sys
import os

# Ensure root is in path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from agents.playwright_scraper import run_scraper

def test_scraper():
    print("[*] Testing Scraper...")
    jobs = run_scraper("AI", "Jakarta", limit=2)
    print(f"[+] Scraped {len(jobs)} jobs.")
    for j in jobs:
        print(f"  - {j['title']} @ {j['company']} ({j['source']})")

if __name__ == "__main__":
    test_scraper()
