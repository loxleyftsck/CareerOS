from typing import List, Dict, Any
from collections import deque
import time

class ShortTermMemory:
    """
    Volatile session-based memory for high-frequency context.
    Tracks last N user actions and system decisions.
    """
    def __init__(self, size: int = 50):
        self.buffer = deque(maxlen=size)

    def record(self, action_type: str, data: Dict[str, Any]):
        entry = {
            "timestamp": time.time(),
            "type": action_type,
            "data": data
        }
        self.buffer.append(entry)

    def get_recent_actions(self, n: int = 5) -> List[Dict]:
        return list(self.buffer)[-n:]

    def clear(self):
        self.buffer.clear()

# Singleton instance
session_memory = ShortTermMemory()
