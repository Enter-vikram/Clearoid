from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.title_routes import router
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="Clearoid",
    description="AI-Assisted Form Title Normalization and Duplicate Detection System",
    version="1.0.0"
)

# Allow CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or restrict to "http://127.0.0.1:8000" later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routes
app.include_router(router)

# Serve frontend files
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
