"""
clawbot.py — Job data ingestion for CareerOS
Phase 1: Realistic seeded mock data (15+ Indonesian tech jobs)
Phase 2: Semi-auto scraper for Glints public pages
"""

from typing import List, Dict, Optional
import re
import sys
import os

# Ensure we can find the project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from storage import db
from utils import logging_util
logger = logging_util.get_logger(__name__)

# ── Mock Dataset (Phase 1) ────────────────────────────────────────────────────

MOCK_JOBS: List[Dict] = [
    {
        "title": "AI Engineer",
        "company": "Gojek",
        "description": (
            "Join Gojek's AI team to build LLM-powered features across the super-app. "
            "You will design RAG pipelines, fine-tune models, and deploy AI agents at scale. "
            "Strong Python and FastAPI skills required."
        ),
        "skills_required": ["Python", "FastAPI", "LLM", "LangChain", "Docker", "PostgreSQL"],
        "experience_min": 1.0,
        "experience_max": 4.0,
        "salary_min": 18000000,
        "salary_max": 30000000,
        "location": "Jakarta",
        "source": "clawbot_mock",
        "url": "https://glints.com/id/jobs/ai-engineer-gojek",
    },
    {
        "title": "Backend Engineer (Python)",
        "company": "Tokopedia",
        "description": (
            "Build and scale Tokopedia's e-commerce backend. "
            "Work with high-traffic microservices using Python, Kafka, and Redis. "
            "3+ years experience required."
        ),
        "skills_required": ["Python", "FastAPI", "Kafka", "Redis", "PostgreSQL", "Docker"],
        "experience_min": 2.0,
        "experience_max": 5.0,
        "salary_min": 20000000,
        "salary_max": 35000000,
        "location": "Jakarta",
        "source": "clawbot_mock",
        "url": "https://www.tokopedia.com/careers/backend-engineer",
    },
    {
        "title": "Machine Learning Engineer",
        "company": "Traveloka",
        "description": (
            "Design and deploy ML models for pricing, recommendations, and fraud detection. "
            "Experience with MLOps and model serving required."
        ),
        "skills_required": ["Python", "TensorFlow", "PyTorch", "MLOps", "Kubernetes", "SQL"],
        "experience_min": 2.0,
        "experience_max": 6.0,
        "salary_min": 22000000,
        "salary_max": 40000000,
        "location": "Jakarta",
        "source": "clawbot_mock",
        "url": "https://www.traveloka.com/id-id/careers",
    },
    {
        "title": "Junior Python Developer",
        "company": "Xendit",
        "description": (
            "Build payment processing APIs and integrations. "
            "Fresh graduates welcome. Python, REST APIs, and basic SQL required."
        ),
        "skills_required": ["Python", "REST API", "SQL", "Git"],
        "experience_min": 0.0,
        "experience_max": 2.0,
        "salary_min": 10000000,
        "salary_max": 18000000,
        "location": "Jakarta",
        "source": "clawbot_mock",
        "url": "https://www.xendit.co/id/careers",
    },
    {
        "title": "Data Engineer",
        "company": "GoTo",
        "description": (
            "Build reliable data pipelines using Airflow, dbt, and Spark. "
            "Maintain data warehouse and ensure data quality across GoTo ecosystem."
        ),
        "skills_required": ["Python", "Spark", "Airflow", "dbt", "SQL", "BigQuery"],
        "experience_min": 2.0,
        "experience_max": 5.0,
        "salary_min": 20000000,
        "salary_max": 35000000,
        "location": "Jakarta",
        "source": "clawbot_mock",
        "url": "https://www.gotogroup.com/careers",
    },
    {
        "title": "Frontend Engineer (React)",
        "company": "Ruangguru",
        "description": (
            "Build beautiful, accessible ed-tech interfaces with React and TypeScript. "
            "Work closely with product and design teams."
        ),
        "skills_required": ["React", "TypeScript", "Next.js", "CSS", "REST API"],
        "experience_min": 1.0,
        "experience_max": 4.0,
        "salary_min": 12000000,
        "salary_max": 22000000,
        "location": "Jakarta",
        "source": "clawbot_mock",
        "url": "https://www.ruangguru.com/careers",
    },
    {
        "title": "DevOps / MLOps Engineer",
        "company": "Shopee",
        "description": (
            "Manage infrastructure for ML training and serving. "
            "Set up CI/CD, Kubernetes clusters, and monitoring for AI services."
        ),
        "skills_required": ["Kubernetes", "Docker", "CI/CD", "Python", "Terraform", "AWS"],
        "experience_min": 2.0,
        "experience_max": 5.0,
        "salary_min": 18000000,
        "salary_max": 32000000,
        "location": "Jakarta",
        "source": "clawbot_mock",
        "url": "https://careers.shopee.id",
    },
    {
        "title": "AI / NLP Engineer",
        "company": "Bukalapak",
        "description": (
            "Build NLP and conversational AI features for Bukalapak's marketplace. "
            "Experience with transformers, LLMs, and embedding models required."
        ),
        "skills_required": ["Python", "NLP", "Transformers", "LLM", "FastAPI", "Redis"],
        "experience_min": 1.5,
        "experience_max": 4.0,
        "salary_min": 16000000,
        "salary_max": 28000000,
        "location": "Bandung",
        "source": "clawbot_mock",
        "url": "https://karir.bukalapak.com",
    },
    {
        "title": "Software Engineer (Remote)",
        "company": "Privy",
        "description": (
            "Build secure digital signature infrastructure. "
            "Remote-first culture, flexible hours. Python and Go experience preferred."
        ),
        "skills_required": ["Python", "Go", "Microservices", "PostgreSQL", "Docker"],
        "experience_min": 1.0,
        "experience_max": 4.0,
        "salary_min": 14000000,
        "salary_max": 24000000,
        "location": "Remote",
        "source": "clawbot_mock",
        "url": "https://privy.id/careers",
    },
    {
        "title": "Junior AI Engineer",
        "company": "Kalibrr",
        "description": (
            "Work on AI-powered job matching and candidate ranking systems. "
            "Great entry-level role for AI/ML enthusiasts. Python required."
        ),
        "skills_required": ["Python", "Machine Learning", "SQL", "scikit-learn", "REST API"],
        "experience_min": 0.0,
        "experience_max": 2.0,
        "salary_min": 9000000,
        "salary_max": 16000000,
        "location": "Jakarta",
        "source": "clawbot_mock",
        "url": "https://www.kalibrr.id/careers",
    },
    {
        "title": "Backend Engineer (Node.js)",
        "company": "OVO",
        "description": (
            "Build payment and fintech APIs using Node.js and TypeScript. "
            "Experience with event-driven systems and financial domain preferred."
        ),
        "skills_required": ["Node.js", "TypeScript", "Kafka", "PostgreSQL", "Docker"],
        "experience_min": 2.0,
        "experience_max": 5.0,
        "salary_min": 18000000,
        "salary_max": 30000000,
        "location": "Jakarta",
        "source": "clawbot_mock",
        "url": "https://www.ovo.id/careers",
    },
    {
        "title": "Senior ML Engineer",
        "company": "Grab",
        "description": (
            "Lead ML initiatives for Grab's Indonesia operations. "
            "Own end-to-end ML lifecycle from data collection to production serving."
        ),
        "skills_required": ["Python", "PyTorch", "MLOps", "Spark", "Kubernetes", "Leadership"],
        "experience_min": 5.0,
        "experience_max": 9.0,
        "salary_min": 35000000,
        "salary_max": 60000000,
        "location": "Jakarta",
        "source": "clawbot_mock",
        "url": "https://grab.careers",
    },
    {
        "title": "Full Stack Developer (Python + React)",
        "company": "DANA",
        "description": (
            "Build and maintain fintech features across backend (Python/Django) "
            "and frontend (React). Full-stack, fast-paced team."
        ),
        "skills_required": ["Python", "Django", "React", "PostgreSQL", "REST API", "Git"],
        "experience_min": 1.5,
        "experience_max": 4.0,
        "salary_min": 15000000,
        "salary_max": 25000000,
        "location": "Jakarta",
        "source": "clawbot_mock",
        "url": "https://www.dana.id/careers",
    },
    {
        "title": "LangGraph / AI Agent Engineer",
        "company": "Zenius",
        "description": (
            "Build autonomous AI agents for adaptive learning using LangGraph and CrewAI. "
            "You will design multi-agent workflows, RAG pipelines, and agentic loops."
        ),
        "skills_required": ["Python", "LangGraph", "CrewAI", "LLM", "RAG", "FastAPI"],
        "experience_min": 0.5,
        "experience_max": 3.0,
        "salary_min": 12000000,
        "salary_max": 22000000,
        "location": "Remote",
        "source": "clawbot_mock",
        "url": "https://www.zenius.net/careers",
    },
    {
        "title": "Data Analyst",
        "company": "Tiket.com",
        "description": (
            "Analyze travel booking data, build dashboards, and provide business insights. "
            "SQL, Python, and Tableau skills required."
        ),
        "skills_required": ["SQL", "Python", "Tableau", "Excel", "Data Analysis"],
        "experience_min": 0.5,
        "experience_max": 3.0,
        "salary_min": 9000000,
        "salary_max": 16000000,
        "location": "Jakarta",
        "source": "clawbot_mock",
        "url": "https://www.tiket.com/careers",
    },
    {
        "title": "Flutter Developer",
        "company": "Halodoc",
        "description": "Build high-quality cross-platform healthcare mobile apps with Flutter and Dart.",
        "skills_required": ["Flutter", "Dart", "Firebase", "REST API", "Git"],
        "experience_min": 1.0,
        "experience_max": 4.0,
        "salary_min": 15000000,
        "salary_max": 25000000,
        "location": "Remote",
        "source": "clawbot_mock",
        "url": "https://www.halodoc.com/karir",
    },
    {
        "title": "iOS Developer",
        "company": "LinkAja",
        "description": "Join our fintech team to build seamless iOS payment experiences.",
        "skills_required": ["Swift", "SwiftUI", "CocoaPods", "REST API", "Git"],
        "experience_min": 2.0,
        "experience_max": 5.0,
        "salary_min": 18000000,
        "salary_max": 32000000,
        "location": "Jakarta",
        "source": "clawbot_mock",
        "url": "https://www.linkaja.id/karir",
    },
    {
        "title": "Cybersecurity Analyst",
        "company": "Telkom Indonesia",
        "description": "Protect the nation's digital infrastructure. Monitor, detect, and respond to threats.",
        "skills_required": ["SIEM", "Pentesting", "Networking", "Linux", "Python"],
        "experience_min": 2.0,
        "experience_max": 5.0,
        "salary_min": 15000000,
        "salary_max": 28000000,
        "location": "Bandung",
        "source": "clawbot_mock",
        "url": "https://telkom.co.id/careers",
    },
    {
        "title": "Cloud Engineer (AWS)",
        "company": "Traveloka",
        "description": "Optimize and secure our AWS infrastructure for scale.",
        "skills_required": ["AWS", "Terraform", "Kubernetes", "Python", "Linux"],
        "experience_min": 3.0,
        "experience_max": 7.0,
        "salary_min": 25000000,
        "salary_max": 45000000,
        "location": "Jakarta",
        "source": "clawbot_mock",
        "url": "https://www.traveloka.com/id-id/careers",
    },
    {
        "title": "Golang Backend Developer",
        "company": "Kopi Kenangan",
        "description": "Build scalable retail-tech services using Go and microservices.",
        "skills_required": ["Go", "Microservices", "PostgreSQL", "Kafka", "Docker"],
        "experience_min": 2.0,
        "experience_max": 5.0,
        "salary_min": 18000000,
        "salary_max": 30000000,
        "location": "South Jakarta",
        "source": "clawbot_mock",
        "url": "https://kopikenangan.com/careers",
    },
    {
        "title": "Ruby on Rails Developer",
        "company": "Bukalapak",
        "description": "Maintain and enhance Bukalapak's core shopping engine.",
        "skills_required": ["Ruby", "Ruby on Rails", "PostgreSQL", "Redis", "Git"],
        "experience_min": 3.0,
        "experience_max": 6.0,
        "salary_min": 20000000,
        "salary_max": 35000000,
        "location": "Jakarta",
        "source": "clawbot_mock",
        "url": "https://karir.bukalapak.com",
    },
    {
        "title": "Product Manager (AI)",
        "company": "Ajaib",
        "description": "Lead AI/ML product initiatives for Indonesia's favorite investing app.",
        "skills_required": ["Product Management", "AI/ML", "SQL", "Data Analysis", "Agile"],
        "experience_min": 3.0,
        "experience_max": 6.0,
        "salary_min": 25000000,
        "salary_max": 45000000,
        "location": "Jakarta",
        "source": "clawbot_mock",
        "url": "https://ajaib.co.id/careers",
    },
    {
        "title": "UI/UX Designer",
        "company": "Bibit",
        "description": "Design user-centric investment experiences for millions of Indonesians.",
        "skills_required": ["Figma", "Design Systems", "Prototyping", "User Research"],
        "experience_min": 2.0,
        "experience_max": 5.0,
        "salary_min": 12000000,
        "salary_max": 22000000,
        "location": "Jakarta",
        "source": "clawbot_mock",
        "url": "https://bibit.id/careers",
    },
    {
        "title": "QA Automation Engineer",
        "company": "Bobobox",
        "description": "Build and maintain automated test suites for our IoT-enabled pods.",
        "skills_required": ["Selenium", "Appium", "Python", "CI/CD", "Jira"],
        "experience_min": 2.0,
        "experience_max": 4.0,
        "salary_min": 12000000,
        "salary_max": 20000000,
        "location": "Bandung",
        "source": "clawbot_mock",
        "url": "https://bobobox.co.id/careers",
    },
    {
        "title": "ML Research Scientist",
        "company": "NeuralID",
        "description": "Push the boundaries of NLP and Speech Recognition for Indonesian languages.",
        "skills_required": ["Python", "PyTorch", "NLP", "Research", "Mathematics"],
        "experience_min": 3.0,
        "experience_max": 8.0,
        "salary_min": 30000000,
        "salary_max": 55000000,
        "location": "Remote",
        "source": "clawbot_mock",
        "url": "https://neuralid.ai/careers",
    },
    {
        "title": "Site Reliability Engineer",
        "company": "Stockbit",
        "description": "Ensure high availability and reliability for our online trading platform.",
        "skills_required": ["Kubernetes", "AWS", "Terraform", "Python", "Prometheus"],
        "experience_min": 3.0,
        "experience_max": 6.0,
        "salary_min": 22000000,
        "salary_max": 38000000,
        "location": "Jakarta",
        "source": "clawbot_mock",
        "url": "https://stockbit.com/careers",
    },
    {
        "title": "BlockChain Developer",
        "company": "Pintu",
        "description": "Build secure crypto trading and web3 wallet features.",
        "skills_required": ["Solidity", "Rust", "Go", "Cryptography", "Ethereum"],
        "experience_min": 2.0,
        "experience_max": 5.0,
        "salary_min": 25000000,
        "salary_max": 45000000,
        "location": "Jakarta",
        "source": "clawbot_mock",
        "url": "https://pintu.co.id/careers",
    },
    {
        "title": "Technical Writer",
        "company": "Midtrans",
        "description": "Create amazing documentation for our payments API.",
        "skills_required": ["Technical Writing", "API Documentation", "Git", "Markdown"],
        "experience_min": 1.0,
        "experience_max": 4.0,
        "salary_min": 10000000,
        "salary_max": 18000000,
        "location": "Jakarta",
        "source": "clawbot_mock",
        "url": "https://midtrans.com/careers",
    },
    {
        "title": "Hardware/Embedded Engineer",
        "company": "eFishery",
        "description": "Build the future of aquaculture with our smart feeding devices.",
        "skills_required": ["C", "C++", "Embedded Systems", "IoT", "PCB Design"],
        "experience_min": 2.0,
        "experience_max": 5.0,
        "salary_min": 14000000,
        "salary_max": 25000000,
        "location": "Bandung",
        "source": "clawbot_mock",
        "url": "https://efishery.com/careers",
    }
]


