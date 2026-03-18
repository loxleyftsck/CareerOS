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
        "go", "rust", "typescript", "vue", "angular", "ci/cd",
        "laravel", "php", "flutter", "dart", "kotlin", "swift", "terraform"
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
            "email": None,
            "phone": None,
            "skills": [],
            "experience_years": 0.0,
            "location": "Jakarta, Indonesia", # Default
            "raw_text": text
        }

        text_lower = text.lower()
        
        # 1. Contact Info Extraction
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
        if email_match: profile["email"] = email_match.group(0)
        
        phone_match = re.search(r"(\+62|08)\d{9,12}", text.replace(" ", ""))
        if phone_match: profile["phone"] = phone_match.group(0)

        # 2. Skills Keyword Match
        for skill in self.COMMON_SKILLS:
            if re.search(rf"\b{re.escape(skill)}\b", text_lower):
                profile["skills"].append(skill.capitalize())

        # 3. Enhanced Experience Years (Handling years + months)
        # Match "X years" or "X years Y months"
        exp_match = re.search(r"(\d+)\s*years?(\s*(\d+)\s*months?)?", text_lower)
        if exp_match:
            years = float(exp_match.group(1))
            months = float(exp_match.group(3)) if exp_match.group(3) else 0
            profile["experience_years"] = years + (months / 12.0)
        
        # 4. Location Detection
        cities = ["jakarta", "bandung", "surabaya", "yogyakarta", "medan", "bali"]
        for city in cities:
            if city in text_lower:
                profile["location"] = city.capitalize()
                break

        # 5. Name extraction
        if nlp:
            doc = nlp(text[:500])
            for ent in doc.ents:
                if ent.label_ == "PERSON" and len(ent.text.split()) > 1:
                    profile["name"] = ent.text
                    break

        return profile

parser = CVParser()
