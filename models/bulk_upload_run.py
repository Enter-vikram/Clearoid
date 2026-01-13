# models/bulk_upload_run.py

from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from database.database import Base


class BulkUploadRun(Base):
    __tablename__ = "bulk_upload_runs"

    id = Column(Integer, primary_key=True, index=True)

    filename = Column(String, nullable=False)
    file_hash = Column(String, nullable=False, unique=True)

    processed = Column(Integer, default=0)
    saved = Column(Integer, default=0)
    duplicates = Column(Integer, default=0)

    # ✅ THIS WAS MISSING
    cluster_count = Column(Integer, default=0)

    # Optional but useful
    status = Column(String, default="completed")

    created_at = Column(DateTime, default=datetime.utcnow)
