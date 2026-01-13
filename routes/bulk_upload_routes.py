from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from database.database import get_db
from models.bulk_upload_run import BulkUploadRun

router = APIRouter(prefix="/bulk-uploads", tags=["Bulk Uploads"])


# -------------------------------------------------
# List all bulk upload runs (latest first)
# -------------------------------------------------
@router.get("/")
def list_bulk_uploads(db: Session = Depends(get_db)):
    """
    Returns history of all bulk upload runs
    (latest first).
    """

    runs = (
        db.query(BulkUploadRun)
        .order_by(BulkUploadRun.created_at.desc())
        .all()
    )

    return [
        {
            "id": r.id,
            "filename": r.filename,
            "processed": r.processed,
            "saved": r.saved,
            "duplicates": r.duplicates,
            "created_at": r.created_at.isoformat(),
        }
        for r in runs
    ]


# -------------------------------------------------
# Get a single bulk upload run (by ID)
# -------------------------------------------------
@router.get("/{run_id}")
def get_bulk_upload(run_id: int, db: Session = Depends(get_db)):
    """
    Get a single bulk upload run by ID.
    Useful for audit/debug/export.
    """

    run = (
        db.query(BulkUploadRun)
        .filter(BulkUploadRun.id == run_id)
        .first()
    )

    if not run:
        raise HTTPException(
            status_code=404,
            detail="Bulk upload run not found"
        )

    return {
        "id": run.id,
        "filename": run.filename,
        "processed": run.processed,
        "saved": run.saved,
        "duplicates": run.duplicates,
        "created_at": run.created_at.isoformat(),
    }
