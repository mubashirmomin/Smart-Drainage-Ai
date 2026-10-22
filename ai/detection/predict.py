"""
ai/detection/predict.py - Inference & Defect Visualizer for Sewer CCTV Footage

Project: AI-Powered Underground Drainage Intelligence and Predictive Maintenance Platform
Role: Run YOLO11 inference on inspection images or video clips, output bounding boxes,
defect classes, confidence scores, and save visual artifacts.
"""

import argparse
import sys
from pathlib import Path
from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def parse_args():
    parser = argparse.ArgumentParser(description="Run YOLO11 defect detection on images or videos.")
    parser.add_argument(
        "--weights",
        type=str,
        default=str(PROJECT_ROOT / "mlops" / "experiments" / "smoke" / "weights" / "best.pt"),
        help="Path to trained YOLO weights file (.pt).",
    )
    parser.add_argument(
        "--source",
        type=str,
        default=str(PROJECT_ROOT / "dataset" / "processed" / "sewer_15class" / "test" / "images"),
        help="Path to image, video, or folder of images.",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.25,
        help="Confidence threshold (default 0.25).",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Inference image resolution (default 640).",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="0",
        help="Device to run on (e.g., '0' for GPU or 'cpu').",
    )
    parser.add_argument(
        "--project",
        type=str,
        default=str(PROJECT_ROOT / "mlops" / "experiments"),
        help="Directory to save predictions.",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="predictions",
        help="Prediction run folder name.",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=10,
        help="Maximum images to infer if source is a folder (default 10 for quick review).",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    weights_path = Path(args.weights)
    if not weights_path.exists():
        print(f"Error: Model weights not found at: {weights_path}", file=sys.stderr)
        sys.exit(1)

    source_path = Path(args.source)
    if not source_path.exists():
        print(f"Error: Source path not found at: {source_path}", file=sys.stderr)
        sys.exit(1)

    # Determine files to process
    if source_path.is_dir():
        image_suffixes = {".jpg", ".jpeg", ".png"}
        candidates = sorted([p for p in source_path.iterdir() if p.suffix.lower() in image_suffixes])
        if not candidates:
            print(f"No image files found in {source_path}", file=sys.stderr)
            sys.exit(1)
        samples = candidates[:args.max_samples]
        print(f"Processing {len(samples)} sample images from {source_path}...")
        targets = [str(p) for p in samples]
    else:
        targets = [str(source_path)]

    print("=" * 60)
    print("  AI Sewer Intelligence - Defect Prediction Pipeline")
    print("=" * 60)
    print(f"Model Weights : {weights_path}")
    print(f"Source        : {source_path}")
    print(f"Confidence Thresh: {args.conf}")
    print(f"Output Dir    : {Path(args.project) / args.name}")
    print("=" * 60)

    model = YOLO(str(weights_path))
    results = model.predict(
        source=targets,
        conf=args.conf,
        imgsz=args.imgsz,
        device=args.device,
        project=str(Path(args.project).resolve()),
        name=args.name,
        save=True,
        save_txt=True,
        save_conf=True,
        exist_ok=True,
        verbose=True,
    )

    print("\n" + "=" * 60)
    print("Detections Summary:")
    print("=" * 60)
    total_detections = 0
    for res in results:
        boxes = res.boxes
        num_boxes = len(boxes) if boxes is not None else 0
        total_detections += num_boxes
        img_name = Path(res.path).name
        if num_boxes > 0:
            classes_detected = [model.names[int(cls_id)] for cls_id in boxes.cls.cpu().numpy()]
            confidences = [f"{float(conf):.2f}" for conf in boxes.conf.cpu().numpy()]
            print(f"[{img_name}] {num_boxes} defect(s):")
            for cname, conf in zip(classes_detected, confidences):
                print(f"   -> {cname} (conf: {conf})")
        else:
            print(f"[{img_name}] Clean pipe (no defect detected above conf {args.conf})")

    print("-" * 60)
    print(f"Total Defects Detected: {total_detections}")
    print(f"Annotated Visuals Saved to: {Path(args.project) / args.name}")
    print("=" * 60)


if __name__ == "__main__":
    main()
