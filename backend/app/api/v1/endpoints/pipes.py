"""
backend/app/api/v1/endpoints/pipes.py - Municipal Drainage Network Asset Endpoints

Project: AI-Powered Underground Drainage Intelligence and Predictive Maintenance Platform
Role: Serves pipe asset metadata, manhole coordinates, and historical condition index
for GIS mapping (Phase 10 & React Frontend).
"""

from typing import List
from fastapi import APIRouter, HTTPException

from backend.app.schemas.inspection import PipeAssetSchema
from backend.app.services.inspection_service import inspection_service

router = APIRouter()


@router.get("/", response_model=List[PipeAssetSchema])
def get_all_pipes():
    """List all monitored municipal drainage pipe segments with GIS coordinates."""
    return inspection_service.list_pipes()


@router.get("/{pipe_id}", response_model=PipeAssetSchema)
def get_pipe_by_id(pipe_id: str):
    """Retrieve details and condition of a specific drainage pipe."""
    pipe = inspection_service.get_pipe(pipe_id)
    if not pipe:
        raise HTTPException(status_code=404, detail=f"Pipe segment '{pipe_id}' not found.")
    return pipe
