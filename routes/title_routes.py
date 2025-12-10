# routes/title_routes.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd
from io import BytesIO
from typing import List

from database.database import get_db, SessionLocal
from schemas.title_schema import TitleCreate, TitleUpdate, TitleOut
from services.title_service import (
    save_title,
    check_duplicate,
    find_similar_titles,
    count_duplicates,
    process_bulk_titles,
)
from models.title import Title

router = APIRouter()   # no prefix

# WEBHOOK ENDPOINT — FINAL 100% WORKING VERSION
from services.ml_service import get_embedding, find_duplicates
import numpy as np

@router.post("/title")
async def webhook_receive_title(payload: TitleCreate):
    embedding = get_embedding(payload.title)
    duplicate_info, score = find_duplicates(payload.title)
    status = "duplicate" if duplicate_info else "unique"

    db = SessionLocal()
    try:
        new_entry = Title(
            title=payload.title,
            normalized_title=payload.title.lower().strip(),
            embedding=embedding.tobytes(),
            is_duplicate=1 if status == "duplicate" else 0,
        )
        db.add(new_entry)
        db.commit()
    finally:
        db.close()

    return {
        "title": payload.title,
        "status": status,
        "similarity_score": round(score, 3),
        "duplicate_match": duplicate_info
    }

# ----------------------------------------------------------
@router.post("/submit", response_model=TitleOut)
def submit(item: TitleCreate, db: Session = Depends(get_db)):
    return save_title(db, item)

@router.post("/check-duplicate")
def duplicate(item: TitleCreate, db: Session = Depends(get_db)):
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
            func.array_agg(
                func.json_build_object("id", Title.id, "title", Title.title)
            ).label("titles"),
            func.count(Title.id).label("cnt")
        )
        .group_by(Title.normalized_title)
        .having(func.count(Title.id) > 1)
        .all()
    )
    return [{"group": g.group, "titles": g.titles, "count": g.cnt} for g in groups]

@router.get("/group/{name}")
def view_group(name: str, db: Session = Depends(get_db)):
    rows = db.query(Title).filter(Title.normalized_title == name).all()
    return {
        "group": name,
        "items": [
            {
                "id": r.id,
                "title": r.title,
                "normalized": r.normalized_title,
                "duplicate": r.is_duplicate,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ]
    }

@router.delete("/group/{name}")
def delete_group(name: str, db: Session = Depends(get_db)):
    db.query(Title).filter(Title.normalized_title == name).delete()
    db.commit()
    return {"success": True}

@router.post("/bulk-upload")
async def bulk_upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files allowed")
    content = await file.read()
    df = pd.read_excel(BytesIO(content))
    return process_bulk_titles(db, df)

@router.get("/", summary="Get titles list")
def get_titles(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1),
    search: str | None = None,
    duplicates: bool | None = None,
    sort: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Title)
    if search:
        query = query.filter(
            (Title.title.ilike(f"%{search}%")) |
            (Title.normalized_title.ilike(f"%{search}%"))
        )
    if duplicates is not None:
        flag = 1 if duplicates else 0
        query = query.filter(Title.is_duplicate == flag)
    if sort == "newest":
        query = query.order_by(Title.created_at.desc())
    elif sort == "oldest":
        query = query.order_by(Title.created_at.asc())
    else:
        query = query.order_by(Title.created_at.desc())

    total = query.count()
    titles = query.offset((page - 1) * limit).limit(limit).all()
    return {
        "success": True,
        "page": page,
        "limit": limit,
        "total": total,
        "data": [
            {
                "id": t.id,
                "title": t.title,
                "normalized_title": t.normalized_title,
                "is_duplicate": t.is_duplicate,
                "created_at": t.created_at.isoformat(),
            }
            for t in titles
        ],
    }