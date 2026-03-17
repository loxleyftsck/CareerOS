import sys
import os
import unittest
import numpy as np

# Ensure project root is in path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from core import antigravity

class TestMatcher(unittest.TestCase):
    def test_skill_score_exact(self):
        """Exact keyword match should return 100 on keyword component."""
        user_skills = ["Python", "Docker"]
        job_skills = ["Python", "Docker"]
        # With no embeddings, it uses keyword overlap
        score = antigravity.compute_skill_score(None, None, user_skills, job_skills)
        self.assertEqual(score, 100.0)

    def test_skill_score_partial(self):
        """Partial keyword match."""
        user_skills = ["Python"]
        job_skills = ["Python", "FastAPI"]
        score = antigravity.compute_skill_score(None, None, user_skills, job_skills)
        self.assertGreater(score, 0)
        self.assertLess(score, 100)

    def test_exp_score_perfect(self):
        """Within range experience."""
        score = antigravity.compute_exp_score(user_exp=3.0, job_exp_min=2.0, job_exp_max=5.0)
        self.assertEqual(score, 100.0)

    def test_exp_score_under(self):
        """Underqualified penalty."""
        score = antigravity.compute_exp_score(user_exp=1.0, job_exp_min=3.0, job_exp_max=5.0)
        self.assertLess(score, 100.0)

    def test_location_score_match(self):
        """Location match."""
        score = antigravity.compute_location_score("Jakarta", "South Jakarta")
        self.assertEqual(score, 100.0)

    def test_location_score_remote(self):
        """Remote always high."""
        score = antigravity.compute_location_score("Bandung", "Remote")
        self.assertEqual(score, 88.0)

if __name__ == "__main__":
    unittest.main()
