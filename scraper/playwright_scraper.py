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

from functools import wraps

def async_retry(retries=3, delay=2, backoff=2):
    """Exponential backoff decorator for async functions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            m_retries, m_delay = retries, delay
            while m_retries > 1:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"Retrying {func.__name__} due to: {e}. Retries left: {m_retries-1}")
                    await asyncio.sleep(m_delay)
                    m_retries -= 1
                    m_delay *= backoff
            return await func(*args, **kwargs)
        return wrapper
    return decorator

class JobBoardConfig:
    def __init__(self, name, url, title_selectors, company_selectors, desc_selectors):
        self.name = name
        self.url = url
        # Support both single strings and lists for resilience
        self.title_selectors = title_selectors if isinstance(title_selectors, list) else [title_selectors]
        self.company_selectors = company_selectors if isinstance(company_selectors, list) else [company_selectors]
        self.desc_selectors = desc_selectors if isinstance(desc_selectors, list) else [desc_selectors]

DEFAULT_BOARDS = [
    JobBoardConfig(
        "HackerNews",
        "https://news.ycombinator.com/jobs",
        [".titleline > a", "td.title > a"],
        ["span.sitestr", ".comhead"],
        [".titleline"]
    ),
    JobBoardConfig(
        "Glints",
        "https://glints.com/id/en/lowongan-kerja",
        ["h3[class*='JobCardSc__JobTitle']", ".DesignSystemJobCard-module__title___2N_M1"],
        ["a[class*='JobCardSc__CompanyName']", ".DesignSystemJobCard-module__companyName___3G6H-"],
        ["div[class*='JobCardSc__JobDescription']"]
    )
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
]

async def get_resilient_locator(page, selectors):
    """Tries multiple selectors until one hits."""
    for selector in selectors:
        locator = page.locator(selector)
        if await locator.count() > 0:
            return locator
    return None

@async_retry(retries=3, delay=5)
async def scrape_site(p, config: JobBoardConfig, keyword: str, location: str, limit: int):
    browser = await p.chromium.launch(headless=True)
    context = await browser.new_context(user_agent=random.choice(USER_AGENTS))
    page = await context.new_page()
    
    jobs = []
    try:
        logger.info(f"Navigating to {config.name}: {config.url}")
        # Human-like delay
        await asyncio.sleep(random.uniform(1, 3))
        
        await page.goto(config.url, timeout=30000, wait_until="domcontentloaded")
        
        # Try to find titles using resilient locators
        title_locator = await get_resilient_locator(page, config.title_selectors)
        if not title_locator:
            raise ValueError(f"No titles found for {config.name} using selectors: {config.title_selectors}")
            
        titles = await title_locator.all_inner_texts()
        
        for i in range(min(len(titles), limit)):
            title = titles[i]
            company = "Tech Company"
            
            # Try resilient company selectors
            company_locator = await get_resilient_locator(page, [f"{s}:nth-child({i+1})" for s in config.company_selectors])
            if company_locator:
                company = await company_locator.first.inner_text()
                
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
        raise # Raise to trigger @async_retry
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

# Streaming stub stays simple
async def scrape_all_streaming(keyword: str, location: str, limit: int = 5):
    all_jobs = await scrape_all(keyword, location, limit)
    for j in all_jobs:
        yield j

def run_scraper_streaming(keyword: str, location: str, limit: int = 5):
    """Sync generator wrapper."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    gen = scrape_all_streaming(keyword, location, limit)
    try:
        while True:
            try:
                job = loop.run_until_complete(gen.__anext__())
                yield job
            except StopAsyncIteration:
                break
    finally:
        loop.close()
