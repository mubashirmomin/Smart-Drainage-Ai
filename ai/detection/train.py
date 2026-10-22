"""
ai/detection/train.py - YOLO11 Training Pipeline for Underground Drainage Defect Detection

Project: AI-Powered Underground Drainage Intelligence and Predictive Maintenance Platform
Target Environment: Windows 11, NVIDIA RTX 3060 Laptop (6GB VRAM), PyTorch + CUDA

Key Features:
- Supports both quick smoke-tests and full production runs via CLI arguments.
- Robust path handling relative to project root.
- Windows-safe multiprocessing guard (if __name__ == '__main__').
- Configurable device, image size, batch size, epochs, and dataset fraction.
"""

import argparse
import sys
from pathlib import Path
import torch
from ultralytics import YOLO

# Resolve project root: .../smart-drainage-ai/
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Train YOLO11 on sewer defect dataset."
    )
    parser.add_argument(
        "--data",
        type=str,
        default=str(PROJECT_ROOT / "dataset" / "processed" / "sewer_15class" / "data.yaml"),
        help="Path to YOLO data.yaml configuration file.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="yolo11s.pt",
        help="Base model checkpoint (e.g., yolo11s.pt, yolo11n.pt).",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=1,
        help="Number of training epochs (default 1 for smoke test).",
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=8,
        help="Batch size (default 8, optimal for 6GB VRAM at 640x640).",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Image size in pixels (default 640).",
    )
    parser.add_argument(
        "--fraction",
        type=float,
        default=1.0,
        help="Fraction of dataset to use (default 1.0 for full dataset, e.g. 0.05 for smoke test).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=2,
        help="DataLoader worker count (default 2 for Windows multiprocessing stability).",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="0" if torch.cuda.is_available() else "cpu",
        help="Device to run on (e.g. '0' for GPU or 'cpu').",
    )
    parser.add_argument(
        "--project",
        type=str,
        default=str(PROJECT_ROOT / "mlops" / "experiments"),
        help="Directory to save experiment runs.",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="smoke",
        help="Experiment run name.",
    )
    parser.add_argument(
        "--exist-ok",
        action="store_true",
        default=True,
        help="Overwrite existing experiment folder of the same name instead of incrementing.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Pre-flight environment summary
    print("=" * 60)
    print("  AI Sewer Intelligence - Training Pipeline")
    print("=" * 60)
    print(f"Project Root     : {PROJECT_ROOT}")
    print(f"Data YAML        : {args.data}")
    print(f"Base Model       : {args.model}")
    print(f"Device           : {args.device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() and args.device != 'cpu' else 'CPU'})")
    if torch.cuda.is_available():
        free_mem, total_mem = torch.cuda.mem_get_info()
        print(f"GPU Free Memory  : {free_mem / (1024**3):.2f} GB / {total_mem / (1024**3):.2f} GB")
    print(f"Epochs           : {args.epochs}")
    print(f"Batch Size       : {args.batch}")
    print(f"Image Size       : {args.imgsz}")
    print(f"Dataset Fraction : {args.fraction * 100:.1f}%")
    print(f"Workers          : {args.workers}")
    print(f"Output Path      : {Path(args.project) / args.name}")
    print("=" * 60)

    # Validate data yaml exists
    data_path = Path(args.data)
    if not data_path.exists():
        print(f"Error: Dataset configuration file not found at: {data_path}", file=sys.stderr)
        sys.exit(1)

    # Initialize YOLO model
    print(f"\n[1/2] Loading model weights '{args.model}'...")
    model = YOLO(args.model)

    # Ensure absolute path so Ultralytics saves directly to mlops/experiments/
    project_path = Path(args.project).resolve()

    # Start training
    print(f"[2/2] Launching training run...")
    results = model.train(
        data=str(data_path),
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        fraction=args.fraction,
        workers=args.workers,
        device=args.device,
        project=str(project_path),
        name=args.name,
        exist_ok=args.exist_ok,
        plots=True,
        save=True,
        verbose=True,
    )

    print("\n" + "=" * 60)
    print("Training job finished successfully!")
    print(f"Artifacts and weights saved to: {Path(args.project) / args.name}")
    print("=" * 60)
    return results


if __name__ == "__main__":
    main()
