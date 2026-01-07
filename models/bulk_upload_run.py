from sqlalchemy import Column, Integer, String, DateTime
from database.database import Base
from datetime import datetime


class BulkUploadRun(Base):
    __tablename__ = "bulk_upload_runs"

    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    file_hash = Column(String, unique=True, nullable=False)

    processed = Column(Integer, default=0)
    saved = Column(Integer, default=0)
    duplicates = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
