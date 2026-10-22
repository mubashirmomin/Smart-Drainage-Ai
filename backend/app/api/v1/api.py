"""
backend/app/api/v1/api.py - API v1 Router Aggregator
"""

from fastapi import APIRouter

from backend.app.api.v1.endpoints import health, inspections, pipes

api_router = APIRouter()
api_router.include_router(health.router, tags=["System & Health"])
api_router.include_router(pipes.router, prefix="/pipes", tags=["Municipal Pipe Assets"])
api_router.include_router(inspections.router, prefix="/inspections", tags=["CCTV Inspections & Analytics"])
