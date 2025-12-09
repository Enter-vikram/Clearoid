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
    # read uploaded file
    contents = await file.read()

    # parse excel file
    try:
        df = pd.read_excel(BytesIO(contents))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Excel file")

    # verify required column
    if "title" not in df.columns:
        raise HTTPException(status_code=400, detail="'title' column missing")

    # run main Bulk Processing Engine
    summary = process_bulk_titles(db, df)

    all_details = summary.get("details", [])

    # pagination / detail toggling
    if details:
        start = (page - 1) * limit
        end = start + limit
        paginated = all_details[start:end]
    else:
        paginated = []

    return {
        "processed": summary["processed"],
        "saved": summary["saved"],
        "duplicates": summary["duplicates"],
        "total_details": len(all_details),
        "page": page,
        "limit": limit,
        "details": paginated,
    }
