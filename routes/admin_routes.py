# routes/admin_routes.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.database import get_db
from models.title import Title

router = APIRouter()


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    total = db.query(func.count(Title.id)).scalar()

    dup_count = (
        db.query(func.count(Title.id))
        .filter(Title.is_duplicate == 1)
        .scalar()
    )

    unique = total - dup_count

    avg_len = db.query(func.avg(func.length(Title.title))).scalar() or 0

    top_norm = (
        db.query(
            Title.normalized_title,
            func.count(Title.id).label("cnt")
        )
        .group_by(Title.normalized_title)
        .order_by(func.count(Title.id).desc())
        .limit(10)
        .all()
    )

    recent = (
        db.query(Title)
        .order_by(Title.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "total": total,
        "duplicates": dup_count,
        "unique": unique,
        "avg_title_length": float(avg_len),
        "top_normalized": [
            {"normalized": n, "count": c}
            for n, c in top_norm
        ],
        "recent": [
            {
                "id": r.id,
                "title": r.title,
                "created_at": r.created_at.isoformat(),
            }
            for r in recent
        ],
    }
