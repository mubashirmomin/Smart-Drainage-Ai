"""
backend/app/services/inspection_service.py - Core Inspection Execution & Management Service

Project: AI-Powered Underground Drainage Intelligence and Predictive Maintenance Platform
Role: Asynchronously manages video processing, defect tracking, condition assessment,
and storage of municipal inspection records.
"""

import json
import shutil
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import uuid

from backend.app.core.config import settings
from backend.app.schemas.inspection import (
    DefectItemSchema,
    InspectionDetailSchema,
    InspectionStatusEnum,
    InspectionSummarySchema,
    PipeAssetSchema,
)

# AI Pipeline Imports
from ai.assessment.evaluate_inspection import evaluate_inspection_file
from ai.tracking.video_analyzer import SewerVideoAnalyzer


class InspectionService:
    """Singleton service orchestrating inspection pipelines and asset registry."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(InspectionService, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.inspections: Dict[str, Dict] = {}
        self.pipes: Dict[str, Dict] = {p["pipe_id"]: p.copy() for p in settings.MUMBAI_PIPE_NETWORK}
        self.registry_file = settings.STORAGE_DIR / "inspections_registry.json"
        self._load_registry()
        self._seed_demo_inspection()
        self._initialized = True

    def _load_registry(self):
        """Load stored inspections from disk if present."""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    self.inspections = json.load(f)
                # Recover or fail any interrupted jobs from previous server shutdown
                changed = False
                for insp_id, data in self.inspections.items():
                    if data.get("status") in ("PROCESSING", "PENDING"):
                        video_file = settings.STORAGE_DIR / insp_id / "annotated_video.mp4"
                        report_file = settings.STORAGE_DIR / insp_id / "condition_assessment.json"
                        if video_file.exists() and report_file.exists():
                            data["status"] = "COMPLETED"
                        else:
                            data["status"] = "FAILED"
                            data["error_message"] = "Analysis interrupted by previous backend shutdown. Please re-run."
                        changed = True
                if changed:
                    self._save_registry()
            except Exception as e:
                print(f"Warning: Could not read registry file: {e}")
                self.inspections = {}

    def _save_registry(self):
        """Persist inspections metadata to disk."""
        try:
            settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
            with open(self.registry_file, "w", encoding="utf-8") as f:
                json.dump(self.inspections, f, indent=2)
        except Exception as e:
            print(f"Error saving registry: {e}")

    def _seed_demo_inspection(self):
        """Seed the verified Phase 4 & 5 inspection run if not present."""
        demo_id = "INSP-MUM-DEMO-001"
        if demo_id in self.inspections:
            return

        source_report = settings.PROJECT_ROOT / "mlops" / "experiments" / "tracking_output" / "condition_assessment.json"
        if not source_report.exists():
            return

        dest_dir = settings.STORAGE_DIR / demo_id
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Copy report, video, and thumbnails to storage
        shutil.copy(source_report, dest_dir / "condition_assessment.json")

        src_video = settings.PROJECT_ROOT / "mlops" / "experiments" / "tracking_output" / "annotated_cctv_inspection_sample.mp4"
        if src_video.exists():
            shutil.copy(src_video, dest_dir / "annotated_video.mp4")

        src_thumb = settings.PROJECT_ROOT / "mlops" / "experiments" / "tracking_output" / "thumbnails"
        if src_thumb.exists():
            dest_thumb = dest_dir / "thumbnails"
            if dest_thumb.exists():
                shutil.rmtree(dest_thumb)
            shutil.copytree(src_thumb, dest_thumb)

        with open(source_report, "r", encoding="utf-8") as f:
            dossier = json.load(f)

        self.inspections[demo_id] = {
            "inspection_id": demo_id,
            "pipe_id": "PIPE-MUM-001",
            "status": "COMPLETED",
            "created_at": "2026-10-22T00:45:00Z",
            "completed_at": "2026-10-22T00:48:00Z",
            "video_filename": "cctv_inspection_sample.mp4",
            "dossier": dossier,
        }
        self._update_pipe_status("PIPE-MUM-001", dossier)
        self._save_registry()

    def _update_pipe_status(self, pipe_id: str, dossier: Dict):
        """Update pipe asset latest condition from inspection dossier."""
        if pipe_id in self.pipes:
            pci = dossier["pipe_health_indices"]["pci_overall_score"]
            cond = dossier["pipe_health_indices"]["condition_state"]
            prio = dossier["maintenance_dispatch_prioritization"]["work_order_priority"]
            self.pipes[pipe_id]["latest_pci"] = pci
            self.pipes[pipe_id]["latest_condition_state"] = cond
            self.pipes[pipe_id]["latest_priority"] = prio

    def list_pipes(self) -> List[PipeAssetSchema]:
        """Return list of monitored pipe segments."""
        return [PipeAssetSchema(**p) for p in self.pipes.values()]

    def get_pipe(self, pipe_id: str) -> Optional[PipeAssetSchema]:
        """Get details for a single pipe asset."""
        p = self.pipes.get(pipe_id)
        return PipeAssetSchema(**p) if p else None

    def list_inspections(self) -> List[InspectionSummarySchema]:
        """Return summary list of all inspections."""
        summaries = []
        for insp_id, data in sorted(self.inspections.items(), key=lambda x: x[1].get("created_at", ""), reverse=True):
            pipe_id = data.get("pipe_id", "UNKNOWN")
            pipe = self.pipes.get(pipe_id, {})
            dossier = data.get("dossier", {})

            pci = None
            cond = None
            prio = None
            block = None
            total_defects = 0

            if dossier:
                pci = dossier.get("pipe_health_indices", {}).get("pci_overall_score")
                cond = dossier.get("pipe_health_indices", {}).get("condition_state")
                prio = dossier.get("maintenance_dispatch_prioritization", {}).get("work_order_priority")
                block = dossier.get("hydraulic_conveyance_assessment", {}).get("blockage_percentage")
                total_defects = len(dossier.get("detailed_defect_inventory", []))

            summaries.append(
                InspectionSummarySchema(
                    inspection_id=insp_id,
                    pipe_id=pipe_id,
                    street_name=pipe.get("street_name", "Municipal Drain Line"),
                    ward=pipe.get("ward", "General"),
                    status=InspectionStatusEnum(data.get("status", "PENDING")),
                    created_at=data.get("created_at", ""),
                    video_filename=data.get("video_filename", ""),
                    pci_score=pci,
                    condition_state=cond,
                    priority=prio,
                    total_defects=total_defects,
                    blockage_percentage=block,
                    annotated_video_url=f"/api/v1/inspections/{insp_id}/video" if data.get("status") == "COMPLETED" else None,
                )
            )
        return summaries

    def get_inspection_detail(self, inspection_id: str) -> Optional[InspectionDetailSchema]:
        """Return full detail dossier for an inspection."""
        data = self.inspections.get(inspection_id)
        if not data:
            return None

        dossier = data.get("dossier")
        detail = InspectionDetailSchema(
            inspection_id=inspection_id,
            pipe_id=data.get("pipe_id", ""),
            status=InspectionStatusEnum(data.get("status", "PENDING")),
            created_at=data.get("created_at", ""),
            completed_at=data.get("completed_at"),
            error_message=data.get("error_message"),
            annotated_video_url=f"/api/v1/inspections/{inspection_id}/video" if data.get("status") == "COMPLETED" else None,
        )

        if dossier:
            if "asset_inspection_meta" in dossier:
                from backend.app.schemas.inspection import (
                    AssetInspectionMetaSchema,
                    PipeHealthIndicesSchema,
                    HydraulicAssessmentSchema,
                    MaintenanceDispatchSchema,
                )
                detail.asset_inspection_meta = AssetInspectionMetaSchema(**dossier["asset_inspection_meta"])
            if "pipe_health_indices" in dossier:
                detail.pipe_health_indices = PipeHealthIndicesSchema(**dossier["pipe_health_indices"])
            if "hydraulic_conveyance_assessment" in dossier:
                detail.hydraulic_conveyance_assessment = HydraulicAssessmentSchema(**dossier["hydraulic_conveyance_assessment"])
            if "maintenance_dispatch_prioritization" in dossier:
                detail.maintenance_dispatch_prioritization = MaintenanceDispatchSchema(**dossier["maintenance_dispatch_prioritization"])

            # Attach thumbnail URLs
            defects = []
            for d in dossier.get("detailed_defect_inventory", []):
                d_copy = d.copy()
                if d_copy.get("thumbnail_path"):
                    filename = Path(d_copy["thumbnail_path"]).name
                    d_copy["thumbnail_url"] = f"/api/v1/inspections/{inspection_id}/thumbnails/{filename}"
                defects.append(DefectItemSchema(**d_copy))
            detail.detailed_defect_inventory = defects

        return detail

    def create_inspection(self, pipe_id: str, video_file_path: Path, video_filename: str) -> str:
        """Initialize inspection record and return inspection_id."""
        now_str = datetime.now(timezone.utc).isoformat()
        insp_id = f"INSP-{int(time.time())}-{uuid.uuid4().hex[:6].upper()}"

        self.inspections[insp_id] = {
            "inspection_id": insp_id,
            "pipe_id": pipe_id,
            "status": "PENDING",
            "created_at": now_str,
            "video_filename": video_filename,
            "video_path": str(video_file_path),
        }
        self._save_registry()
        return insp_id

    def execute_inspection_task(self, inspection_id: str):
        """Asynchronous worker that runs AI tracking and condition assessment."""
        record = self.inspections.get(inspection_id)
        if not record:
            return

        record["status"] = "PROCESSING"
        self._save_registry()

        video_path = Path(record["video_path"])
        out_dir = settings.STORAGE_DIR / inspection_id
        out_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 1. Run Video Analysis & Tracking
            analyzer = SewerVideoAnalyzer(
                model_weights=str(settings.model_weights_path),
                conf_threshold=0.25,
                min_hits=2,
            )
            analyzer.process_video(
                video_path=str(video_path),
                output_dir=str(out_dir),
                save_annotated_video=True,
            )

            # Standardize output video name
            target_video = out_dir / "annotated_video.mp4"
            if not target_video.exists():
                for p in out_dir.glob("annotated_*.mp4"):
                    shutil.move(str(p), str(target_video))
                    break

            # 2. Run Condition Assessment
            summary_json = out_dir / "inspection_summary.json"
            dossier_json = out_dir / "condition_assessment.json"
            dossier = evaluate_inspection_file(
                inspection_json_path=str(summary_json),
                output_path=str(dossier_json),
            )

            # 3. Update Record
            record["status"] = "COMPLETED"
            record["completed_at"] = datetime.now(timezone.utc).isoformat()
            record["dossier"] = dossier
            self._update_pipe_status(record["pipe_id"], dossier)

        except Exception as e:
            print(f"Error processing inspection {inspection_id}: {e}")
            record["status"] = "FAILED"
            record["error_message"] = str(e)
            record["completed_at"] = datetime.now(timezone.utc).isoformat()

        finally:
            self._save_registry()


inspection_service = InspectionService()
