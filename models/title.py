from sqlalchemy import Column, Integer, String, Text
from database.database import Base

class Title(Base):
    __tablename__ = "titles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    normalized_title = Column(String, nullable=False, index=True)

    # embedding stored as JSON text
    embedding = Column(Text, nullable=False)

    # ✅ REQUIRED by your service: marks whether title is duplicate
    is_duplicate = Column(Integer, default=0, index=True)
