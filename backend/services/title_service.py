from difflib import SequenceMatcher
from typing import Iterable, Optional

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from backend.utils.text_cleaner import clean_text
from backend.services.embedding_service import get_embedding
from database.models import Title

SIMILARITY_THRESHOLD = 0.83


def _token_sort(text: str) -> str:
    return " ".join(sorted(text.split()))


def lexical_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0

    direct = SequenceMatcher(None, a, b).ratio()
    token_sorted = SequenceMatcher(None, _token_sort(a), _token_sort(b)).ratio()
    return float(max(direct, token_sorted))


def _tokenize(text: str) -> list[str]:
    return [t for t in text.split() if t]


def _token_overlap(a: str, b: str) -> float:
    a_tokens = set(_tokenize(a))
    b_tokens = set(_tokenize(b))
    if not a_tokens or not b_tokens:
        return 0.0
    return len(a_tokens & b_tokens) / len(a_tokens | b_tokens)


def _is_identifier_like(text: str) -> bool:
    # Treat mixed alphanumeric IDs (USN-like values) as exact-match entities.
    compact = text.replace("-", "").replace("_", "")
    has_alpha = any(ch.isalpha() for ch in compact)
    has_digit = any(ch.isdigit() for ch in compact)
    return has_alpha and has_digit and len(compact) >= 5 and " " not in text


def _single_keyword_conflict(a: str, b: str) -> bool:
    a_tokens = _tokenize(a)
    b_tokens = _tokenize(b)
    if len(a_tokens) != len(b_tokens) or len(a_tokens) < 2:
        return False

    remaining_b = b_tokens.copy()
    mismatched_a = []
    for tok in a_tokens:
        if tok in remaining_b:
            remaining_b.remove(tok)
        else:
            mismatched_a.append(tok)

    if len(mismatched_a) != 1 or len(remaining_b) != 1:
        return False

    # If only one term differs and it is not a close typo, treat as different topics.
    mismatch_sim = SequenceMatcher(None, mismatched_a[0], remaining_b[0]).ratio()
    return mismatch_sim < 0.82


def _read_embedding(value) -> Optional[np.ndarray]:
    if value is None:
        return None

    if isinstance(value, memoryview):
        value = value.tobytes()

    if isinstance(value, (bytes, bytearray)):
        arr = np.frombuffer(value, dtype=np.float32)
        return arr if arr.size else None

    return None


def _score_pair(input_text: str, input_vec: np.ndarray, row: Title) -> float:
    semantic = 0.0
    row_vec = _read_embedding(row.embedding)
    if row_vec is not None:
        try:
            semantic = float(cosine_similarity([input_vec], [row_vec])[0][0])
        except Exception:
            semantic = 0.0

    lex = lexical_similarity(input_text, row.normalized_title or "")
    # Blend lexical and semantic scores for typo-tolerant matching.
    return float(max(semantic, (0.65 * semantic) + (0.35 * lex), lex * 0.95))


def _is_duplicate_match(
    input_text: str,
    candidate_text: str,
    semantic: float,
    lexical: float,
    threshold: float,
) -> bool:
    if _is_identifier_like(input_text) or _is_identifier_like(candidate_text):
        return input_text == candidate_text

    overlap = _token_overlap(input_text, candidate_text)
    if _single_keyword_conflict(input_text, candidate_text):
        # Prevent over-grouping like "movie recommendation system" vs "music recommendation system".
        return False

    hybrid = max(semantic, (0.65 * semantic) + (0.35 * lexical), lexical * 0.95)

    # Require some lexical/token support in addition to semantic closeness.
    if hybrid < threshold:
        return False
    if semantic < 0.80 and lexical < 0.86:
        return False
    if overlap < 0.34 and lexical < 0.90:
        return False

    return True


def _find_best_match(db: Optional[Session], cleaned_text: str, vec: np.ndarray, rows: Optional[Iterable[Title]] = None):
    best_score = 0.0
    best_row = None

    if rows is None:
        if db is None:
            return None, 0.0
        rows = db.query(Title).all()

    for row in rows:
        score = _score_pair(cleaned_text, vec, row)

        if score > best_score:
            best_score = score
            best_row = row

    return best_row, best_score


def enforce_single_primary(db: Session, normalized_title: str):
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


def save_title(db: Session, item):
    raw = item.title
    cleaned = clean_text(raw)

    vec = np.array(get_embedding(cleaned), dtype=np.float32)
    vec_bytes = vec.tobytes()

    rows = db.query(Title).filter(Title.is_duplicate == 0).all()
    best_row, best_score, is_dup = is_probable_duplicate(
        cleaned_text=cleaned,
        vector=vec,
        existing_rows=rows,
        threshold=SIMILARITY_THRESHOLD,
    )

    if best_row and is_dup:
        normalized = best_row.normalized_title
        is_duplicate = 1
    else:
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

    enforce_single_primary(db, normalized)

    return obj


def check_duplicate(db: Session, item, threshold: float = SIMILARITY_THRESHOLD):
    raw = item.title
    cleaned = clean_text(raw)

    vec = np.array(get_embedding(cleaned), dtype=np.float32)
    rows = db.query(Title).filter(Title.is_duplicate == 0).all()
    best_row, best_score, is_dup = is_probable_duplicate(
        cleaned_text=cleaned,
        vector=vec,
        existing_rows=rows,
        threshold=threshold,
    )

    return {
        "duplicate": bool(best_row and is_dup),
        "score": round(best_score, 3),
        "match_id": best_row.id if best_row else None,
        "canonical": best_row.normalized_title if best_row else None,
    }


def find_similar_titles(db: Session, item, threshold: float = 0.75):
    raw = item.title
    cleaned = clean_text(raw)

    vec = np.array(get_embedding(cleaned), dtype=np.float32)
    results = []

    for row in db.query(Title).all():
        score = _score_pair(cleaned, vec, row)

        if score >= threshold:
            results.append({
                "id": row.id,
                "title": row.title,
                "score": round(score, 3),
            })

    return sorted(results, key=lambda x: x["score"], reverse=True)


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
        current_rows = db.query(Title).filter(Title.is_duplicate == 0).all()
        best_row, _, is_dup = is_probable_duplicate(
            cleaned_text=cleaned,
            vector=vec,
            existing_rows=current_rows,
            threshold=SIMILARITY_THRESHOLD,
        )

        if best_row and is_dup:
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

        enforce_single_primary(db, normalized)

    return summary


def count_duplicates(db: Session):
    return (
        db.query(Title)
        .filter(Title.is_duplicate == 1)
        .count()
    )


def is_probable_duplicate(
    cleaned_text: str,
    vector: np.ndarray,
    existing_rows: Iterable[Title],
    threshold: float = SIMILARITY_THRESHOLD,
):
    best_row, best_score = _find_best_match(
        db=None,
        cleaned_text=cleaned_text,
        vec=vector,
        rows=existing_rows,
    )
    if not best_row:
        return None, best_score, False

    candidate_vec = _read_embedding(best_row.embedding)
    semantic = 0.0
    if candidate_vec is not None:
        try:
            semantic = float(cosine_similarity([vector], [candidate_vec])[0][0])
        except Exception:
            semantic = 0.0
    lexical = lexical_similarity(cleaned_text, best_row.normalized_title or "")

    is_dup = _is_duplicate_match(
        cleaned_text,
        best_row.normalized_title or "",
        semantic=semantic,
        lexical=lexical,
        threshold=threshold,
    )
    return best_row, best_score, is_dup
