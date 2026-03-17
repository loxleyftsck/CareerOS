import sys
import os
import unittest

# Ensure project root is in path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from core import rl_engine, db

class TestRL(unittest.TestCase):
    def setUp(self):
        db.init_db()

    def test_state_key_generation(self):
        """Verify state keys are consistent and categorized correctly."""
        job = {
            "skills_required": ["Python", "Docker"],
            "experience_min": 5,
            "location": "Jakarta"
        }
        profile = {"skills": ["Python"]}
        key = rl_engine._state_key(job, profile)
        # Expected: backend (python) : senior (5) : jakarta
        self.assertEqual(key, "backend:senior:jakarta")

    def test_q_update(self):
        """Verify Q-values change after an update."""
        job = {"skills_required": ["React"], "experience_min": 1, "location": "Remote", "id": 1}
        profile = {"skills": ["JS"]}
        
        key = rl_engine._state_key(job, profile)
        initial_q = db.get_q_value(key)
        
        # Action: apply (+2 reward)
        rl_engine.update(job, profile, "apply")
        new_q = db.get_q_value(key)
        
        self.assertNotEqual(initial_q, new_q)
        self.assertGreater(new_q, initial_q)

if __name__ == "__main__":
    unittest.main()
