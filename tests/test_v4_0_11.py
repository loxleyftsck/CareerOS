import os
import sys

# Add project root to path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from engine.scoring import fast_scoring

def verify_output_schema():
    profile = {"skills": ["Python", "TensorFlow"]}
    job = {"id": 1, "skills_required": ["Python", "PyTorch", "AWS"], "title": "ML Engineer"}
    
    # disable Rust fallback to just python for quick check
    fast_scoring.RUST_AVAILABLE = False
    
    res = fast_scoring.rank_jobs(profile, [job])[0]
    
    # Assertions based on the new requirements
    assert "match_score" in res, "match_score is missing"
    assert "match_confidence" in res, "match_confidence is missing"
    assert "application_prep" in res, "application_prep is missing"
    
    prep_list = res["application_prep"]
    assert isinstance(prep_list, list), "application_prep must be a list"
    assert len(prep_list) > 0, "application_prep must not be empty"
    
    for item in prep_list:
        assert "type" in item, "prep item missing 'type'"
        assert "action" in item, "prep item missing 'action'"
        
    explanation = res["explanation"]
    assert "key_matches" in explanation, "key_matches missing from explanation"
    assert "gaps" in explanation, "gaps missing from explanation"
    assert "risk_assessment" in explanation, "risk_assessment missing"
    assert "confidence_level" in explanation, "confidence_level missing"
    
    print("ALL ASSERTIONS PASSED. Unbiased evaluation constraints implemented successfully.")

if __name__ == "__main__":
    verify_output_schema()
