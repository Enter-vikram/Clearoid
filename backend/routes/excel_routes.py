from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Query
import pandas as pd
import numpy as np
import hashlib
import re
import uuid
from pathlib import Path

from database.connection import SessionLocal
from database.models import Title, BulkUploadRun
from backend.services.embedding_service import get_embedding
from backend.services.title_service import is_probable_duplicate
from backend.utils.text_cleaner import clean_text

router = APIRouter(prefix="/excel", tags=["Excel"])

TEMP_DIR = Path(__file__).parent.parent.parent / "temp" / "uploads"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


def hash_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def process_file_bulk_bg(file_path: str, filename: str, skip_hash_check: bool = False):
    db = SessionLocal()
    try:
        file_hash = hash_file(file_path)

        existing_run = (
            db.query(BulkUploadRun)
            .filter(BulkUploadRun.file_hash == file_hash)
            .first()
        )

        if existing_run and not skip_hash_check:
            print("Duplicate file upload skipped:", filename)
            return

        file_ext = Path(file_path).suffix.lower()
        if file_ext == ".csv":
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        # Get first column and remove NaN/empty values
        first_col = df.columns[0]
        df = df[[first_col]].dropna()
        df = df[df[first_col].astype(str).str.strip() != '']
        df = df[df[first_col].astype(str).str.lower() != 'nan']

        canonical_rows = (
            db.query(Title)
            .filter(Title.is_duplicate == 0)
            .all()
        )

        processed = 0
        saved = 0
        duplicates = 0
        clusters = {}

        for _, row in df.iterrows():
            original = str(row[first_col]).strip()
            # Preserve alphanumeric IDs (e.g., 1CG21CS127) to avoid over-collapsing
            # when IGNORE_NUMBERS is enabled for natural-language titles.
            looks_like_identifier = bool(re.match(r"^[A-Za-z0-9_-]{5,}$", original)) and any(
                ch.isalpha() for ch in original
            ) and any(ch.isdigit() for ch in original)
            normalized = original.lower() if looks_like_identifier else clean_text(original)

            if not normalized or normalized == "nan" or pd.isna(normalized):
                continue
            processed += 1

            vec = np.array(get_embedding(normalized), dtype=np.float32)
            best_row, _, is_dup = is_probable_duplicate(
                normalized,
                vec,
                canonical_rows,
            )

            cluster_key = best_row.normalized_title if best_row and is_dup else normalized
            clusters.setdefault(cluster_key, []).append(original)

            vec_bytes = vec.tobytes()

            if is_dup:
                duplicates += 1
                db.add(
                    Title(
                        title=original,
                        normalized_title=cluster_key,
                        embedding=vec_bytes,
                        is_duplicate=1,
                    )
                )
            else:
                db.add(
                    Title(
                        title=original,
                        normalized_title=normalized,
                        embedding=vec_bytes,
                        is_duplicate=0
                    )
                )

                canonical_rows.append(
                    Title(
                        title=original,
                        normalized_title=normalized,
                        embedding=vec_bytes,
                        is_duplicate=0,
                    )
                )
                saved += 1

        run_hash = file_hash
        if skip_hash_check:
            run_hash = f"{file_hash}:{uuid.uuid4().hex[:8]}"

        run = BulkUploadRun(
            filename=filename,
            file_hash=run_hash,
            processed=processed,
            saved=saved,
            duplicates=duplicates,
        )

        db.add(run)
        db.commit()

        print({
            "file": filename,
            "processed": processed,
            "saved": saved,
            "duplicates": duplicates,
            "clusters": {k: v for k, v in clusters.items() if len(v) > 1}
        })

    finally:
        db.close()


@router.post("/bulk-upload")
async def bulk_upload(
    file: UploadFile = File(...),
    force_reprocess: bool = Query(False),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    if not file.filename.lower().endswith((".xlsx", ".xls", ".csv")):
        raise HTTPException(
            status_code=400,
            detail="Only spreadsheet files (.xlsx, .xls, .csv) are allowed"
        )

    temp_path = TEMP_DIR / file.filename

    file_bytes = await file.read()
    with open(temp_path, "wb") as f:
        f.write(file_bytes)

    file_hash = hashlib.sha256(file_bytes).hexdigest()
    db = SessionLocal()
    try:
        existing_run = (
            db.query(BulkUploadRun)
            .filter(BulkUploadRun.file_hash == file_hash)
            .first()
        )
    finally:
        db.close()

    if existing_run and not force_reprocess:
        return {
            "status": "already_processed",
            "filename": file.filename,
            "processed": existing_run.processed,
            "saved": existing_run.saved,
            "duplicates": existing_run.duplicates,
            "created_at": existing_run.created_at.isoformat() if existing_run.created_at else None,
            "message": "This file was already processed. Use force_reprocess=true to process it again."
        }

    background_tasks.add_task(
        process_file_bulk_bg,
        str(temp_path),
        file.filename,
        force_reprocess
    )

    return {
        "status": "processing",
        "filename": file.filename,
        "message": "File accepted and queued for background processing."
    }
