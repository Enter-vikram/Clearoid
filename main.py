from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# --- Database setup ---
from database.database import Base, engine

# Import models so SQLAlchemy registers them
import models.title  

# Create tables BEFORE routers touch anything
Base.metadata.create_all(bind=engine)

# --- Routers ---
from routes.title_routes import router as title_router
from routes.excel_routes import router as excel_router

# --- App ---
app = FastAPI(
    title="Clearoid",
    description="AI-Assisted Form Title Normalization and Duplicate Detection System",
    version="1.0.0",
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API routes ---
app.include_router(title_router, prefix="/titles")
app.include_router(excel_router, prefix="/excel")

# --- Frontend (must be last) ---
#app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

