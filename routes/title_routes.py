from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database.database import get_db, Title

router = APIRouter()

# Pydantic model for request body
class TitleItem(BaseModel):
    title: str

# -------------------------------
# GET route to check server
# -------------------------------
@router.get("/")
def root():
    return {"message": "Clearoid backend is running!"}

# -------------------------------
# POST /submit route
# -------------------------------
@router.post("/submit")   # <-- THIS IS THE POST ROUTE
def submit_title(item: TitleItem, db: Session = Depends(get_db)):
    # Normalize title
    normalized = item.title.lower().strip()

    # Create a Title object
    new_title = Title(title=item.title, normalized_title=normalized)

    # Add to DB
    db.add(new_title)
    db.commit()
    db.refresh(new_title)

    return {"message": "Title stored successfully", "id": new_title.id}

@router.post("/check-duplicate")
def check_duplicate(item: TitleItem, db: Session = Depends(get_db)):
    normalized = item.title.lower().strip()
    
    # Check if the normalized title exists
    existing = db.query(Title).filter(Title.normalized_title == normalized).first()
    
    if existing:
        return {"duplicate": True, "id": existing.id, "title": existing.title}
    else:
        return {"duplicate": False}
