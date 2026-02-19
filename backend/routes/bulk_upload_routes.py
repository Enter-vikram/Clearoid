from fastapi import APIRouter
from database.database import SessionLocal
from backend.models.bulk_upload_run import BulkUploadRun

router = APIRouter(prefix="/bulk-uploads", tags=["Bulk Uploads"])


@router.get("")
def list_bulk_uploads():
    """
    Returns history of all bulk upload runs
    (latest first).
    """
    db = SessionLocal()
    try:
        return (
            db.query(BulkUploadRun)
            .order_by(BulkUploadRun.created_at.desc())
            .all()
        )
    finally:
        db.close()


@router.get("/{run_id}")
def get_bulk_upload(run_id: int):
    """
    Get a single bulk upload run by ID.
    Useful for audit/debug.
    """
    db = SessionLocal()
    try:
        run = (
            db.query(BulkUploadRun)
            .filter(BulkUploadRun.id == run_id)
            .first()
        )

        if not run:
            return {"error": "Bulk upload run not found"}

        return run
    finally:
        db.close()