# ── JD Text Parser ────────────────────────────────────────────────────────────

COMMON_SKILLS = [
    "Python", "JavaScript", "TypeScript", "Java", "Go", "Rust", "C++", "C#",
    "React", "Next.js", "Vue", "Angular", "Node.js", "Express",
    "FastAPI", "Django", "Flask", "Spring Boot",
    "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
    "Docker", "Kubernetes", "Terraform", "AWS", "GCP", "Azure",
    "LLM", "LangChain", "LangGraph", "CrewAI", "RAG", "Embeddings",
    "Machine Learning", "Deep Learning", "NLP", "PyTorch", "TensorFlow",
    "MLOps", "Airflow", "Spark", "Kafka", "dbt", "BigQuery",
    "Git", "CI/CD", "REST API", "Microservices", "GraphQL",
    "scikit-learn", "Pandas", "NumPy", "Transformers",
]

SALARY_PATTERN = re.compile(
    r"Rp\.?\s*([\d.,]+)\s*[Jj]uta|"
    r"([\d.,]+)\s*[Jj]uta|"
    r"IDR\s*([\d.,]+)|"
    r"salary[:\s]+([\d.,]+)",
    re.IGNORECASE
)

EXP_PATTERN = re.compile(
    r"(\d+)[\+\-]?\s*(?:year|tahun|yr)s?\s*(?:of\s*)?(?:experience|pengalaman)",
    re.IGNORECASE
)


