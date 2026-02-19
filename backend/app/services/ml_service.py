# services/ml_service.py

import re
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from services.embedding_service import get_embedding


# --------------------------
# Text normalization
# --------------------------
def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# --------------------------
# Duplicate detection
# --------------------------
def find_duplicates(new_title: str, threshold: float = 0.80):
    """
    Finds the most similar existing title.
    Returns (duplicate_info | None, max_score)
    """
    from database.database import get_db_session
    from models.title import Title

    clean_title = normalize(new_title)
    new_embedding = np.array(get_embedding(clean_title), dtype=np.float32)

    with get_db_session() as session:
        titles = session.query(Title).all()

        if not titles:
            return None, 0.0

        embeddings = []
        valid_titles = []

        for t in titles:
            if t.embedding:
                emb = np.frombuffer(t.embedding, dtype=np.float32)
                embeddings.append(emb)
                valid_titles.append(t)

        if not embeddings:
            return None, 0.0

        embeddings = np.vstack(embeddings)

        similarities = cosine_similarity([new_embedding], embeddings)[0]

        max_idx = int(np.argmax(similarities))
        max_score = float(similarities[max_idx])

        if max_score >= threshold:
            duplicate = valid_titles[max_idx]
            return {
                "id": duplicate.id,
                "title": duplicate.title,
                "score": round(max_score, 3),
            }, max_score

        return None, max_score
