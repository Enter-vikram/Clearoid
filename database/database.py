# database/database.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import logging

logger = logging.getLogger("clearoid.db")

# -------------------------------------------------
# LOAD ENV (explicit & safe)
# -------------------------------------------------
load_dotenv(override=True)

# Default to SQLite if anything goes wrong
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./clearoid.db")

# Normalize common mistakes
if DATABASE_URL.startswith("sqlite:///") is False and DATABASE_URL.startswith("sqlite://") is False:
    # Hard safety: prevent accidental MySQL usage
    if DATABASE_URL.startswith("mysql"):
        raise RuntimeError(
            "❌ MySQL detected in DATABASE_URL but MySQL is not supported.\n"
            "Fix your .env to use SQLite:\n"
            "DATABASE_URL=sqlite:///./clearoid.db"
        )

logger.info("Using DATABASE_URL=%s", DATABASE_URL)

# -------------------------------------------------
# ENGINE
# -------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
    if DATABASE_URL.startswith("sqlite")
    else {},
    future=True,
)

# -------------------------------------------------
# SESSION
# -------------------------------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()

# -------------------------------------------------
# DEPENDENCY
# -------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
