"""
Backend configuration
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/database/titles.db")

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Upload
UPLOAD_DIR = BASE_DIR / "temp" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB

# ML
SIMILARITY_THRESHOLD = 85
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = ENVIRONMENT == "development"
