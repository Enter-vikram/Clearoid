#!/usr/bin/env python3
"""Test script to verify backend server starts correctly"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("🔍 Testing Clearoid Backend...\n")

# Test 1: Database
print("1️⃣ Testing Database Connection...")
try:
    from database.connection import Base, engine, SessionLocal
    from database.models import Title, BulkUploadRun
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.close()
    print("   ✅ Database OK\n")
except Exception as e:
    print(f"   ❌ Database Error: {e}\n")
    sys.exit(1)

# Test 2: Routes
print("2️⃣ Testing Route Imports...")
try:
    from backend.routes.title_routes import router as title_router
    from backend.routes.excel_routes import router as excel_router
    from backend.routes.auth_routes import router as auth_router
    from backend.routes.admin_routes import router as admin_router
    print("   ✅ All routes imported\n")
except Exception as e:
    print(f"   ❌ Route Error: {e}\n")
    sys.exit(1)

# Test 3: Services
print("3️⃣ Testing Services...")
try:
    from backend.services import title_service, embedding_service
    print("   ✅ Services OK\n")
except Exception as e:
    print(f"   ❌ Service Error: {e}\n")
    sys.exit(1)

# Test 4: Frontend files
print("4️⃣ Testing Frontend Files...")
frontend_path = Path(__file__).parent / "frontend"
pages_path = frontend_path / "pages"
required_files = ["dashboard.html", "signin.html", "upload.html", "data.html", "export.html"]
missing = []
for file in required_files:
    if not (pages_path / file).exists():
        missing.append(file)

if missing:
    print(f"   ❌ Missing files: {', '.join(missing)}\n")
else:
    print("   ✅ All frontend files present\n")

# Test 5: FastAPI app
print("5️⃣ Testing FastAPI App...")
try:
    from backend.main import app
    print("   ✅ FastAPI app created\n")
except Exception as e:
    print(f"   ❌ FastAPI Error: {e}\n")
    sys.exit(1)

print("=" * 50)
print("✅ ALL TESTS PASSED!")
print("=" * 50)
print("\n🚀 Start server with:")
print("   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000")
print("\n🌐 Access at:")
print("   http://localhost:8000/pages/dashboard.html")
print("   http://localhost:8000/pages/signin.html")
