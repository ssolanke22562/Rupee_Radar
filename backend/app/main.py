from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.database import engine, Base
from backend.app.api.v1.router import api_router
import threading
import logging
import os

# Create database tables
Base.metadata.create_all(bind=engine)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="RupeeRadar API",
    description="AI-powered personal finance assistant backend",
    version="1.0.0"
)

# CORS middleware configuration — allow specific origins or all for development
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
origins = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API router
app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
def startup_event():
    """
    Phase 6.1: Start the background TTL purge worker on app startup.
    Runs every 30 minutes to clean up expired sessions and uploaded files.
    """
    from backend.app.pipeline.session_purge import start_purge_worker
    purge_thread = threading.Thread(target=start_purge_worker, daemon=True)
    purge_thread.start()
    logger.info("Session TTL purge worker started (runs every 30 minutes).")

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "service": "RupeeRadar Backend"}