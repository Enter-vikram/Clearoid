from sqlalchemy.orm import Session
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd

from utils.text_cleaner import clean_text
from services.embedding_service import get_embedding
from models.title import Title

SIMILARITY_THRESHOLD = 0.85


# ---------------------------------------------------------
# Internal helper: find best semantic match
# ---------------------------------------------------------
def _find_best_match(db: Session, vec: np.ndarray):
    best_score = 0.0
    best_row = None

    rows = db.query(Title).all()

    for row in rows:
        if not row.embedding:
            continue

        try:
            stored = np.frombuffer(row.embedding, dtype=np.float32)
            score = float(cosine_similarity([vec], [stored])[0][0])
        except Exception:
            continue

        if score > best_score:
            best_score = score
            best_row = row

    return best_row, best_score


# ---------------------------------------------------------
# 🔒 HARD RULE: exactly ONE unique per normalized_title
# ---------------------------------------------------------
def enforce_single_primary(db: Session, normalized_title: str):
    """
    Ensures exactly ONE unique row per cluster.
    Oldest row (by created_at) is canonical primary.
    All others are forced to duplicate.
    """
    rows = (
        db.query(Title)
        .filter(Title.normalized_title == normalized_title)
        .order_by(Title.created_at.asc())
        .all()
    )

    if not rows:
        return

    primary = rows[0]
    primary.is_duplicate = 0

    for r in rows[1:]:
        r.is_duplicate = 1

    db.commit()


# ---------------------------------------------------------
# Save a single title (OPTION A + CLUSTER LOCK)
# ---------------------------------------------------------
def save_title(db: Session, item):
    raw = item.title
    cleaned = clean_text(raw)

    vec = np.array(get_embedding(cleaned), dtype=np.float32)
    vec_bytes = vec.tobytes()

    best_row, best_score = _find_best_match(db, vec)

    if best_row and best_score >= SIMILARITY_THRESHOLD:
        # semantic duplicate → inherit canonical cluster
        normalized = best_row.normalized_title
        is_duplicate = 1
    else:
        # new semantic cluster
        normalized = cleaned
        is_duplicate = 0

    obj = Title(
        title=raw,
        normalized_title=normalized,
        embedding=vec_bytes,
        is_duplicate=is_duplicate,
    )

    db.add(obj)
    db.commit()
    db.refresh(obj)

    # 🔒 enforce canonical truth AFTER insert
    enforce_single_primary(db, normalized)

    return obj


# ---------------------------------------------------------
# Check duplicate (READ ONLY)
# ---------------------------------------------------------
def check_duplicate(db: Session, item, threshold: float = SIMILARITY_THRESHOLD):
    raw = item.title
    cleaned = clean_text(raw)

    vec = np.array(get_embedding(cleaned), dtype=np.float32)
    best_row, best_score = _find_best_match(db, vec)

    return {
        "duplicate": bool(best_row and best_score >= threshold),
        "score": round(best_score, 3),
        "match_id": best_row.id if best_row else None,
        "canonical": best_row.normalized_title if best_row else None,
    }


# ---------------------------------------------------------
# Find similar titles (unchanged semantics)
# ---------------------------------------------------------
def find_similar_titles(db: Session, item, threshold: float = 0.75):
    raw = item.title
    cleaned = clean_text(raw)

    vec = np.array(get_embedding(cleaned), dtype=np.float32)
    results = []

    for row in db.query(Title).all():
        try:
            stored = np.frombuffer(row.embedding, dtype=np.float32)
            score = float(cosine_similarity([vec], [stored])[0][0])
        except Exception:
            continue

        if score >= threshold:
            results.append({
                "id": row.id,
                "title": row.title,
                "score": round(score, 3),
            })

    return sorted(results, key=lambda x: x["score"], reverse=True)


# ---------------------------------------------------------
# Bulk upload (EXACT SAME RULES + LOCK)
# ---------------------------------------------------------
def process_bulk_titles(db: Session, df: pd.DataFrame):
    summary = {
        "processed": 0,
        "duplicates": 0,
        "saved": 0,
    }

    titles = df["title"].dropna().astype(str).tolist()

    for raw in titles:
        summary["processed"] += 1
        cleaned = clean_text(raw)

        vec = np.array(get_embedding(cleaned), dtype=np.float32)
        best_row, best_score = _find_best_match(db, vec)

        if best_row and best_score >= SIMILARITY_THRESHOLD:
            normalized = best_row.normalized_title
            is_duplicate = 1
            summary["duplicates"] += 1
        else:
            normalized = cleaned
            is_duplicate = 0
            summary["saved"] += 1

        obj = Title(
            title=raw,
            normalized_title=normalized,
            embedding=vec.tobytes(),
            is_duplicate=is_duplicate,
        )

        db.add(obj)
        db.commit()

        # 🔒 enforce after EVERY insert
        enforce_single_primary(db, normalized)

    return summary


# ---------------------------------------------------------
# Count duplicates
# ---------------------------------------------------------
def count_duplicates(db: Session):
    return (
        db.query(Title)
        .filter(Title.is_duplicate == 1)
        .count()
    )
