import time
import json
import logging
import os
from typing import Dict, Any, Optional, List

# Setup specialized logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CrispDecision")

class DecisionState:
    """Stateful memory for a specific module's decision path."""
    def __init__(self, module: str, initial_method: str):
        self.module = module
        self.last_method = initial_method
        self.last_context_value = 0.0
        self.last_switch_time = time.time()
        self.confidence = 1.0
        self.switch_count = 0
        self.adaptive_buffer = 0.10  # Initial 10%
        self.volatility = 0.0
        self.history: List[Dict] = []
        self.performance_history: List[float] = []

class CrispDecisionEngine:
    """
    Production-Hardened Meta-Controller for CareerOS v4.0.
    Features: Adaptive Buffering, Critical Overrides, Cost-Aware Switching.
    """
    
    def __init__(self, log_dir: str = "logs"):
        self.log_path = os.path.join(log_dir, "decisions.jsonl")
        os.makedirs(log_dir, exist_ok=True)

        # Base Thresholds
        self.thresholds = {
            "matching_volume": {"ab": 500, "bc": 50000},
            "memory_depth": {"ab": 30, "bc": 200},
            "radar_lifespan": {"ab": 72, "bc": 12}, 
        }
        
        # Resource Costs (Lower is better)
        self.costs = {
            "A": 1.0,   # Local/O(N)
            "B": 5.0,   # Semantic/O(N)
            "C": 12.0,  # Reranker/O(N^2)
            "D": 30.0   # Full LLM/Agent
        }
        
        # Performance Targets
        self.min_recall = 0.65
        self.min_switch_interval = 60 
        self.states: Dict[str, DecisionState] = {}

    def _get_state(self, module: str, default_method: str) -> DecisionState:
        if module not in self.states:
            self.states[module] = DecisionState(module, default_method)
        return self.states[module]

    def _calculate_utility(self, method: str, raw_score: float) -> float:
        """Utility = Performance Score - (Cost Weight / 10)"""
        cost_penalty = self.costs.get(method, 10.0) / 100.0
        return raw_score - cost_penalty

    def _update_adaptive_buffer(self, state: DecisionState):
        """Increase buffer if switching too frequently (Anti-jitter)."""
        if state.switch_count > 5:
            state.adaptive_buffer = min(0.30, state.adaptive_buffer + 0.05)
            state.switch_count = 0 # reset window
        elif state.adaptive_buffer > 0.10:
            state.adaptive_buffer -= 0.01 # slow decay

    def _should_switch(self, state: DecisionState, current_val: float, val_low: float, val_high: float, ascending: bool = True) -> Optional[str]:
        # Strict v4.0 Hysteresis Logic (±10% from state.adaptive_buffer)
        buffer = state.adaptive_buffer
        
        if ascending:
            # Transition A -> B
            if state.last_method == "A" and current_val > val_low * (1 + buffer):
                return "B"
            # Transition B -> A
            if state.last_method == "B" and current_val < val_low * (1 - buffer):
                return "A"
            # Transition B -> C
            if state.last_method == "B" and current_val > val_high * (1 + buffer):
                return "C"
            # Transition C -> B
            if state.last_method == "C" and current_val < val_high * (1 - buffer):
                return "B"
        else:
            # Inverse logic for descending axes (like radar lifespan)
            if state.last_method == "A" and current_val < val_low * (1 - buffer):
                return "B"
            if state.last_method == "B" and current_val > val_low * (1 + buffer):
                return "A"
            if state.last_method == "B" and current_val < val_high * (1 - buffer):
                return "C"
            if state.last_method == "C" and current_val > val_high * (1 + buffer):
                return "B"
        
        return None

    def decide_matching(self, job_count: int, recall_score: float = 1.0) -> str:
        """v4.0 API: Hysteresis-aware matching strategy decision."""
        state = self._get_state("matching", "A")
        
        # Check Cooldown (Strict 60s)
        if (time.time() - state.last_switch_time) < self.min_switch_interval:
            return state.last_method

        is_critical = recall_score < self.min_recall
        if is_critical:
            new_method = "C"
            reason = "CRITICAL_DEGRADATION"
        else:
            new_method = self._should_switch(
                state, job_count, 
                self.thresholds["matching_volume"]["ab"],
                self.thresholds["matching_volume"]["bc"]
            ) or state.last_method
            reason = "Threshold check"

        return self._finalize(state, new_method, job_count, is_critical, reason)

    def decide_memory(self, history_count: int) -> str:
        """v4.0 API: Hysteresis-aware memory strategy decision."""
        state = self._get_state("memory", "A")
        
        # Check Cooldown (Strict 60s)
        if (time.time() - state.last_switch_time) < self.min_switch_interval:
            return state.last_method

        new_method = self._should_switch(
            state, history_count,
            self.thresholds["memory_depth"]["ab"],
            self.thresholds["memory_depth"]["bc"]
        ) or state.last_method
        return self._finalize(state, new_method, history_count)

    def decide_resume(self, seniority: int, specificity: float, dream_job: bool = False) -> str:
        state = self._get_state("resume", "A")
        
        # Cost-aware priority
        if dream_job:
            new_method = "D"
            reason = "User-flagged Priority"
        elif seniority >= 8 or specificity > 0.8:
            new_method = "C"
            reason = "High complexity"
        elif seniority >= 3 or specificity > 0.4:
            new_method = "B"
            reason = "Medium complexity"
        else:
            new_method = "A"
            reason = "Standard flow"
            
        return self._finalize(state, new_method, specificity, dream_job, reason)

    def decide_radar(self, avg_lifespan_hours: float) -> str:
        state = self._get_state("radar", "A")
        new_method = self._should_switch(
            state, avg_lifespan_hours,
            self.thresholds["radar_lifespan"]["ab"],
            self.thresholds["radar_lifespan"]["bc"],
            ascending=False
        ) or state.last_method
        return self._finalize(state, new_method, avg_lifespan_hours)

    def _calculate_confidence(self, state: DecisionState, context_val: float) -> float:
        """Confidence drops if near threshold or high volatility."""
        # Simple distance-based confidence for demonstration
        # In a real system, we'd check against historical accuracy
        volatility_penalty = min(0.4, state.adaptive_buffer - 0.10)
        return max(0.1, 1.0 - volatility_penalty)

    def _finalize(self, state: DecisionState, new_method: str, context_val: float, is_critical: bool = False, reason: str = "") -> str:
        current_time = time.time()
        is_switch = new_method != state.last_method
        
        # Anti-oscillation with Critical Override
        if is_switch and not is_critical and (current_time - state.last_switch_time < self.min_switch_interval):
            logger.debug(f"Stability Hold: {state.module} kept at {state.last_method}")
            return state.last_method

        if is_switch:
            self._update_adaptive_buffer(state)
            log_entry = {
                "timestamp": current_time,
                "module": state.module,
                "context_val": context_val,
                "method_old": state.last_method,
                "method_new": new_method,
                "reason": reason or "Threshold crossover",
                "switch": True,
                "buffer": state.adaptive_buffer,
                "is_critical": is_critical
            }
            self._log_decision(log_entry)
            
            state.last_method = new_method
            state.last_switch_time = current_time
            state.switch_count += 1
            
        state.last_context_value = context_val
        state.confidence = self._calculate_confidence(state, context_val)
        return new_method

    def _log_decision(self, entry: Dict):
        """Append to local history."""
        try:
            with open(self.log_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error(f"Logging failed: {e}")

    def update_performance(self, module: str, score: float):
        """Lapisan 3: Update state based on reality."""
        if module in self.states:
            state = self.states[module]
            state.performance_history.append(score)
            if len(state.performance_history) > 100:
                state.performance_history.pop(0)

# Singleton manager
engine = CrispDecisionEngine()
