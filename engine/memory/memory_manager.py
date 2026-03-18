import time
from typing import Dict, List, Any
from storage import db
from utils import logging_util

logger = logging_util.get_logger("MemoryManager")

class MemoryManager:
    """
    Handles aging, pruning, and storage optimization for CareerOS.
    Implements Hot vs Cold storage logic and data pruning.
    """
    def __init__(self, aging_rate: float = 0.95, pruning_threshold: float = 0.1):
        self.aging_rate = aging_rate
        self.pruning_threshold = pruning_threshold

    def age_q_table(self):
        """Decay all Q-values in the database by the aging rate."""
        logger.info("Running Q-table aging...")
        # In a real system, we'd do this in a single SQL query for performance
        conn = db.get_conn()
        try:
            conn.execute("UPDATE rl_qtable SET q_value = q_value * ?", (self.aging_rate,))
            conn.commit()
            logger.info("Q-table aged successfully.")
        except Exception as e:
            logger.error(f"Aging failed: {e}")
        finally:
            conn.close()

    def prune_low_value_states(self):
        """Remove Q-table entries with low visit counts or near-zero values."""
        logger.info("Pruning low-value entries...")
        conn = db.get_conn()
        try:
            # Prune if Q is near zero AND visit count is low
            res = conn.execute(
                "DELETE FROM rl_qtable WHERE abs(q_value) < ? AND visit_count < 5",
                (self.pruning_threshold,)
            )
            conn.commit()
            logger.info(f"Pruned {res.rowcount} entries.")
        except Exception as e:
            logger.error(f"Pruning failed: {e}")
        finally:
            conn.close()

    def cleanup_old_jobs(self, days: int = 30):
        """Move old jobs to cold storage or delete them (Aging system)."""
        logger.info(f"Cleaning up jobs older than {days} days...")
        # Logic to delete or mark jobs as 'archived'
        # For MVP, we'll just delete 'new' jobs that were never acted upon
        conn = db.get_conn()
        try:
            res = conn.execute(
                "DELETE FROM jobs WHERE status = 'new' AND created_at < datetime('now', ?)",
                (f'-{days} days',)
            )
            conn.commit()
            logger.info(f"Cleaned up {res.rowcount} old untracked jobs.")
        except Exception as e:
            logger.error(f"Job cleanup failed: {e}")
        finally:
            conn.close()

    def run_full_maintenance(self):
        """Execute full engine maintenance."""
        start = time.time()
        self.age_q_table()
        self.prune_low_value_states()
        self.cleanup_old_jobs()
        logger.info(f"Maintenance completed in {time.time() - start:.4f}s")

if __name__ == "__main__":
    mm = MemoryManager()
    mm.run_full_maintenance()
