/**
 * frontend/src/types.ts - TypeScript Interfaces matching FastAPI Backend Schemas
 */

export interface DefectItem {
  defect_id: number;
  class_name: string;
  class_id?: number;
  failure_mode: 'STRUCTURAL' | 'HYDRAULIC' | string;
  description: string;
  severity_score: number;
  severity_grade: number; // 1 to 5
  grade_description: string;
  max_area_percentage: number;
  persistence_seconds: number;
  first_time_sec?: number;
  last_time_sec?: number;
  detection_confidence: number;
  recommended_repair_action: string;
  target_resolution_days: number;
  best_bbox?: number[];
  thumbnail_url?: string;
}

export interface PipeHealthIndices {
  pci_overall_score: number;
  condition_state: 'EXCELLENT' | 'GOOD' | 'FAIR' | 'POOR' | 'CRITICAL' | string;
  condition_description: string;
  structural_index_sci: number;
  operational_index_oci: number;
}

export interface HydraulicAssessment {
  blockage_percentage: number;
  blockage_severity_tier: string;
  estimated_flow_loss_pct: number;
  monsoon_overflow_risk: string;
  flow_impeding_defects_count: number;
  primary_blockage_cause: string;
  immediate_cleaning_required: boolean;
  recommended_hydraulic_action: string;
}

export interface MaintenanceDispatch {
  work_order_priority: 'P1_EMERGENCY' | 'P2_HIGH_PRIORITY' | 'P3_MEDIUM_PRIORITY' | 'P4_ROUTINE_MONITORING' | string;
  sla_target_timeframe: string;
  dispatch_rationale: string;
  max_defect_grade_observed: number;
  critical_defects_count: number;
}

export interface AssetInspectionMeta {
  video_file: string;
  video_duration_seconds: number;
  total_frames_analyzed: number;
  inspection_optical_status: string;
  degraded_footage_pct: number;
}

export interface InspectionSummary {
  inspection_id: string;
  pipe_id: string;
  street_name: string;
  ward: string;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  created_at: string;
  video_filename: string;
  pci_score?: number;
  condition_state?: string;
  priority?: string;
  total_defects: number;
  blockage_percentage?: number;
  annotated_video_url?: string;
}

export interface InspectionDetail {
  inspection_id: string;
  pipe_id: string;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  created_at: string;
  completed_at?: string;
  error_message?: string;
  asset_inspection_meta?: AssetInspectionMeta;
  pipe_health_indices?: PipeHealthIndices;
  hydraulic_conveyance_assessment?: HydraulicAssessment;
  maintenance_dispatch_prioritization?: MaintenanceDispatch;
  detailed_defect_inventory: DefectItem[];
  annotated_video_url?: string;
}

export interface PipeAsset {
  pipe_id: string;
  street_name: string;
  ward: string;
  material: string;
  diameter_mm: number;
  length_meters: number;
  installation_year: number;
  start_manhole: string;
  end_manhole: string;
  start_coords: [number, number]; // [lat, lng]
  end_coords: [number, number];
  criticality: string;
  latest_pci?: number;
  latest_condition_state?: string;
  latest_priority?: string;
}

export interface SystemHealth {
  status: string;
  version: string;
  device: string;
  cuda_available: boolean;
  gpu_name?: string;
  vram_free_gb?: number;
  vram_total_gb?: number;
  model_checkpoint: string;
  model_loaded: boolean;
  total_pipes_monitored: number;
  total_inspections_logged: number;
}

export interface WorkOrderItem {
  inspection_id: string;
  pipe_id: string;
  street_name: string;
  ward: string;
  pci_score?: number;
  blockage_percentage?: number;
  sla_timeframe: string;
  dispatch_rationale: string;
  defect_count: number;
  primary_repair_actions: string[];
  inspection_date: string;
}

export interface WorkOrderQueueResponse {
  summary: {
    p1_emergency_count: number;
    p2_high_count: number;
    p3_medium_count: number;
    p4_routine_count: number;
    total_active_work_orders: number;
  };
  work_order_queue: {
    P1_EMERGENCY: WorkOrderItem[];
    P2_HIGH_PRIORITY: WorkOrderItem[];
    P3_MEDIUM_PRIORITY: WorkOrderItem[];
    P4_ROUTINE_MONITORING: WorkOrderItem[];
  };
}
