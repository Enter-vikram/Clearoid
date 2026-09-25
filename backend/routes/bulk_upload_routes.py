from fastapi import APIRouter, HTTPException
from database.connection import SessionLocal
from database.models import BulkUploadRun

router = APIRouter(prefix="/bulk-uploads", tags=["Bulk Uploads"])


@router.get("")
def list_bulk_uploads():
    db = SessionLocal()
    try:
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
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in runs
        ]
    finally:
        db.close()


@router.get("/{run_id}")
def get_bulk_upload(run_id: int):
    db = SessionLocal()
    try:
        run = db.query(BulkUploadRun).filter(BulkUploadRun.id == run_id).first()
        if not run:
            raise HTTPException(status_code=404, detail="Bulk upload run not found")
        return {
            "id": run.id,
            "filename": run.filename,
            "processed": run.processed,
            "saved": run.saved,
            "duplicates": run.duplicates,
            "created_at": run.created_at.isoformat() if run.created_at else None,
        }
    finally:
        db.close()
