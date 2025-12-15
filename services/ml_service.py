# services/ml_service.py
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load MiniLM once at startup
MODEL = SentenceTransformer("all-MiniLM-L6-v2")

# Optional OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USE_OPENAI = bool(OPENAI_API_KEY)

if USE_OPENAI:
    try:
        import openai
        openai.api_key = OPENAI_API_KEY
    except ImportError:
        print("openai package not installed. Install with: pip install openai")
        USE_OPENAI = False

def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def get_embedding(text: str):
    clean = normalize(text)
    
    if USE_OPENAI:
        try:
            response = openai.Embedding.create(
                input=clean,
                model="text-embedding-3-small"
            )
            return np.array(response['data'][0]['embedding'], dtype=np.float32)
        except Exception as e:
            print(f"OpenAI embedding failed, falling back to MiniLM: {e}")
    
    # Fallback to MiniLM
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