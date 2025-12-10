# services/ml_service.py
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re

# Load model once at startup
MODEL = SentenceTransformer("all-MiniLM-L6-v2")

def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# This is the function used by webhook
def get_embedding(text: str):
    clean = normalize(text)
    return MODEL.encode(clean, normalize_embeddings=True)

# This is the function that checks for duplicates in DB
def find_duplicates(new_title: str, threshold: float = 0.80):
    from database.database import get_db_session
    from models.title import Title

    new_embedding = get_embedding(new_title)

    with get_db_session() as session:
        titles = session.query(Title).all()
        
        if not titles:
            return None, 0.0

        embeddings = []
        for t in titles:
            if t.embedding:
                emb = np.frombuffer(t.embedding, dtype=np.float32)
                embeddings.append(emb)

        if not embeddings:
            return None, 0.0

        embeddings = np.array(embeddings)
        similarities = cosine_similarity([new_embedding], embeddings)[0]
        
        max_score = float(np.max(similarities))
        max_idx = int(np.argmax(similarities))

        if max_score >= threshold:
            duplicate = titles[max_idx]
            return {
                "id": duplicate.id,
                "title": duplicate.title,
                "score": round(max_score, 3)
            }, max_score

        return None, max_score