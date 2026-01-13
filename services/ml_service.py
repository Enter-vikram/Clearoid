# services/ml_service.py

import re
import numpy as np
from rapidfuzz import fuzz
from typing import Tuple, Optional
from sqlalchemy.orm import Session

from models.title import Title
from services.embedding_service import embed_texts


# --------------------------------------------------
# Text normalization
# --------------------------------------------------
def normalize(text: str) -> str:
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# --------------------------------------------------
# Vector math
# --------------------------------------------------
def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    denom = np.linalg.norm(v1) * np.linalg.norm(v2)
    if denom == 0:
        return 0.0
    return float(np.dot(v1, v2) / denom)


# --------------------------------------------------
# Similarity functions
# --------------------------------------------------
def semantic_similarity(a: str, b: str) -> float:
    embeddings = embed_texts([a, b])
    v1 = np.array(embeddings[0])
    v2 = np.array(embeddings[1])
    return cosine_similarity(v1, v2)


def fuzzy_similarity(a: str, b: str) -> float:
    return fuzz.token_set_ratio(a, b) / 100.0


def hybrid_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0

    sem = semantic_similarity(a, b)
    fuzz_score = fuzzy_similarity(a, b)
    return round((0.7 * sem) + (0.3 * fuzz_score), 4)


# --------------------------------------------------
# Duplicate detection (DB injected)
# --------------------------------------------------
def find_duplicates(
    db: Session,
    new_title: str,
    threshold: float = 0.85
) -> Tuple[Optional[dict], float]:

    clean_new = normalize(new_title)

    if not clean_new:
        return None, 0.0

    titles = db.query(Title).all()

    best_match = None
    best_score = 0.0

    for t in titles:
        if not t.title:
            continue

        existing = normalize(t.title)
        score = hybrid_similarity(clean_new, existing)

        if score > best_score:
            best_score = score
            best_match = t

    if best_match and best_score >= threshold:
        return {
            "id": best_match.id,
            "title": best_match.title,
            "score": round(best_score, 3),
        }, best_score

    return None, best_score
