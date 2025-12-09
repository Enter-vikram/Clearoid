# main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

API_KEY = os.getenv("API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# Logger setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("clearoid")


# --------------------------
# DB SETUP
# --------------------------
from database.database import Base, engine
import models.title

Base.metadata.create_all(bind=engine)


# --------------------------
# Routers
# --------------------------
from routes.title_routes import router as title_router
from routes.excel_routes import router as excel_router
from routes.admin_routes import router as admin_router


# --------------------------
# FastAPI App
# --------------------------
app = FastAPI(
    title="Clearoid",
    description="AI-Assisted Title Normalization & Duplicate Detection System",
    version="1.0.0",
)


# --------------------------
# CORS
# --------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------
# Global Error Handler
# --------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={"success": False, "detail": "Internal server error"},
    )


# --------------------------
# Register API Routers
# --------------------------
app.include_router(title_router, prefix="/titles", tags=["Titles"])
app.include_router(excel_router, prefix="/excel", tags=["Excel"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])


# --------------------------
# FRONTEND
# --------------------------
# Must be LAST — catches all frontend routing
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
