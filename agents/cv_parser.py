import fitz  # PyMuPDF
import docx
import spacy
import re
from typing import Dict, List, Any
import os

# Load spaCy model (ensure it's downloaded: python -m spacy download en_core_web_sm)
try:
    nlp = spacy.load("en_core_web_sm")
except:
    # Silent fail or logger if not found
    nlp = None

class CVParser:
    """
    Parses resume files (PDF, DOCX) and extracts structured profile data.
    """
    
    COMMON_SKILLS = [
        "python", "javascript", "react", "node", "docker", "kubernetes", 
        "aws", "gcp", "azure", "sql", "postgresql", "fastapi", "flask",
        "tensorflow", "pytorch", "machine learning", "ai", "java", "c++",
        "go", "rust", "typescript", "vue", "angular", "ci/cd"
    ]

    def extract_text_from_pdf(self, file_path: str) -> str:
        text = ""
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
        return text

    def extract_text_from_docx(self, file_path: str) -> str:
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    def parse(self, file_path: str) -> Dict[str, Any]:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            text = self.extract_text_from_pdf(file_path)
        elif ext == ".docx":
            text = self.extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        return self.extract_info(text)

    def extract_info(self, text: str) -> Dict[str, Any]:
        profile = {
            "name": "Extracted User",
            "skills": [],
            "experience_years": 0,
            "raw_text": text
        }

        # 1. Simple Keyword Match for Skills
        text_lower = text.lower()
        for skill in self.COMMON_SKILLS:
            if re.search(rf"\b{re.escape(skill)}\b", text_lower):
                profile["skills"].append(skill.capitalize())

        # 2. Heuristic for Experience Years
        # Look for numbers near "years" and "experience"
        exp_match = re.search(r"(\d+)\+?\s*years?\s*of?\s*experience", text_lower)
        if exp_match:
            profile["experience_years"] = float(exp_match.group(1))
        
        # 3. Name extraction (Very basic heuristic)
        if nlp:
            doc = nlp(text[:500]) # Only check first 500 chars
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    profile["name"] = ent.text
                    break

        return profile

parser = CVParser()
