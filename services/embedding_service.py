from pathlib import Path
from dotenv import load_dotenv

# Always load .env (safe even if empty)
BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

import os
import logging
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# ==========================================================
# Configuration
# ==========================================================

USE_OPENAI = os.getenv("USE_OPENAI", "false").lower() == "true"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ==========================================================
# MiniLM (default, CPU-only, deterministic)
# ==========================================================

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

    # ❗ IMPORTANT: no normalize_embeddings here
    emb = model.encode(
        text,
        convert_to_numpy=True,
        show_progress_bar=False
    )

    return emb.tolist()

# ==========================================================
# OpenAI (optional, guarded)
# ==========================================================

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

# ==========================================================
# Unified public API
# ==========================================================

def get_embedding(text: str) -> List[float]:
    """
    Returns an embedding for the given text.

    Default: MiniLM
    Optional: OpenAI (only if USE_OPENAI=true)
    """

    if USE_OPENAI:
        try:
            return get_openai_embedding(text)
        except Exception as e:
            logger.warning(
                "OpenAI embedding failed, falling back to MiniLM: %s",
                str(e)
            )

    return get_minilm_embedding(text)
