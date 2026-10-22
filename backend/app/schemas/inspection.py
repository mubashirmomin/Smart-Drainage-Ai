"""
backend/app/schemas/inspection.py - Pydantic Request/Response Data Schemas

Project: AI-Powered Underground Drainage Intelligence and Predictive Maintenance Platform
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class InspectionStatusEnum(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class WorkOrderPriorityEnum(str, Enum):
    P1_EMERGENCY = "P1_EMERGENCY"
    P2_HIGH_PRIORITY = "P2_HIGH_PRIORITY"
    P3_MEDIUM_PRIORITY = "P3_MEDIUM_PRIORITY"
    P4_ROUTINE_MONITORING = "P4_ROUTINE_MONITORING"


class DefectItemSchema(BaseModel):
    defect_id: int
    class_name: str
    class_id: Optional[int] = None
    failure_mode: str
    description: str
    severity_score: float
    severity_grade: int
    grade_description: str
    max_area_percentage: float
    persistence_seconds: float
    first_time_sec: Optional[float] = None
    last_time_sec: Optional[float] = None
    detection_confidence: float
    recommended_repair_action: str
    target_resolution_days: int
    best_bbox: Optional[List[float]] = None
    thumbnail_url: Optional[str] = None


class PipeHealthIndicesSchema(BaseModel):
    pci_overall_score: float
    condition_state: str
    condition_description: str
    structural_index_sci: float
    operational_index_oci: float


class HydraulicAssessmentSchema(BaseModel):
    blockage_percentage: float
    blockage_severity_tier: str
    estimated_flow_loss_pct: float
    monsoon_overflow_risk: str
    flow_impeding_defects_count: int
    primary_blockage_cause: str
    immediate_cleaning_required: bool
    recommended_hydraulic_action: str


class MaintenanceDispatchSchema(BaseModel):
    work_order_priority: str
    sla_target_timeframe: str
    dispatch_rationale: str
    max_defect_grade_observed: int
    critical_defects_count: int


class AssetInspectionMetaSchema(BaseModel):
    video_file: str
    video_duration_seconds: float
    total_frames_analyzed: int
    inspection_optical_status: str
    degraded_footage_pct: float


class InspectionSummarySchema(BaseModel):
    inspection_id: str
    pipe_id: str
    street_name: str
    ward: str
    status: InspectionStatusEnum
    created_at: str
    video_filename: str
    pci_score: Optional[float] = None
    condition_state: Optional[str] = None
    priority: Optional[str] = None
    total_defects: int = 0
    blockage_percentage: Optional[float] = None
    annotated_video_url: Optional[str] = None


class InspectionDetailSchema(BaseModel):
    inspection_id: str
    pipe_id: str
    status: InspectionStatusEnum
    created_at: str
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    asset_inspection_meta: Optional[AssetInspectionMetaSchema] = None
    pipe_health_indices: Optional[PipeHealthIndicesSchema] = None
    hydraulic_conveyance_assessment: Optional[HydraulicAssessmentSchema] = None
    maintenance_dispatch_prioritization: Optional[MaintenanceDispatchSchema] = None
    detailed_defect_inventory: List[DefectItemSchema] = Field(default_factory=list)
    annotated_video_url: Optional[str] = None


class PipeAssetSchema(BaseModel):
    pipe_id: str
    street_name: str
    ward: str
    material: str
    diameter_mm: int
    length_meters: float
    installation_year: int
    start_manhole: str
    end_manhole: str
    start_coords: List[float]
    end_coords: List[float]
    criticality: str
    latest_pci: Optional[float] = None
    latest_condition_state: Optional[str] = None
    latest_priority: Optional[str] = None


class SystemHealthSchema(BaseModel):
    status: str
    version: str
    device: str
    cuda_available: bool
    gpu_name: Optional[str] = None
    vram_free_gb: Optional[float] = None
    vram_total_gb: Optional[float] = None
    model_checkpoint: str
    model_loaded: bool
    total_pipes_monitored: int
    total_inspections_logged: int
