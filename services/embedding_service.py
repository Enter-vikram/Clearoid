# services/embedding_service.py

from pathlib import Path
from dotenv import load_dotenv
import os
import logging
from typing import List

from sentence_transformers import SentenceTransformer
import numpy as np

# --------------------------------------------------
# ENV
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

USE_OPENAI = os.getenv("USE_OPENAI", "false").lower() == "true"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

logger = logging.getLogger(__name__)

# --------------------------------------------------
# MiniLM (default, CPU-only)
# --------------------------------------------------
_minilm_model = None


def get_minilm_model():
    global _minilm_model
    if _minilm_model is None:
        _minilm_model = SentenceTransformer(
            "all-MiniLM-L6-v2",
            device="cpu"
        )
    return _minilm_model


def get_minilm_embedding(text: str) -> List[float]:
    model = get_minilm_model()
    emb = model.encode(
        text,
        convert_to_numpy=True,
        show_progress_bar=False
    )
    return emb.tolist()


def get_minilm_embeddings(texts: List[str]) -> List[List[float]]:
    model = get_minilm_model()
    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        show_progress_bar=False
    )
    return embeddings.tolist()


# --------------------------------------------------
# OpenAI (optional fallback)
# --------------------------------------------------
_openai_client = None


def get_openai_client():
    global _openai_client
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set")

    if _openai_client is None:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=OPENAI_API_KEY)

    return _openai_client


def get_openai_embedding(text: str) -> List[float]:
    client = get_openai_client()
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


# --------------------------------------------------
# ✅ PUBLIC API (THIS FIXES YOUR CRASH)
# --------------------------------------------------
def get_embedding(text: str) -> List[float]:
    """Single text embedding"""
    if USE_OPENAI:
        try:
            return get_openai_embedding(text)
        except Exception as e:
            logger.warning("OpenAI failed, falling back to MiniLM: %s", e)

    return get_minilm_embedding(text)


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    ✅ REQUIRED BY ml_service.py
    Batch embedding (fast for Excel / bulk)
    """
    if not texts:
        return []

    if USE_OPENAI:
        try:
            return [get_openai_embedding(t) for t in texts]
        except Exception as e:
            logger.warning("OpenAI batch failed, fallback to MiniLM: %s", e)

    return get_minilm_embeddings(texts)
