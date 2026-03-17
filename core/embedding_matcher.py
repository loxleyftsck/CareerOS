import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

class FaissMatcher:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        # Using IndexFlatIP since we will normalize vectors for Cosine Similarity
        self.index = faiss.IndexFlatIP(self.dimension)
        self.jobs = []
        
    def _normalize(self, vectors):
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return np.where(norms == 0, vectors, vectors / norms)

    def add_jobs(self, job_list):
        if not job_list:
            return
            
        self.jobs.extend(job_list)
        # Create a single string for each job description to embed
        texts = [f"{j['title']} {j['company']} {j['description']}" for j in job_list]
        
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        normalized_embeddings = self._normalize(embeddings)
        self.index.add(normalized_embeddings)

    def search(self, profile_text: str, top_k: int = 5):
        if self.index.ntotal == 0:
            return []
            
        user_emb = self.model.encode([profile_text], convert_to_numpy=True)
        user_emb = self._normalize(user_emb)
        
        # Search the FAISS index
        distances, indices = self.index.search(user_emb, min(top_k, self.index.ntotal))
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.jobs):
                job = self.jobs[idx]
                # Map Inner Product mathematically [-1, 1] to a percentage [0, 100]
                score = (dist + 1) / 2 * 100 
                results.append({
                    "job": job,
                    "score": round(float(score), 1)
                })
                
        # Sort results from highest to lowest score
        return sorted(results, key=lambda x: x["score"], reverse=True)
