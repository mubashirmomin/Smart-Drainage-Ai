"""
backend/app/api/v1/endpoints/inspections.py - Inspection Trigger & Video Analytics Endpoints

Project: AI-Powered Underground Drainage Intelligence and Predictive Maintenance Platform
Role: Handles CCTV video uploads, background AI processing, and delivery of annotated media.
"""

import re
import shutil
import time
from pathlib import Path
from typing import List
from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from backend.app.core.config import settings
from backend.app.schemas.inspection import (
    InspectionDetailSchema,
    InspectionSummarySchema,
)
from backend.app.services.inspection_service import inspection_service

router = APIRouter()


@router.get("/", response_model=List[InspectionSummarySchema])
def list_inspections():
    """List all past and ongoing CCTV drainage inspections."""
    return inspection_service.list_inspections()


@router.get("/{inspection_id}", response_model=InspectionDetailSchema)
def get_inspection(inspection_id: str):
    """Retrieve complete condition assessment dossier for an inspection."""
    detail = inspection_service.get_inspection_detail(inspection_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Inspection '{inspection_id}' not found.")
    return detail


@router.post("/upload")
async def upload_inspection_video(
    background_tasks: BackgroundTasks,
    pipe_id: str = Form(...),
    file: UploadFile = File(...),
):
    """
    Upload a CCTV video (.mp4, .avi, .mov), register inspection, and initiate background AI tracking.
    """
    if pipe_id not in inspection_service.pipes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid pipe_id '{pipe_id}'. Available pipes: {list(inspection_service.pipes.keys())}",
        )

    # Validate file extension
    valid_exts = {".mp4", ".avi", ".mov", ".mkv"}
    suffix = Path(file.filename).suffix.lower()
    if suffix not in valid_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported video format '{suffix}'. Allowed: {valid_exts}",
        )

    # Save uploaded file safely
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    clean_name = re.sub(r"[^a-zA-Z0-9_\.-]", "_", Path(file.filename).name)
    save_path = settings.UPLOAD_DIR / f"{pipe_id}_{int(time.time())}_{clean_name}"
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Create inspection record
    insp_id = inspection_service.create_inspection(
        pipe_id=pipe_id,
        video_file_path=save_path,
        video_filename=file.filename,
    )

    # Dispatch asynchronous background task
    background_tasks.add_task(inspection_service.execute_inspection_task, insp_id)

    return {
        "inspection_id": insp_id,
        "pipe_id": pipe_id,
        "status": "PENDING",
        "message": "Video uploaded successfully. AI defect detection and tracking initiated in background.",
        "poll_url": f"/api/v1/inspections/{insp_id}",
    }


@router.post("/run-sample")
def run_sample_inspection(
    background_tasks: BackgroundTasks,
    pipe_id: str = Form(default="PIPE-MUM-001"),
):
    """
    One-click trigger using the included benchmark CCTV video (dataset/sample_videos/cctv_inspection_sample.mp4).
    Enables instant demonstration without requiring a custom upload.
    """
    sample_video = settings.SAMPLE_VIDEOS_DIR / "cctv_inspection_sample.mp4"
    if not sample_video.exists():
        raise HTTPException(status_code=404, detail="Sample benchmark video not found on server.")

    insp_id = inspection_service.create_inspection(
        pipe_id=pipe_id,
        video_file_path=sample_video,
        video_filename=sample_video.name,
    )

    background_tasks.add_task(inspection_service.execute_inspection_task, insp_id)

    return {
        "inspection_id": insp_id,
        "pipe_id": pipe_id,
        "status": "PENDING",
        "message": "Benchmark CCTV video queued for AI defect tracking and condition assessment.",
        "poll_url": f"/api/v1/inspections/{insp_id}",
    }


@router.get("/{inspection_id}/video")
def stream_annotated_video(inspection_id: str):
    """Stream the AI-annotated inspection video with tracking boxes and HUD overlay."""
    video_path = settings.STORAGE_DIR / inspection_id / "annotated_video.mp4"
    if not video_path.exists():
        raise HTTPException(status_code=404, detail=f"Annotated video not found for '{inspection_id}'.")
    return FileResponse(path=str(video_path), media_type="video/mp4", filename=f"annotated_{inspection_id}.mp4")


@router.get("/{inspection_id}/thumbnails/{filename}")
def get_defect_thumbnail(inspection_id: str, filename: str):
    """Retrieve high-resolution defect crop thumbnail."""
    thumb_path = settings.STORAGE_DIR / inspection_id / "thumbnails" / filename
    if not thumb_path.exists():
        raise HTTPException(status_code=404, detail=f"Thumbnail '{filename}' not found.")
    return FileResponse(path=str(thumb_path), media_type="image/jpeg")
