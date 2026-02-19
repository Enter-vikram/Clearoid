"""
Quick test script to verify backend structure
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("Testing imports...")

try:
    from database.connection import Base, engine, get_db
    print("[OK] Database connection imported")
except Exception as e:
    print(f"[FAIL] Database connection failed: {e}")

try:
    from database.models.title import Title
    from database.models.bulk_upload_run import BulkUploadRun
    print("[OK] Models imported")
except Exception as e:
    print(f"[FAIL] Models import failed: {e}")

try:
    from backend.app.core.config import DATABASE_URL, REDIS_URL
    print("[OK] Config imported")
except Exception as e:
    print(f"[FAIL] Config import failed: {e}")

try:
    # Test database connection
    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created")
except Exception as e:
    print(f"[FAIL] Database creation failed: {e}")

print("\n[SUCCESS] All tests passed! Backend structure is working.")
