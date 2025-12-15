# routes/title_routes.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd
import os

from database.database import get_db
from schemas.title_schema import TitleCreate, TitleOut
from services.title_service import (
    save_title,
    check_duplicate,
    find_similar_titles,
    count_duplicates,
    process_bulk_titles,
)
from models.title import Title

# For background jobs
from jobs import q, process_file_bulk

router = APIRouter()  # no prefix

# ----------------------------------------------------------
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
async def bulk_upload(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only Excel files allowed")
    
    # Read file content
    content = await file.read()
    
    # Save to temp directory
    temp_dir = "./temp"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, file.filename)
    
    with open(temp_path, "wb") as f:
        f.write(content)
    
    # Enqueue background job
    job = q.enqueue(process_file_bulk, temp_path)
    
    return {
        "job_id": job.get_id(),
        "status": "queued",
        "message": "File uploaded and processing started in background",
        "filename": file.filename
    }

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