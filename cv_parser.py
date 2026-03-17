import re
import spacy
import fitz  # PyMuPDF
import docx
from typing import Dict, List

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    pass

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


def extract_text_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF byte stream."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = []
    for page in doc:
        text.append(page.get_text())
    return "\n".join(text)


def extract_text_docx(file_bytes: bytes) -> str:
    """Extract text from a DOCX byte stream."""
    from io import BytesIO
    doc = docx.Document(BytesIO(file_bytes))
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])


def parse_cv(text: str) -> Dict:
    """
    Parse unstructured CV text to extract skills and estimate experience.
    Uses regex + spaCy NLP for extraction.
    """
    doc = nlp(text)
    text_lower = text.lower()
    
    # 1. Extract Skills
    found_skills = set()
    for skill in COMMON_SKILLS:
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.add(skill)
            
    # 2. Estimate Experience Years
    years = re.findall(r'\b(199\d|20[0-2]\d)\b', text)
    exp_years = 0.0
    if years:
        years = [int(y) for y in years]
        min_year = min(years)
        max_year = max(years)
        from datetime import datetime
        current_year = datetime.now().year
        if re.search(r'\b(present|now|current)\b', text_lower):
            max_year = current_year
        calculated = max_year - min_year
        if 0 < calculated <= 40:
            exp_years = float(calculated)
            
    if exp_years == 0:
        exp_matches = re.findall(r'(\d+)[\+\-]?\s*(?:year|yr)s?\s*(?:of\s*)?(?:experience)', text_lower)
        if exp_matches:
            try:
                exp_years = float(exp_matches[0])
            except ValueError:
                pass

    return {
        "skills": list(found_skills),
        "experience_years": exp_years,
        "raw_text": text[:2000]
    }
