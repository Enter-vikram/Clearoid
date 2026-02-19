#!/bin/bash

# Clearoid Project Refactoring Script
# Run this to clean and organize the project

set -e

PROJECT_DIR="/Users/santhoshkumar/Downloads/Testing-files--main"
cd "$PROJECT_DIR"

echo "🧹 Starting Clearoid Project Refactoring..."
echo ""

# ============================================================
# STEP 1: DELETE TEMPORARY & JUNK FILES
# ============================================================
echo "📦 Step 1: Removing temporary and junk files..."

rm -rf temp/
rm -f test_connections.py test_structure.py
rm -f start.sh start.bat START_CLEAROID.bat RUN.sh install.sh test_and_run.sh START.sh
rm -f ARCHITECTURE.md COMMANDS.txt CONNECTION_GUIDE.md DEPLOYMENT_CHECKLIST.md
rm -f IMPORT_FIX_COMPLETE.md NAVIGATION_UPDATE_GUIDE.txt QUICKSTART.md
rm -f REFACTOR_COMPLETE.md RUN_COMMAND.md SETUP_COMPLETE.md START_HERE.md
rm -f PUBLIC_AUTH_SPLIT.txt
rm -rf docs/
rm -rf .github/
rm -f frontend/README.md

echo "✅ Temporary files removed"

# ============================================================
# STEP 2: DELETE DUPLICATE BACKEND FILES
# ============================================================
echo "📦 Step 2: Removing duplicate backend files..."

rm -rf backend/app/
rm -rf backend/models/
rm -rf backend/schemas/
rm -f database/database.py
rm -rf database/migrations/

echo "✅ Duplicate backend files removed"

# ============================================================
# STEP 3: DELETE DUPLICATE FRONTEND FILES
# ============================================================
echo "📦 Step 3: Removing duplicate frontend files..."

cd frontend
rm -f components.html landing.html index.html

echo "✅ Duplicate frontend files removed"

# ============================================================
# STEP 4: REORGANIZE FRONTEND STRUCTURE
# ============================================================
echo "📦 Step 4: Reorganizing frontend structure..."

mkdir -p pages assets/css

# Move HTML files
mv Dashboard.html pages/dashboard.html 2>/dev/null || true
mv signin.html pages/signin.html 2>/dev/null || true
mv upload.html pages/upload.html 2>/dev/null || true
mv data.html pages/data.html 2>/dev/null || true
mv history.html pages/history.html 2>/dev/null || true
mv Export.html pages/export.html 2>/dev/null || true

# Move CSS
mv styles.css assets/css/styles.css 2>/dev/null || true

cd ..

echo "✅ Frontend reorganized"

# ============================================================
# STEP 5: UPDATE BACKEND MAIN.PY
# ============================================================
echo "📦 Step 5: Updating backend configuration..."

cat > backend/main.py << 'EOF'
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse
from dotenv import load_dotenv
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv(Path(__file__).parent.parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("clearoid")

from database.connection import Base, engine
from database.models import Title, BulkUploadRun

Base.metadata.create_all(bind=engine)

from backend.routes.title_routes import router as title_router
from backend.routes.excel_routes import router as excel_router
from backend.routes.admin_routes import router as admin_router
from backend.routes.auth_routes import router as auth_router

app = FastAPI(title="Clearoid", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception")
    return JSONResponse(status_code=500, content={"success": False, "detail": "Internal server error"})

app.include_router(title_router)
app.include_router(excel_router)
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
app.include_router(auth_router)

frontend_path = Path(__file__).parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
EOF

echo "✅ Backend updated"

# ============================================================
# STEP 6: CREATE UPLOADS DIRECTORY
# ============================================================
echo "📦 Step 6: Creating uploads directory..."

mkdir -p uploads

echo "✅ Uploads directory created"

# ============================================================
# STEP 7: UPDATE EXCEL ROUTES
# ============================================================
echo "📦 Step 7: Updating excel routes..."

cat > backend/routes/excel_routes.py << 'EOF'
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
import pandas as pd
import numpy as np
import hashlib
from pathlib import Path

from database.connection import SessionLocal
from database.models import Title, BulkUploadRun
from backend.services.excel_deduper import dedupe_excel
from backend.services.embedding_service import get_embedding

router = APIRouter(prefix="/excel", tags=["Excel"])

UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def hash_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def process_file_bulk_bg(file_path: str, filename: str):
    db = SessionLocal()
    try:
        file_hash = hash_file(file_path)
        existing_run = db.query(BulkUploadRun).filter(BulkUploadRun.file_hash == file_hash).first()
        
        if existing_run:
            print("Duplicate file upload skipped:", filename)
            return

        df = pd.read_excel(file_path)
        first_col = df.columns[0]
        df = df[[first_col]].dropna()
        df = df[df[first_col].astype(str).str.strip() != '']
        df = df[df[first_col].astype(str).str.lower() != 'nan']

        unique_df, clusters = dedupe_excel(df, column=None, ignore_numbers=True)
        existing_norms = {r[0] for r in db.query(Title.normalized_title).all()}
        saved = 0

        for _, row in unique_df.iterrows():
            normalized = row["normalized"]
            if not normalized or normalized == 'nan' or pd.isna(normalized):
                continue
            if normalized in existing_norms:
                continue

            vec = get_embedding(normalized)
            vec_bytes = np.array(vec, dtype=np.float32).tobytes()
            db.add(Title(title=row[first_col], normalized_title=normalized, embedding=vec_bytes, is_duplicate=0))
            existing_norms.add(normalized)
            saved += 1

        run = BulkUploadRun(filename=filename, file_hash=file_hash, processed=len(df), saved=saved, duplicates=len(df) - saved)
        db.add(run)
        db.commit()
        print({"file": filename, "processed": len(df), "saved": saved, "duplicates": len(df) - saved})
    finally:
        db.close()

@router.post("/bulk-upload")
async def bulk_upload(file: UploadFile = File(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    if not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are allowed")
    
    temp_path = UPLOAD_DIR / file.filename
    with open(temp_path, "wb") as f:
        f.write(await file.read())
    
    background_tasks.add_task(process_file_bulk_bg, str(temp_path), file.filename)
    return {"status": "processing", "filename": file.filename}
EOF

echo "✅ Excel routes updated"

# ============================================================
# DONE
# ============================================================
echo ""
echo "✅ Refactoring complete!"
echo ""
echo "📁 New structure:"
echo "   backend/ - API routes, services, utils"
echo "   database/ - Models and connection"
echo "   frontend/pages/ - HTML pages"
echo "   frontend/assets/css/ - Stylesheets"
echo "   uploads/ - File uploads"
echo ""
echo "🚀 To start the server:"
echo "   cd backend && uvicorn main:app --reload"
echo ""
