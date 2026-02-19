# models/title.py
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from database.connection import Base

class Title(Base):
    __tablename__ = "titles"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Original user-entered title
    title = Column(String, nullable=False)

    # Normalized title used for fuzzy search & filtering
    normalized_title = Column(String, nullable=False, index=True)

    # Embedding stored as JSON string (vector output)
    embedding = Column(Text, nullable=False)

    # Duplicate flag (0 = unique, 1 = duplicate)
    is_duplicate = Column(Integer, default=0, index=True)

    # Timestamp for sorting by newest/oldest
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
