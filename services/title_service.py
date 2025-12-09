import json
from sqlalchemy.orm import Session
from sklearn.cluster import KMeans
import numpy as np
import pandas as pd

from utils.text_cleaner import clean_text
from services.ml_service import embed_title, similarity
from models.title import Title


# ---------------------------
# Save Single Title
# ---------------------------
def save_title(db: Session, item):
    raw = item.title
    clean = clean_text(raw)

    # embed
    vec = embed_title(clean)

    # check duplicate
    dup_info = check_duplicate(db, {"title": clean})

    obj = Title(
        title=raw,
        normalized_title=clean,
        embedding=json.dumps(vec),
        is_duplicate=dup_info["duplicate"]
    )

    db.add(obj)
    db.commit()
    db.refresh(obj)

    return {
        "message": "Saved",
        "id": obj.id,
        "duplicate": dup_info["duplicate"],
        "duplicate_score": dup_info["score"]
    }


# ---------------------------
# Duplicate Check (best match)
# ---------------------------
def check_duplicate(db: Session, item, threshold: float = 0.88):
    raw = item["title"] if isinstance(item, dict) else item.title
    clean = clean_text(raw)

    new_vec = embed_title(clean)

    best_score = 0.0
    best_match = None

    for row in db.query(Title).all():
        stored_vec = json.loads(row.embedding)
        score = similarity(new_vec, stored_vec)

        if score > best_score:
            best_score = score
            best_match = row

    if best_match and best_score >= threshold:
        return {
            "duplicate": True,
            "score": best_score,
            "id": best_match.id,
            "title": best_match.title
        }

    return {
        "duplicate": False,
        "score": best_score
    }


# ---------------------------
# Find All Similar Titles
# ---------------------------
def find_similar_titles(db: Session, item, threshold: float = 0.75):
    raw = item["title"] if isinstance(item, dict) else item.title
    clean = clean_text(raw)

    new_vec = embed_title(clean)
    similar = []

    for row in db.query(Title).all():
        stored_vec = json.loads(row.embedding)
        score = similarity(new_vec, stored_vec)

        if score >= threshold:
            similar.append({
                "id": row.id,
                "title": row.title,
                "score": score
            })

    similar.sort(key=lambda x: x["score"], reverse=True)
    return similar


# ---------------------------
# Count total duplicates saved
# ---------------------------
def count_duplicates(db: Session):
    return db.query(Title).filter(Title.is_duplicate == True).count()


# ---------------------------
# Cluster Titles by Meaning
# ---------------------------
def cluster_titles(db: Session, k: int = 5):
    rows = db.query(Title).all()
    if not rows:
        return {"error": "No titles in database"}

    vectors = [json.loads(r.embedding) for r in rows]
    ids = [r.id for r in rows]

    vectors_np = np.array(vectors)

    model = KMeans(n_init=10, n_clusters=k)
    labels = model.fit_predict(vectors_np)

    clusters = {}
    for label, row_id in zip(labels, ids):
        clusters.setdefault(label, []).append(row_id)

    return clusters


# ---------------------------
# Bulk Excel Title Processor
# df expected
# ---------------------------
def process_bulk_titles(db: Session, df: pd.DataFrame):
    summary = {
        "processed": 0,
        "duplicates": 0,
        "saved": 0,
        "details": []
    }

    titles = df["title"].dropna().tolist()

    for raw in titles:
        summary["processed"] += 1

        clean = clean_text(raw)

        # duplicate check
        dup_info = check_duplicate(db, {"title": clean})

        if dup_info["duplicate"]:
            summary["duplicates"] += 1
            summary["details"].append({
                "title": raw,
                "duplicate": True,
                "id": dup_info["id"],
                "score": dup_info["score"]
            })
            continue

        # save new
        vec = embed_title(clean)

        obj = Title(
            title=raw,
            normalized_title=clean,
            embedding=json.dumps(vec),
            is_duplicate=False
        )

        db.add(obj)
        db.commit()

        summary["saved"] += 1

    return summary
