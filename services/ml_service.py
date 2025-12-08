# services/ml_service.py

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re

# Load model once at startup (cheap, ~20MB)
MODEL = SentenceTransformer("all-MiniLM-L6-v2")


def normalize(text: str) -> str:
    """
    Basic normalization for titles:
    lower case, remove extra spaces, remove punctuation noise.
    """
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def embed_title(text: str):
    """
    Return embedding vector (list of floats).
    """
    clean = normalize(text)
    vec = MODEL.encode(clean)
    return vec.tolist()


def similarity(vec1, vec2):
    """
    Cosine similarity between two embeddings.
    Returns value between -1 and 1.
    """
    a = np.array(vec1).reshape(1, -1)
    b = np.array(vec2).reshape(1, -1)
    return float(cosine_similarity(a, b)[0][0])
