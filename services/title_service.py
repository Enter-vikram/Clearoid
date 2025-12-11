# services/title_service.py
from sqlalchemy.orm import Session
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd
import json
from utils.text_cleaner import clean_text
from services.ml_service import get_embedding
from models.title import Title


def save_title(db: Session, item):
    raw = item.title
    clean = clean_text(raw)
    vec = get_embedding(clean)
    dup_info = check_duplicate(db, {"title": clean})

    obj = Title(
        title=raw,
        normalized_title=clean,
        embedding=vec.tobytes(),
        is_duplicate=1 if dup_info["duplicate"] else 0
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj  # Return full model for TitleOut


def check_duplicate(db: Session, item, threshold: float = 0.85):
    raw = item["title"] if isinstance(item, dict) else item.title
    clean = clean_text(raw)
    new_vec = get_embedding(clean)
    best_score = 0.0

    for row in db.query(Title).all():
        if not row.embedding:
            continue
        try:
            if isinstance(row.embedding, str):
                stored_vec = np.array(json.loads(row.embedding), dtype=np.float32)
            else:
                stored_vec = np.frombuffer(row.embedding, dtype=np.float32)
            score = float(cosine_similarity([new_vec], [stored_vec])[0][0])
            if score > best_score:
                best_score = score
        except:
            continue

    # FIXED: Convert numpy types to native Python types
    is_duplicate = bool(best_score >= threshold)
    score = round(float(best_score), 3)

    return {"duplicate": is_duplicate, "score": score}


def find_similar_titles(db: Session, item, threshold: float = 0.75):
    raw = item["title"] if isinstance(item, dict) else item.title
    clean = clean_text(raw)
    new_vec = get_embedding(clean)
    similar = []

    for row in db.query(Title).all():
        if not row.embedding:
            continue
        try:
            if isinstance(row.embedding, str):
                stored_vec = np.array(json.loads(row.embedding), dtype=np.float32)
            else:
                stored_vec = np.frombuffer(row.embedding, dtype=np.float32)
            score = float(cosine_similarity([new_vec], [stored_vec])[0][0])
            if score >= threshold:
                similar.append({
                    "id": row.id,
                    "title": row.title,
                    "score": round(score, 3)
                })
        except:
            continue

    similar.sort(key=lambda x: x["score"], reverse=True)
    return similar


def process_bulk_titles(db: Session, df: pd.DataFrame):
    summary = {"processed": 0, "duplicates": 0, "saved": 0}
    titles = df["title"].dropna().astype(str).tolist()

    # Load existing embeddings
    existing = db.query(Title).all()
    existing_embs = []
    for t in existing:
        if t.embedding:
            try:
                if isinstance(t.embedding, str):
                    vec = np.array(json.loads(t.embedding), dtype=np.float32)
                else:
                    vec = np.frombuffer(t.embedding, dtype=np.float32)
                existing_embs.append(vec)
            except:
                continue

    batch_cleaned = set()

    for raw in titles:
        summary["processed"] += 1
        clean = clean_text(raw).strip()

        # Exact match in batch
        if clean in batch_cleaned:
            summary["duplicates"] += 1
            continue

        # Semantic match against DB
        is_duplicate = False
        if existing_embs:
            new_emb = get_embedding(clean)
            scores = cosine_similarity([new_emb], existing_embs)[0]
            if float(scores.max()) >= 0.85:
                is_duplicate = True

        if is_duplicate:
            summary["duplicates"] += 1
            continue

        # Save unique
        vec = get_embedding(clean)
        obj = Title(
            title=raw,
            normalized_title=clean,
            embedding=vec.tobytes(),
            is_duplicate=0
        )
        db.add(obj)
        db.commit()
        summary["saved"] += 1
        batch_cleaned.add(clean)

    return summary


def count_duplicates(db: Session):
    return db.query(Title).filter(Title.is_duplicate == 1).count()