import sys
import os

# Add root to sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from agents.cv_parser import parser

def test_cv_parsing_v4_0_6():
    print("[*] Starting CVParser v4.0.6 Verification...")
    
    cv_text = """
    Budi Santoso
    Senior Software Engineer
    Email: budi.santoso@example.com
    Phone: +62 812 3456 7890
    Location: Bandung, West Java
    
    Experience: 
    5 years 6 months of professional experience in web development.
    
    Skills:
    - Flutter & Dart for mobile
    - Laravel & PHP for backend
    - React & TypeScript for frontend
    - Go for microservices
    """
    
    print("[*] Extracting info from mock CV...")
    profile = parser.extract_info(cv_text)
    
    print(f"Name: {profile['name']}")
    print(f"Email: {profile['email']}")
    print(f"Phone: {profile['phone']}")
    print(f"Skills: {profile['skills']}")
    print(f"Experience: {profile['experience_years']} years")
    print(f"Location: {profile['location']}")
    
    # Assertions
    assert "Budi Santoso" in profile["name"]
    assert profile["email"] == "budi.santoso@example.com"
    assert "81234567890" in profile["phone"]
    assert "Flutter" in profile["skills"]
    assert "Laravel" in profile["skills"]
    assert "Go" in profile["skills"]
    assert profile["experience_years"] == 5.5
    assert profile["location"] == "Bandung"
    
    print("[OK] CVParser v4.0.6 verification successful!")

if __name__ == "__main__":
    test_cv_parsing_v4_0_6()
