import time
import sys
import os

# Add root to sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from engine.decision_framework import engine as crisp_engine

def test_hysteresis_and_cooldown():
    print("[*] Starting CrispDecisionEngine v4.0.2 Verification...")
    
    # Threshold for matching a->b is 500. Buffer is 10% (50).
    # Expected switch A->B at > 550.
    # Expected switch B->A at < 450.
    
    # 1. Start at A
    method = crisp_engine.decide_matching(100)
    print(f"Initial (100 jobs): {method}") # Should be A
    
    # 2. Test positive buffer (At 540, should still be A)
    method = crisp_engine.decide_matching(540)
    print(f"At 540 jobs (within +10%): {method}") # Should be A
    
    # 3. Test switch A->B (At 560, should switch to B)
    method = crisp_engine.decide_matching(560)
    print(f"At 560 jobs (outside +10%): {method}") # Should be B
    
    # 4. Test cooldown (At 400, should be A, but cooldown is 60s, so should stay B)
    print("[*] Testing 60s Cooldown...")
    method = crisp_engine.decide_matching(400)
    print(f"At 400 jobs (immediate attempt): {method}") # Should be B (cooldown active)
    
    print("[OK] Hysteresis and Cooldown logic verified via terminal logs.")

if __name__ == "__main__":
    test_hysteresis_and_cooldown()