def parse_jd(raw_text: str) -> Dict:
    """
    Extract structured fields from pasted JD text.
    Returns partial dict — user fills in remaining fields via form.
    """
    lines = [l.strip() for l in raw_text.strip().splitlines() if l.strip()]

    # Skills: scan all text for known skill keywords
    text_lower = raw_text.lower()
    skills_found = [s for s in COMMON_SKILLS if s.lower() in text_lower]

    # Experience years
    exp_matches = EXP_PATTERN.findall(raw_text)
    exp_years = int(exp_matches[0]) if exp_matches else 0

    # Salary — convert to IDR int
    sal_matches = SALARY_PATTERN.findall(raw_text)
    salary_min = 0
    for groups in sal_matches:
        val = next((g for g in groups if g), None)
        if val:
            val_clean = val.replace(",", "").replace(".", "")
            try:
                salary_min = int(val_clean) * 1_000_000
                break
            except ValueError:
                pass

    # Remote detection
    location_hint = ""
    if any(k in text_lower for k in ("remote", "wfh", "work from home")):
        location_hint = "Remote"
    elif "jakarta" in text_lower:
        location_hint = "Jakarta"
    elif "bandung" in text_lower:
        location_hint = "Bandung"

    return {
        "skills_required": skills_found[:12],
        "experience_min": float(exp_years),
        "experience_max": float(exp_years + 2),
        "salary_min": salary_min,
        "location": location_hint,
        "description": raw_text[:1000],
    }


# ── Glints Scraper (Phase 2 stub) ─────────────────────────────────────────────

def scrape_glints(keyword: str, location: str = "jakarta", limit: int = 10) -> List[Dict]:
    """
    Scrape Glints public job listings.
    Returns list of job dicts compatible with db.insert_job().
    Phase 1: Returns mock data filtered by keyword.
    Phase 2: Real HTTP scraping (requires requests + BeautifulSoup).
    """
    keyword_lower = keyword.lower()
    results = [
        j for j in MOCK_JOBS
        if keyword_lower in j["title"].lower()
        or keyword_lower in j["description"].lower()
        or any(keyword_lower in s.lower() for s in j["skills_required"])
    ]
    return results[:limit] if results else MOCK_JOBS[:limit]


# ── Loader ────────────────────────────────────────────────────────────────────

def load_mock_data() -> int:
    """Insert all mock jobs into DB. Skips duplicates by title+company."""
    existing = {(j["title"], j["company"]) for j in db.get_all_jobs()}
    inserted = 0
    for job in MOCK_JOBS:
        if (job["title"], job["company"]) not in existing:
            db.insert_job(job)
            inserted += 1
    return inserted
