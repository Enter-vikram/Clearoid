from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse
from dotenv import load_dotenv
import logging

# -------------------------------------------------
# ENV
# -------------------------------------------------
# Always load .env safely
load_dotenv()

# -------------------------------------------------
# LOGGER
# -------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("clearoid")

# -------------------------------------------------
# DB SETUP
# -------------------------------------------------
from database.database import Base, engine

# ⚠️ IMPORTANT
# Import ALL models BEFORE create_all
# Otherwise tables will NOT be created
import models.title
import models.bulk_upload_run

Base.metadata.create_all(bind=engine)

# -------------------------------------------------
# ROUTERS
# -------------------------------------------------
from routes.title_routes import router as title_router
from routes.excel_routes import router as excel_router
from routes.admin_routes import router as admin_router

# -------------------------------------------------
# FASTAPI APP
# -------------------------------------------------
app = FastAPI(
    title="Clearoid",
    description="AI-Assisted Title Normalization & Duplicate Detection System",
    version="1.0.0",
)

# -------------------------------------------------
# CORS (frontend safe)
# -------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # tighten later if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# GLOBAL ERROR HANDLER
# -------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "detail": "Internal server error"
        },
    )

# -------------------------------------------------
# LEGACY ROUTE SAFETY (FIXES 405 ERRORS)
# -------------------------------------------------
# Old frontend / API calls safety net

@app.post("/submit")
async def legacy_submit_redirect():
    return RedirectResponse(
        url="/api/submit",
        status_code=307
    )

@app.post("/check-duplicate")
async def legacy_check_duplicate_redirect():
    return RedirectResponse(
        url="/api/check-duplicate",
        status_code=307
    )

# -------------------------------------------------
# ROUTER REGISTRATION (ORDER MATTERS)
# -------------------------------------------------
# title_routes -> prefix="/api"
# excel_routes -> prefix="/excel"
# admin_routes -> prefix="/admin"

app.include_router(title_router)
app.include_router(excel_router)
app.include_router(admin_router, prefix="/admin", tags=["Admin"])

# -------------------------------------------------
# FRONTEND (STATIC FILES)
# -------------------------------------------------
# Serves:
# /index.html
# /upload.html
# /history.html
# /export.html
app.mount(
    "/",
    StaticFiles(directory="frontend", html=True),
    name="frontend",
)
