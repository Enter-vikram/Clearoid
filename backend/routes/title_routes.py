import io
from datetime import datetime

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.connection import get_db
from backend.schemas.title_schema import TitleCreate, TitleOut, TitleUpdate
from backend.utils.text_cleaner import clean_text
from backend.services.embedding_service import get_embedding
from backend.services.title_service import (
    save_title,
    check_duplicate,
    find_similar_titles,
    count_duplicates,
)
from database.models import Title

router = APIRouter(prefix="/api", tags=["Titles"])
SIMILARITY_THRESHOLD = 0.85


def _best_match_excluding(db: Session, vec: np.ndarray, exclude_id: int):
    best_score = 0.0
    best_row = None
    for row in db.query(Title).filter(Title.id != exclude_id).all():
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


@router.post("/submit", response_model=TitleOut)
def submit(item: TitleCreate, db: Session = Depends(get_db)):
    return save_title(db, item)


@router.post("/check-duplicate")
def check_duplicate_route(item: TitleCreate, db: Session = Depends(get_db)):
    return check_duplicate(db, item)


@router.post("/similar-titles")
def similar_titles(item: TitleCreate, db: Session = Depends(get_db)):
    return {"results": find_similar_titles(db, item)}


@router.get("/duplicate-count")
def duplicate_count(db: Session = Depends(get_db)):
    return {"duplicate_count": count_duplicates(db)}


@router.get("/clusters")
def clusters(db: Session = Depends(get_db)):
    groups = (
        db.query(
            Title.normalized_title.label("group"),
            func.count(Title.id).label("count")
        )
        .group_by(Title.normalized_title)
        .having(func.count(Title.id) > 1)
        .all()
    )

    return [
        {"group": g.group, "count": g.count}
        for g in groups
    ]


@router.get("/history")
def history(db: Session = Depends(get_db)):
    rows = (
        db.query(Title)
        .order_by(Title.created_at.desc())
        .all()
    )

    data = []
    for r in rows:
        data.append({
            "id": r.id,
            "title": r.title,
            "normalized": r.normalized_title,
            "status": "duplicate" if r.is_duplicate else "unique",
            "cluster": r.normalized_title,
            "created_at": r.created_at.isoformat()
        })

    return {
        "total": len(data),
        "unique": sum(1 for d in data if d["status"] == "unique"),
        "duplicates": sum(1 for d in data if d["status"] == "duplicate"),
        "clusters": len(set(d["cluster"] for d in data)),
        "data": data
    }


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total = db.query(Title).count()
    duplicates = db.query(Title).filter(Title.is_duplicate == 1).count()
    unique = total - duplicates
    
    clusters = (
        db.query(Title.normalized_title)
        .group_by(Title.normalized_title)
        .having(func.count(Title.id) > 1)
        .count()
    )
    
    return {
        "total": total,
        "unique": unique,
        "duplicates": duplicates,
        "clusters": clusters
    }


@router.get("/titles")
def get_titles(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1),
    search: str | None = None,
    duplicates: bool | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Title)

    if search:
        query = query.filter(
            (Title.title.ilike(f"%{search}%")) |
            (Title.normalized_title.ilike(f"%{search}%"))
        )

    if duplicates is not None:
        query = query.filter(Title.is_duplicate == (1 if duplicates else 0))

    total = query.count()
    rows = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "total": total,
        "data": [
            {
                "id": r.id,
                "title": r.title,
                "normalized": r.normalized_title,
                "is_duplicate": r.is_duplicate,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ],
    }


@router.delete("/titles/{title_id}")
def delete_title(title_id: int, db: Session = Depends(get_db)):
    row = db.query(Title).filter(Title.id == title_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Title not found")

    db.delete(row)
    db.commit()
    return {"deleted": 1, "id": title_id}


@router.put("/titles/{title_id}")
def update_title(title_id: int, payload: TitleUpdate, db: Session = Depends(get_db)):
    row = db.query(Title).filter(Title.id == title_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Title not found")

    if not payload.title:
        raise HTTPException(status_code=400, detail="title is required")

    raw = payload.title.strip()
    if not raw:
        raise HTTPException(status_code=400, detail="title cannot be empty")

    cleaned = clean_text(raw)
    vec = np.array(get_embedding(cleaned), dtype=np.float32)
    best_row, best_score = _best_match_excluding(db, vec, title_id)

    if best_row and best_score >= SIMILARITY_THRESHOLD:
        row.normalized_title = best_row.normalized_title
        row.is_duplicate = 1
    else:
        row.normalized_title = cleaned
        row.is_duplicate = 0

    row.title = raw
    row.embedding = vec.tobytes()

    db.commit()
    db.refresh(row)
    return {
        "id": row.id,
        "title": row.title,
        "normalized_title": row.normalized_title,
        "is_duplicate": row.is_duplicate,
    }


@router.delete("/titles")
def delete_titles(
    scope: str = Query("all"),
    ids: str | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Title)

    if ids:
        id_values = []
        for token in ids.split(","):
            token = token.strip()
            if token.isdigit():
                id_values.append(int(token))
        if not id_values:
            raise HTTPException(status_code=400, detail="No valid ids provided")
        query = query.filter(Title.id.in_(id_values))
    else:
        if scope == "unique":
            query = query.filter(Title.is_duplicate == 0)
        elif scope == "duplicate":
            query = query.filter(Title.is_duplicate == 1)
        elif scope != "all":
            raise HTTPException(status_code=400, detail="Invalid scope")

    deleted = query.delete(synchronize_session=False)
    db.commit()
    return {"deleted": int(deleted)}


@router.get("/export/excel")
def export_excel(
    type: str = Query("all"),
    ids: str | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Title).order_by(Title.created_at.desc())

    if type == "unique":
        query = query.filter(Title.is_duplicate == 0)
    elif type == "duplicate":
        query = query.filter(Title.is_duplicate == 1)
    elif type == "selected":
        if not ids:
            raise HTTPException(status_code=400, detail="ids is required for selected export")
        parsed_ids = [int(x.strip()) for x in ids.split(",") if x.strip().isdigit()]
        if not parsed_ids:
            raise HTTPException(status_code=400, detail="No valid ids provided")
        query = query.filter(Title.id.in_(parsed_ids))
    elif type != "all":
        raise HTTPException(status_code=400, detail="Invalid export type")

    rows = query.all()
    if not rows:
        raise HTTPException(status_code=404, detail="No data available for export")

    data = [
        {
            "id": r.id,
            "title": r.title,
            "normalized_title": r.normalized_title,
            "status": "duplicate" if r.is_duplicate else "unique",
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="titles")
    output.seek(0)

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"clearoid_{type}_{ts}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
