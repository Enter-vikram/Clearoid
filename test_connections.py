#!/usr/bin/env python3
"""Connection smoke checks for local development and pytest."""

import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def check_imports() -> bool:
    print("Testing imports...")

    try:
        from database.connection import Base, engine, SessionLocal, get_db  # noqa: F401
        print("✅ Database connection imports OK")
    except Exception as e:
        print(f"❌ Database connection imports FAILED: {e}")
        return False

    try:
        from database.models import Title, BulkUploadRun  # noqa: F401
        print("✅ Database models imports OK")
    except Exception as e:
        print(f"❌ Database models imports FAILED: {e}")
        return False

    try:
        from backend.services.title_service import save_title, check_duplicate  # noqa: F401
        print("✅ Title service imports OK")
    except Exception as e:
        print(f"❌ Title service imports FAILED: {e}")
        return False

    try:
        from backend.services.embedding_service import get_embedding  # noqa: F401
        print("✅ Embedding service imports OK")
    except Exception as e:
        print(f"❌ Embedding service imports FAILED: {e}")
        return False

    try:
        from backend.routes.title_routes import router as title_router  # noqa: F401
        from backend.routes.excel_routes import router as excel_router  # noqa: F401
        from backend.routes.admin_routes import router as admin_router  # noqa: F401
        print("✅ All routes imports OK")
    except Exception as e:
        print(f"❌ Routes imports FAILED: {e}")
        return False

    return True


def check_database() -> bool:
    print("\nTesting database connection...")

    try:
        from database.connection import Base, engine, SessionLocal
        from database.models import Title, BulkUploadRun  # noqa: F401

        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")

        db = SessionLocal()
        count = db.query(Title).count()
        db.close()
        print(f"✅ Database query successful (found {count} titles)")
        return True
    except Exception as e:
        print(f"❌ Database test FAILED: {e}")
        return False


def check_directories() -> bool:
    print("\nTesting directory structure...")

    required_dirs = [
        Path("temp/uploads"),
        Path("database"),
        Path("backend"),
        Path("frontend"),
    ]

    all_exist = True
    for dir_path in required_dirs:
        if dir_path.exists():
            print(f"✅ {dir_path} exists")
        else:
            print(f"❌ {dir_path} missing")
            all_exist = False

    return all_exist


def check_env() -> bool:
    print("\nTesting environment configuration...")
    env_file = Path(".env")

    if not env_file.exists():
        print("❌ .env file missing")
        return False

    print("✅ .env file exists")
    content = env_file.read_text(encoding="utf-8")
    if "DATABASE_URL" in content:
        print("✅ DATABASE_URL configured")
    else:
        print("⚠️  DATABASE_URL not found in .env")
    return True


def test_imports():
    assert check_imports()


def test_database():
    assert check_database()


def test_directories():
    assert check_directories()


def test_env():
    assert check_env()


def main():
    print("=" * 60)
    print("Clearoid Connection Test")
    print("=" * 60)

    results = [
        ("Imports", check_imports()),
        ("Database", check_database()),
        ("Directories", check_directories()),
        ("Environment", check_env()),
    ]

    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:20s}: {status}")

    all_passed = all(result[1] for result in results)

    print("=" * 60)
    if all_passed:
        print("🎉 All tests passed! System is ready.")
        print("\nStart the server with:")
        print("  ./start.sh")
        print("\nOr manually:")
        print("  uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000")
    else:
        print("⚠️  Some tests failed. Check errors above.")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
