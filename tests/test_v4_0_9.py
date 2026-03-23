import sys
import os
import unittest

# Add project root to path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from storage import db

class TestMultiProfileSupport(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Ensure DB is initialized
        db.init_db()
        
    def test_multi_profile_lifecycle(self):
        # 1. Create Profile A
        profile_a = {
            "name": "Alice Backend",
            "skills": ["Python", "Django", "SQL"],
            "target_roles": ["Backend Engineer"]
        }
        id_a = db.save_profile(profile_a)
        
        # 2. Create Profile B
        profile_b = {
            "name": "Alice Data Science",
            "skills": ["Python", "Pandas", "Scikit-Learn"],
            "target_roles": ["Data Scientist"]
        }
        id_b = db.save_profile(profile_b)
        
        self.assertNotEqual(id_a, id_b, "Profiles should have distinct IDs")
        
        # 3. Retrieve all
        all_profs = db.get_all_profiles()
        self.assertGreaterEqual(len(all_profs), 2)
        
        # 4. Set A active
        db.set_active_profile(id_a)
        active_prof = db.get_profile()
        self.assertEqual(active_prof["id"], id_a)
        self.assertEqual(active_prof["name"], "Alice Backend")
        
        # 5. Set B active
        db.set_active_profile(id_b)
        active_prof = db.get_profile()
        self.assertEqual(active_prof["id"], id_b)
        self.assertEqual(active_prof["name"], "Alice Data Science")
        
        # 6. Fetch explicitly by ID
        prof_a_explicit = db.get_profile(id_a)
        self.assertEqual(prof_a_explicit["name"], "Alice Backend")

if __name__ == "__main__":
    unittest.main()
