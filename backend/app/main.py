"""
backend/app/main.py - Main FastAPI Application Entrypoint

Project: AI-Powered Underground Drainage Intelligence and Predictive Maintenance Platform
Environment: Windows OS, FastAPI, PyTorch + CUDA, React Frontend
"""

import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add project root to sys.path so modules resolve cleanly
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from backend.app.api.v1.api import api_router
from backend.app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description=(
        "Production AI Platform for Municipal Underground Sewer & Stormwater CCTV Analytics. "
        "Performs automated defect detection, multi-frame ByteTrack deduplication, "
        "hydraulic blockage modeling, Pipe Condition Index (PCI 0-100) scoring, "
        "and prioritized maintenance work order generation."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS Middleware for Vite / React Frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
def root():
    """Root platform entrypoint."""
    return JSONResponse(
        content={
            "platform": settings.PROJECT_NAME,
            "version": settings.PROJECT_VERSION,
            "status": "ONLINE",
            "documentation": "/docs",
            "api_v1_base": settings.API_V1_STR,
            "system_health": f"{settings.API_V1_STR}/health",
            "pipes_endpoint": f"{settings.API_V1_STR}/pipes",
            "inspections_endpoint": f"{settings.API_V1_STR}/inspections",
            "maintenance_queue": f"{settings.API_V1_STR}/queue",
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main.app", host="0.0.0.0", port=8000, reload=True)
