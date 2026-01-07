from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.database import get_db
from schemas.title_schema import TitleCreate, TitleOut
from services.title_service import (
    save_title,
    check_duplicate,
    find_similar_titles,
    count_duplicates,
)
from models.title import Title

router = APIRouter(prefix="/api", tags=["Titles"])


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
