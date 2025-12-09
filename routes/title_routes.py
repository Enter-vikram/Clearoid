# routes/title_routes.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd
from io import BytesIO
from typing import List

from database.database import get_db
from schemas.title_schema import TitleCreate, TitleUpdate, TitleOut
from services.title_service import (
    save_title,
    check_duplicate,
    find_similar_titles,
    count_duplicates,
    process_bulk_titles,
)

from models.title import Title

router = APIRouter()


# ----------------------------------------------------------
# Submit title
# ----------------------------------------------------------
@router.post("/submit", response_model=TitleOut)
def submit(item: TitleCreate, db: Session = Depends(get_db)):
    return save_title(db, item)


# ----------------------------------------------------------
# Check duplicate
# ----------------------------------------------------------
@router.post("/check-duplicate")
def duplicate(item: TitleCreate, db: Session = Depends(get_db)):
    return check_duplicate(db, item)


# ----------------------------------------------------------
# Similar titles
# ----------------------------------------------------------
@router.post("/similar-titles")
def similar_titles(item: TitleCreate, db: Session = Depends(get_db)):
    return {"results": find_similar_titles(db, item)}


# ----------------------------------------------------------
# Duplicate count
# ----------------------------------------------------------
@router.get("/duplicate-count")
def duplicate_count(db: Session = Depends(get_db)):
    return {"duplicate_count": count_duplicates(db)}


# ----------------------------------------------------------
# ✅ Clusters (group by normalized_title)
# ----------------------------------------------------------
@router.get("/clusters")
def clusters(db: Session = Depends(get_db)):

    groups = (
        db.query(
            Title.normalized_title.label("group"),
            func.array_agg(
                func.json_build_object(
                    "id", Title.id,
                    "title", Title.title
                )
            ).label("titles"),
            func.count(Title.id).label("cnt")
        )
        .group_by(Title.normalized_title)
        .having(func.count(Title.id) > 1)
        .all()
    )

    return [
        {
            "group": g.group,
            "titles": g.titles,
            "count": g.cnt,
        }
        for g in groups
    ]


# ----------------------------------------------------------
# ✅ View a cluster
# GET /titles/group/{name}
# ----------------------------------------------------------
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


# ----------------------------------------------------------
# ✅ Delete a cluster
# DELETE /titles/group/{name}
# ----------------------------------------------------------
@router.delete("/group/{name}")
def delete_group(name: str, db: Session = Depends(get_db)):

    db.query(Title).filter(Title.normalized_title == name).delete()
    db.commit()

    return {"success": True}


# ----------------------------------------------------------
# Bulk upload
# ----------------------------------------------------------
@router.post("/bulk-upload")
async def bulk_upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files allowed")

    content = await file.read()
    df = pd.read_excel(BytesIO(content))
    return process_bulk_titles(db, df)


# ----------------------------------------------------------
# ✅ GET /titles  (pagination + filters + sort)
# ----------------------------------------------------------
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


# ----------------------------------------------------------
# GET /titles/{id}
# ----------------------------------------------------------
@router.get("/{id}", response_model=TitleOut)
def get_title_detail(id: int, db: Session = Depends(get_db)):
    title = db.query(Title).filter(Title.id == id).first()
    if not title:
        raise HTTPException(status_code=404, detail="Title not found")
    return title


# ----------------------------------------------------------
# PUT /titles/{id}
# ----------------------------------------------------------
@router.put("/{id}", response_model=TitleOut)
def update_title(id: int, item: TitleUpdate, db: Session = Depends(get_db)):
    title = db.query(Title).filter(Title.id == id).first()

    if not title:
        raise HTTPException(status_code=404, detail="Title not found")

    if item.title is not None:
        title.title = item.title

    if item.normalized_title is not None:
        title.normalized_title = item.normalized_title

    if item.is_duplicate is not None:
        title.is_duplicate = int(item.is_duplicate)

    db.add(title)
    db.commit()
    db.refresh(title)

    return title


# ----------------------------------------------------------
# DELETE /titles/{id}
# ----------------------------------------------------------
@router.delete("/{id}")
def delete_title(id: int, db: Session = Depends(get_db)):
    title = db.query(Title).filter(Title.id == id).first()

    if not title:
        raise HTTPException(status_code=404, detail="Title not found")

    db.delete(title)
    db.commit()

    return {"success": True, "message": f"Deleted title {id}"}


# ----------------------------------------------------------
# DELETE /titles/bulk-delete
# ----------------------------------------------------------
@router.delete("/bulk-delete")
def bulk_delete(ids: List[int] = Body(..., embed=True), db: Session = Depends(get_db)):
    if not ids:
        raise HTTPException(status_code=400, detail="No ids provided")

    rows = db.query(Title).filter(Title.id.in_(ids)).all()

    for r in rows:
        db.delete(r)

    db.commit()

    return {"success": True, "deleted_count": len(rows)}
