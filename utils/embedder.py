"""
embedder.py — Sentence embedding wrapper using bge-small-en-v1.5
Loaded once via Streamlit cache, runs on CPU in ~20ms/query.
"""

import numpy as np
import streamlit as st


@st.cache_resource(show_spinner="🧠 Loading AI model... (first run ~30s)")
def _load_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("BAAI/bge-small-en-v1.5")


def encode(text: str) -> np.ndarray:
    """Encode a single string to a 384-dim normalized vector."""
    model = _load_model()
    vec = model.encode(text, normalize_embeddings=True, show_progress_bar=False)
    return vec.astype(np.float32)


def encode_batch(texts: list) -> np.ndarray:
    """Encode a list of strings to a (N, 384) matrix."""
    model = _load_model()
    vecs = model.encode(
        texts,
        normalize_embeddings=True,
        batch_size=32,
        show_progress_bar=False
    )
    return vecs.astype(np.float32)


def encode_profile(profile: dict) -> np.ndarray:
    """Build a rich profile text and encode it."""
    skills = ", ".join(profile.get("skills", []))
    roles = ", ".join(profile.get("target_roles", []))
    goals = profile.get("career_goals", "")
    text = f"Skills: {skills}. Target roles: {roles}. Goals: {goals}"
    return encode(text)


def encode_job(job: dict) -> np.ndarray:
    """Build a rich job text and encode it."""
    skills = ", ".join(job.get("skills_required", []))
    text = (
        f"{job.get('title', '')} at {job.get('company', '')}. "
        f"Required skills: {skills}. "
        f"{job.get('description', '')[:500]}"
    )
    return encode(text)
