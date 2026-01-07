from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./titles.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# 🔽 IMPORTANT: force model registration
# Without these imports, tables will NEVER be created
from models.title import Title
from models.bulk_upload_run import BulkUploadRun 


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
