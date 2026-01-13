# routes/title_routes.py

from fastapi import APIRouter, Depends, Query, HTTPException, Body, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
import numpy as np
import io
import csv
from datetime import datetime
import logging

from database.database import get_db
from models.title import Title
from schemas.title_schema import TitleCreate, TitleOut
from services.ml_service import find_duplicates, hybrid_similarity
from services.embedding_service import get_embedding

logger = logging.getLogger(__name__)

# =================================================
# ROUTER
# =================================================
router = APIRouter(prefix="/api", tags=["Titles"])


# =================================================
# Submit single title
# =================================================
@router.post("/submit", response_model=TitleOut)
def submit(item: TitleCreate, db: Session = Depends(get_db)):
    title_text = item.title.strip()

    if not title_text:
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    normalized = title_text.lower().strip()

    # Generate embedding
    vector = get_embedding(normalized)
    embedding_bytes = np.array(vector, dtype=np.float32).tobytes()

    # Duplicate detection
    dup, score = find_duplicates(db, title_text)

    new_entry = Title(
        title=title_text,
        normalized_title=normalized,
        embedding=embedding_bytes,
        is_duplicate=1 if dup else 0,
        # You can store similarity score if your model has a field for it
        # similarity_score=score if dup else 1.0
    )

    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)

    return new_entry


# =================================================
# Check duplicate (no save)
# =================================================
@router.post("/check-duplicate")
def check_duplicate_route(item: TitleCreate, db: Session = Depends(get_db)):
    dup, score = find_duplicates(db, item.title)

    if dup:
        return {
            "duplicate": True,
            "id": dup["id"],
            "title": dup["title"],
            "score": round(score, 4),
        }

    return {"duplicate": False, "score": round(score, 4)}


# =================================================
# Similar titles (semantic search)
# =================================================
@router.post("/similar-titles")
def similar_titles(
    item: TitleCreate,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    rows = db.query(Title).all()

    scored = []
    for r in rows:
        score = hybrid_similarity(item.title, r.title)
        if score >= 0.7:
            scored.append({
                "id": r.id,
                "title": r.title,
                "score": round(score, 4),
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return {"results": scored[:limit]}


# =================================================
# History (feeds history.html)
# =================================================
@router.get("/history")
def history(db: Session = Depends(get_db)):
    rows = db.query(Title).order_by(Title.created_at.desc()).all()

    data = []
    for r in rows:
        # If you have a similarity_score field in model, use it
        # Otherwise fallback to 1.0 for unique, or last detected score
        similarity = 1.0 if not r.is_duplicate else 0.92  # placeholder - improve later

        data.append({
            "id": r.id,
            "title": r.title,
            "status": "duplicate" if r.is_duplicate else "unique",
            "cluster": r.normalized_title,  # or real cluster id/group if implemented
            "similarityScore": similarity,
            "created_at": r.created_at.isoformat(),
        })

    return {
        "total": len(data),
        "unique": sum(1 for d in data if d["status"] == "unique"),
        "duplicates": sum(1 for d in data if d["status"] == "duplicate"),
        "clusters": len(set(d["cluster"] for d in data)),
        "data": data,
    }


# =================================================
# Export endpoint (CSV download)
# =================================================
@router.get("/export")
def export_titles(
    type: str = Query(..., description="all | unique | selected"),
    ids: str | None = Query(None, description="comma separated IDs when type=selected"),
    db: Session = Depends(get_db)
):
    query = db.query(Title)

    if type == "unique":
        query = query.filter(Title.is_duplicate == 0)
        filename = "clearoid_unique_titles.csv"
    elif type == "all":
        filename = "clearoid_all_titles.csv"
    elif type == "selected":
        if not ids:
            raise HTTPException(status_code=400, detail="ids parameter is required for type=selected")
        try:
            selected_ids = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid ids format - must be comma-separated integers")
        
        if not selected_ids:
            raise HTTPException(status_code=400, detail="No valid IDs provided")
        
        query = query.filter(Title.id.in_(selected_ids))
        filename = f"clearoid_selected_{len(selected_ids)}_titles.csv"
    else:
        raise HTTPException(status_code=400, detail="Invalid export type. Must be: all, unique or selected")

    titles = query.all()

    if not titles:
        raise HTTPException(status_code=404, detail="No titles found matching the criteria")

    # Prepare CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Headers - more useful columns
    writer.writerow([
        "ID",
        "Title",
        "Status",
        "Is Duplicate",
        "Normalized Title",
        "Similarity Score (placeholder)",
        "Created At"
    ])

    # Data rows
    for t in titles:
        writer.writerow([
            t.id,
            t.title,
            "duplicate" if t.is_duplicate else "unique",
            "Yes" if t.is_duplicate else "No",
            t.normalized_title,
            "1.000" if not t.is_duplicate else "0.92 (placeholder)",  # ← improve when real score stored
            t.created_at.strftime("%Y-%m-%d %H:%M:%S")
        ])

    output.seek(0)

    # Return as downloadable file
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache"
        }
    )


# =================================================
# DELETE: single title
# =================================================
@router.delete("/title/{title_id}")
def delete_title(title_id: int, db: Session = Depends(get_db)):
    title = db.query(Title).filter(Title.id == title_id).first()
    if not title:
        raise HTTPException(status_code=404, detail="Title not found")

    db.delete(title)
    db.commit()
    return {"success": True, "deleted_id": title_id}


# =================================================
# DELETE: multiple titles (bulk)
# =================================================
@router.post("/titles/delete")
def delete_multiple_titles(
    ids: list[int] = Body(...),
    db: Session = Depends(get_db),
):
    if not ids:
        raise HTTPException(status_code=400, detail="No IDs provided")

    deleted = db.query(Title).filter(Title.id.in_(ids)).delete(synchronize_session=False)
    db.commit()

    return {
        "success": True,
        "deleted_count": deleted,
        "ids": ids,
    }