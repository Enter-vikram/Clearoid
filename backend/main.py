import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")

# Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("clearoid")

# Database setup
from database.connection import Base, engine
from database.models import Title, BulkUploadRun

# Create temp directory for uploads
temp_dir = Path(__file__).parent.parent / "temp" / "uploads"
temp_dir.mkdir(parents=True, exist_ok=True)

# Import routers
from backend.routes.title_routes import router as title_router
from backend.routes.excel_routes import router as excel_router
from backend.routes.admin_routes import router as admin_router
from backend.routes.auth_routes import router as auth_router

# Ensure all model metadata (including auth User) is registered before table creation.
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(
    title="Clearoid",
    description="AI-Assisted Title Normalization & Duplicate Detection System",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={"success": False, "detail": "Internal server error"},
    )

# Legacy route redirects
@app.post("/submit")
async def legacy_submit_redirect():
    return RedirectResponse(url="/api/submit", status_code=307)

@app.post("/check-duplicate")
async def legacy_check_duplicate_redirect():
    return RedirectResponse(url="/api/check-duplicate", status_code=307)

# Router registration
app.include_router(title_router)
app.include_router(excel_router)
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
app.include_router(auth_router)

# Root redirect
@app.get("/")
async def root():
    return RedirectResponse(url="/index.html")

# Frontend static files
frontend_path = Path(__file__).parent.parent / "frontend"

app.mount(
    "/",
    StaticFiles(directory=str(frontend_path), html=True),
    name="frontend",
)
