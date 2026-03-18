from typing import Dict, Any

class LongTermMemory:
    """
    Persistent career memory interface.
    Aggregates historical outcomes to inform future probabilities.
    """
    def __init__(self):
        pass

    def get_cluster_performance(self, cluster_id: str) -> Dict[str, Any]:
        """Retrieves success rates and volume for a specific skill cluster."""
        stats = db.get_cluster_stats(cluster_id)
        
        # Bayesian Success Rate (Simplified)
        interviews = stats.get("interviews", 0)
        total = stats.get("total_applies", 0)
        
        success_rate = interviews / total if total > 0 else 0.0
        
        return {
            "cluster_id": cluster_id,
            "interviews": interviews,
            "total_applies": total,
            "success_rate": round(success_rate, 2),
            "confidence": "High" if total > 10 else "Low"
        }

# Singleton instance
career_memory = LongTermMemory()
