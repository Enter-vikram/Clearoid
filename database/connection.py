import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load env from project root if present.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Default to local sqlite DB if DATABASE_URL is not provided.
DEFAULT_DB_PATH = Path(__file__).resolve().parent / "titles.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

# Ensure sqlite directory exists when using sqlite URLs.
if DATABASE_URL.startswith("sqlite:///"):
    sqlite_target = Path(DATABASE_URL.replace("sqlite:///", "", 1))
    sqlite_target.parent.mkdir(parents=True, exist_ok=True)

engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
