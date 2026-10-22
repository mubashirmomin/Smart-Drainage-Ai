"""
backend/app/core/config.py - Application Configuration & Reference Municipal Network

Project: AI-Powered Underground Drainage Intelligence and Predictive Maintenance Platform
Environment: Windows OS, FastAPI, PyTorch + CUDA, React Frontend
"""

from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings:
    PROJECT_NAME: str = "AI Sewer & Drainage Intelligence Platform"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    PROJECT_ROOT: Path = PROJECT_ROOT

    # CORS configuration for Vite / React development server
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ]

    # File storage paths
    BACKEND_DIR: Path = PROJECT_ROOT / "backend"
    UPLOAD_DIR: Path = BACKEND_DIR / "uploads"
    STORAGE_DIR: Path = BACKEND_DIR / "storage" / "inspections"
    SAMPLE_VIDEOS_DIR: Path = PROJECT_ROOT / "dataset" / "sample_videos"

    # AI Model weights path (prefers 15-class trained model, falls back to smoke weights)
    MODEL_WEIGHTS_15CLS: Path = PROJECT_ROOT / "mlops" / "experiments" / "yolo11s_15cls_test" / "weights" / "best.pt"
    MODEL_WEIGHTS_SMOKE: Path = PROJECT_ROOT / "mlops" / "experiments" / "smoke" / "weights" / "best.pt"

    @property
    def model_weights_path(self) -> Path:
        if self.MODEL_WEIGHTS_15CLS.exists():
            return self.MODEL_WEIGHTS_15CLS
        elif self.MODEL_WEIGHTS_SMOKE.exists():
            return self.MODEL_WEIGHTS_SMOKE
        else:
            return PROJECT_ROOT / "yolo11s.pt"

    # Reference Municipal Drainage Asset Network (Mumbai Urban Drainage Context)
    MUMBAI_PIPE_NETWORK: List[Dict] = [
        {
            "pipe_id": "PIPE-MUM-001",
            "street_name": "Dr. B.A. Road (Hindmata Junction)",
            "ward": "Ward F/South (Parel)",
            "material": "Reinforced Concrete (RCC)",
            "diameter_mm": 1200,
            "length_meters": 145.0,
            "installation_year": 1998,
            "start_manhole": "MH-F-101",
            "end_manhole": "MH-F-102",
            "start_coords": [19.0125, 72.8428],
            "end_coords": [19.0138, 72.8435],
            "criticality": "HIGH_SURCHARGE_RISK",
        },
        {
            "pipe_id": "PIPE-MUM-002",
            "street_name": "SV Road (Andheri Subway Underpass)",
            "ward": "Ward K/West (Andheri)",
            "material": "Spun Concrete",
            "diameter_mm": 900,
            "length_meters": 110.0,
            "installation_year": 2005,
            "start_manhole": "MH-KW-201",
            "end_manhole": "MH-KW-202",
            "start_coords": [19.1198, 72.8465],
            "end_coords": [19.1207, 72.8472],
            "criticality": "CHRONIC_FLOOD_PRONE",
        },
        {
            "pipe_id": "PIPE-MUM-003",
            "street_name": "LBS Marg (Kurla Depot to Station)",
            "ward": "Ward L (Kurla West)",
            "material": "Brick Masonry Arch / RCC",
            "diameter_mm": 1000,
            "length_meters": 180.0,
            "installation_year": 1985,
            "start_manhole": "MH-L-301",
            "end_manhole": "MH-L-302",
            "start_coords": [19.0682, 72.8821],
            "end_coords": [19.0695, 72.8834],
            "criticality": "HEAVY_SILT_ACCUMULATION",
        },
        {
            "pipe_id": "PIPE-MUM-004",
            "street_name": "BKC Avenue 1 (Near G-Block)",
            "ward": "Ward H/East (Bandra East)",
            "material": "High-Density Polyethylene (HDPE)",
            "diameter_mm": 600,
            "length_meters": 95.0,
            "installation_year": 2018,
            "start_manhole": "MH-HE-401",
            "end_manhole": "MH-HE-402",
            "start_coords": [19.0655, 72.8685],
            "end_coords": [19.0663, 72.8692],
            "criticality": "MODERATE_FLOW",
        },
        {
            "pipe_id": "PIPE-MUM-005",
            "street_name": "Dadar TT Circle (Pritam Hotel Invert)",
            "ward": "Ward F/North (Dadar East)",
            "material": "Reinforced Concrete (RCC)",
            "diameter_mm": 900,
            "length_meters": 125.0,
            "installation_year": 2001,
            "start_manhole": "MH-FN-501",
            "end_manhole": "MH-FN-502",
            "start_coords": [19.0178, 72.8478],
            "end_coords": [19.0189, 72.8486],
            "criticality": "COMMERCIAL_GREASE_RISK",
        },
    ]


settings = Settings()
