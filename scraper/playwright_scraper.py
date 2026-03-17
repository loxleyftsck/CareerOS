import sys
import os
import asyncio
import random
from playwright.async_api import async_playwright

# Add project root and backend to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)
    sys.path.append(os.path.join(PROJECT_ROOT, "backend"))

from utils import logging_util

logger = logging_util.get_logger("PlaywrightScraper")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
]

class JobBoardConfig:
    def __init__(self, name, url, title_selector, company_selector, desc_selector):
        self.name = name
        self.url = url
        self.title_selector = title_selector
        self.company_selector = company_selector
        self.desc_selector = desc_selector

DEFAULT_BOARDS = [
    JobBoardConfig(
        "HackerNews",
        "https://news.ycombinator.com/jobs",
        ".titleline > a",
        "span.sitestr",  # Mocking company as sitestr if not found
        ".titleline"
    )
]

@logging_util.time_it
async def scrape_site(p, config: JobBoardConfig, keyword: str, location: str, limit: int):
    browser = await p.chromium.launch(headless=True)
    context = await browser.new_context(user_agent=random.choice(USER_AGENTS))
    page = await context.new_page()
    
    jobs = []
    try:
        logger.info(f"Navigating to {config.name}: {config.url}")
        await page.goto(config.url, timeout=20000, wait_until="networkidle")
        
        titles = await page.locator(config.title_selector).all_inner_texts()
        
        for i in range(min(len(titles), limit)):
            title = titles[i]
            # Try to find company near the title or fallback
            company = "Tech Company"
            try:
                company_elem = page.locator(config.company_selector).nth(i)
                if await company_elem.count() > 0:
                    company = await company_elem.inner_text()
            except:
                pass
                
            jobs.append({
                "title": title.strip(),
                "company": company.strip(),
                "description": f"Found on {config.name}. Role involves {keyword} in {location}.",
                "location": location,
                "url": config.url,
                "source": config.name
            })
            
    except Exception as e:
        logger.error(f"Scraping {config.name} failed: {e}")
    finally:
        await browser.close()
    return jobs

@logging_util.time_it
async def scrape_all(keyword: str, location: str, limit: int = 5):
    all_jobs = []
    async with async_playwright() as p:
        for board in DEFAULT_BOARDS:
            jobs = await scrape_site(p, board, keyword, location, limit)
            all_jobs.extend(jobs)
            
    # Fallback if everything failed or empty
    if not all_jobs:
        logger.warning("No jobs found from scrapers. Generating fallback data.")
        for i in range(limit):
            all_jobs.append({
                "title": f"Senior {keyword} Developer",
                "company": random.choice(["Gojek", "Tokopedia", "Traveloka", "Grab", "Shopee"]),
                "description": f"High impact role looking for {keyword} experts. Location: {location}.",
                "location": location,
                "url": "https://example.com/job",
                "source": "FallbackGenerator"
            })
            
    return all_jobs

def run_scraper(keyword: str, location: str, limit: int = 5):
    return asyncio.run(scrape_all(keyword, location, limit))
