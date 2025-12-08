from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
import pandas as pd
from io import BytesIO

from database.database import get_db
from schemas.title_schema import TitleCreate
from services.title_service import (
    save_title,
    check_duplicate,
    find_similar_titles,
    count_duplicates,
    cluster_titles,
    process_bulk_titles
)


router = APIRouter()


# ------------------------------
# Submit a title
# ------------------------------
@router.post("/submit")
def submit(item: TitleCreate, db: Session = Depends(get_db)):
    return save_title(db, item)


# ------------------------------
# Check duplicate (best match)
# ------------------------------
@router.post("/check-duplicate")
def duplicate(item: TitleCreate, db: Session = Depends(get_db)):
    return check_duplicate(db, item)


# ------------------------------
# Find similar titles
# ------------------------------
@router.post("/similar-titles")
def similar_titles(item: TitleCreate, db: Session = Depends(get_db)):
    return {
        "results": find_similar_titles(db, item)
    }


# ------------------------------
# Count total duplicates stored
# ------------------------------
@router.get("/duplicate-count")
def duplicate_count(db: Session = Depends(get_db)):
    return {
        "duplicate_count": count_duplicates(db)
    }


# ------------------------------
# Cluster titles (semantic grouping)
# ------------------------------
@router.get("/clusters")
def clusters(db: Session = Depends(get_db), k: int = 5):
    return cluster_titles(db, k)

