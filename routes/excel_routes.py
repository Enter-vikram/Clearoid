from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from io import BytesIO
import pandas as pd

from database.database import get_db
from services.title_service import process_bulk_titles

router = APIRouter()


@router.post("/upload-excel")
async def upload_excel(
    file: UploadFile = File(...),
    page: int = 1,
    limit: int = 20,
    details: bool = True,
    db: Session = Depends(get_db),
):
    # read file bytes
    contents = await file.read()

    # parse excel
    try:
        df = pd.read_excel(BytesIO(contents))
    except Exception:
        raise HTTPException(400, "Invalid Excel file")

    # validate column
    if "title" not in df.columns:
        raise HTTPException(400, "'title' column missing")

    titles = df["title"].dropna().tolist()

    # run your duplicate engine
    summary = process_bulk_titles(titles, db)

    full_details = summary.get("details", [])

    # pagination + toggle
    if details:
        start = (page - 1) * limit
        end = start + limit
        page_details = full_details[start:end]
    else:
        page_details = []

    return {
        "processed": summary["processed"],
        "saved": summary["saved"],
        "duplicates": summary["duplicates"],
        "total_details": len(full_details),
        "page": page,
        "limit": limit,
        "details": page_details,
    }
