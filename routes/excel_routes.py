from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
import os
import pandas as pd
import numpy as np
import hashlib
import logging
from collections import defaultdict

from database.database import SessionLocal
from models.title import Title
from models.bulk_upload_run import BulkUploadRun
from services.ml_service import normalize
from services.embedding_service import get_embedding

router = APIRouter(prefix="/excel", tags=["Excel"])

TEMP_DIR = "./temp"
logger = logging.getLogger("clearoid.excel")


# =================================================
# Utils
# =================================================
def hash_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def detect_title_column(df: pd.DataFrame) -> str:
    df.columns = [c.strip().lower() for c in df.columns]

    aliases = {
        "title",
        "project title",
        "topic",
        "project",
        "idea",
        "name",
    }

    for col in df.columns:
        if col in aliases:
            return col

    raise ValueError(
        "Excel must contain a title column "
        "(e.g. title / project title / topic)"
    )


def dedupe_excel(df: pd.DataFrame, column: str):
    """
    Simple normalization-based deduplication.
    Returns:
        unique_df, clusters
    """
    clusters = defaultdict(list)
    rows = []

    for _, row in df.iterrows():
        raw = str(row[column]).strip()
        if not raw:
            continue

        norm = normalize(raw)
        clusters[norm].append(raw)

        rows.append({
            "title": raw,
            "normalized": norm,
        })

    unique = {}
    for r in rows:
        unique.setdefault(r["normalized"], r)

    unique_df = pd.DataFrame(unique.values())
    return unique_df, clusters


# =================================================
# Background processor
# =================================================
def process_file_bulk_bg(file_path: str, filename: str):
    db = SessionLocal()

    try:
        file_hash = hash_file(file_path)

        # -----------------------------------
        # Skip duplicate file uploads
        # -----------------------------------
        existing = (
            db.query(BulkUploadRun)
            .filter(BulkUploadRun.file_hash == file_hash)
            .first()
        )

        if existing:
            logger.info(f"Duplicate file skipped: {filename}")
            return

        # -----------------------------------
        # Load Excel
        # -----------------------------------
        df = pd.read_excel(file_path)

        title_col = detect_title_column(df)
        df = df.rename(columns={title_col: "title"})

        # -----------------------------------
        # Deduplicate titles
        # -----------------------------------
        unique_df, clusters = dedupe_excel(df, column="title")

        existing_norms = {
            r[0] for r in db.query(Title.normalized_title).all()
        }

        saved = 0

        for _, row in unique_df.iterrows():
            norm = row["normalized"]

            if not norm or norm in existing_norms:
                continue

            embedding = get_embedding(norm)
            emb_bytes = np.array(embedding, dtype=np.float32).tobytes()

            db.add(
                Title(
                    title=row["title"],
                    normalized_title=norm,
                    embedding=emb_bytes,
                    is_duplicate=False,
                )
            )

            existing_norms.add(norm)
            saved += 1

        # -----------------------------------
        # Save bulk upload run
        # -----------------------------------
        run = BulkUploadRun(
            filename=filename,
            file_hash=file_hash,
            processed=len(df),
            saved=saved,
            duplicates=len(df) - saved,
            status="completed",
        )

        db.add(run)
        db.commit()

        logger.info({
            "file": filename,
            "processed": len(df),
            "saved": saved,
            "duplicates": len(df) - saved,
            "clusters": len(clusters),
        })

    except Exception as e:
        logger.exception("Bulk upload failed")
        raise e

    finally:
        db.close()


# =================================================
# API Endpoint
# =================================================
@router.post("/bulk-upload")
async def bulk_upload(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    if not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400,
            detail="Only Excel files (.xlsx, .xls) are allowed",
        )

    os.makedirs(TEMP_DIR, exist_ok=True)
    temp_path = os.path.join(TEMP_DIR, file.filename)

    with open(temp_path, "wb") as f:
        f.write(await file.read())

    background_tasks.add_task(
        process_file_bulk_bg,
        temp_path,
        file.filename,
    )

    return {
        "status": "processing",
        "filename": file.filename,
    }
