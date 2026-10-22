"""
backend/app/api/v1/endpoints/health.py - System Health & Maintenance Prioritization Queue Endpoints

Project: AI-Powered Underground Drainage Intelligence and Predictive Maintenance Platform
"""

from typing import Dict, List
from fastapi import APIRouter
import torch

from backend.app.core.config import settings
from backend.app.schemas.inspection import SystemHealthSchema
from backend.app.services.inspection_service import inspection_service

router = APIRouter()


@router.get("/health", response_model=SystemHealthSchema)
def get_system_health():
    """Diagnostic system health check for GPU, CUDA, and model checkpoint status."""
    cuda_avail = torch.cuda.is_available()
    device = "CUDA:0" if cuda_avail else "CPU"
    gpu_name = torch.cuda.get_device_name(0) if cuda_avail else None

    vram_free = None
    vram_total = None
    if cuda_avail:
        free_bytes, total_bytes = torch.cuda.mem_get_info()
        vram_free = round(free_bytes / (1024**3), 2)
        vram_total = round(total_bytes / (1024**3), 2)

    weights_path = settings.model_weights_path

    return SystemHealthSchema(
        status="HEALTHY",
        version=settings.PROJECT_VERSION,
        device=device,
        cuda_available=cuda_avail,
        gpu_name=gpu_name,
        vram_free_gb=vram_free,
        vram_total_gb=vram_total,
        model_checkpoint=str(weights_path.name),
        model_loaded=weights_path.exists(),
        total_pipes_monitored=len(inspection_service.pipes),
        total_inspections_logged=len(inspection_service.inspections),
    )


@router.get("/queue")
def get_work_order_queue():
    """
    Returns prioritized maintenance work order queue categorized into
    P1 (Emergency), P2 (High), P3 (Medium), P4 (Routine).
    """
    queue = {
        "P1_EMERGENCY": [],
        "P2_HIGH_PRIORITY": [],
        "P3_MEDIUM_PRIORITY": [],
        "P4_ROUTINE_MONITORING": [],
    }

    for insp_id, data in inspection_service.inspections.items():
        if data.get("status") != "COMPLETED":
            continue
        dossier = data.get("dossier", {})
        prio_info = dossier.get("maintenance_dispatch_prioritization", {})
        prio = prio_info.get("work_order_priority", "P4_ROUTINE_MONITORING")
        pipe_id = data.get("pipe_id", "UNKNOWN")
        pipe = inspection_service.pipes.get(pipe_id, {})

        item = {
            "inspection_id": insp_id,
            "pipe_id": pipe_id,
            "street_name": pipe.get("street_name", "Municipal Line"),
            "ward": pipe.get("ward", "General"),
            "pci_score": dossier.get("pipe_health_indices", {}).get("pci_overall_score"),
            "blockage_percentage": dossier.get("hydraulic_conveyance_assessment", {}).get("blockage_percentage"),
            "sla_timeframe": prio_info.get("sla_target_timeframe"),
            "dispatch_rationale": prio_info.get("dispatch_rationale"),
            "defect_count": len(dossier.get("detailed_defect_inventory", [])),
            "primary_repair_actions": [
                d.get("recommended_repair_action")
                for d in dossier.get("detailed_defect_inventory", [])[:3]
            ],
            "inspection_date": data.get("created_at"),
        }
        if prio in queue:
            queue[prio].append(item)
        else:
            queue["P4_ROUTINE_MONITORING"].append(item)

    return {
        "summary": {
            "p1_emergency_count": len(queue["P1_EMERGENCY"]),
            "p2_high_count": len(queue["P2_HIGH_PRIORITY"]),
            "p3_medium_count": len(queue["P3_MEDIUM_PRIORITY"]),
            "p4_routine_count": len(queue["P4_ROUTINE_MONITORING"]),
            "total_active_work_orders": sum(len(v) for v in queue.values()),
        },
        "work_order_queue": queue,
    }
