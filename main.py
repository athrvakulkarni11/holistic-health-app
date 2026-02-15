"""
Main FastAPI application entry point.
Serves the API endpoints and the static frontend.
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.config import HOST, PORT
import uvicorn
import os

app = FastAPI(
    title="Holistic Health AI Platform",
    description="AI-powered biomarker analytics and health suggestions.",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy import to avoid loading heavy modules at import time
@app.on_event("startup")
async def startup_event():
    from app.api import router as api_router
    app.include_router(api_router, prefix="/api")
    print("[App] API routes loaded.")

# Serve static files (Frontend)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    # Only use reload in local development, never in production
    is_dev = os.getenv("ENVIRONMENT", "production").lower() == "development"
    uvicorn.run("main:app", host=HOST, port=PORT, reload=is_dev)

