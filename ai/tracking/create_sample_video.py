"""
ai/tracking/create_sample_video.py - Compile Sequential Sewer Frames into Test CCTV Video

Project: AI-Powered Underground Drainage Intelligence and Predictive Maintenance Platform
Purpose: The Roboflow Sewer dataset provides extracted frame sequences. This script compiles
consecutive inspection frames from a known defect sequence (e.g., Video #339) into a realistic
CCTV MP4 video to test defect tracking, deduplication, and quality assessment.
"""

import csv
import sys
from pathlib import Path
import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INDEX_CSV = PROJECT_ROOT / "dataset" / "metadata" / "sample_index.csv"
DATASET_DIR = PROJECT_ROOT / "dataset" / "processed" / "sewer_15class"
OUTPUT_DIR = PROJECT_ROOT / "dataset" / "sample_videos"


def build_sample_video(video_no="356", fps=5, output_name="cctv_inspection_sample.mp4"):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / output_name

    if not INDEX_CSV.exists():
        print(f"Error: {INDEX_CSV} not found.", file=sys.stderr)
        sys.exit(1)

    with open(INDEX_CSV, "r", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["video_no"] == video_no]

    if not rows:
        print(f"No frames found for video #{video_no}", file=sys.stderr)
        sys.exit(1)

    # Sort frames chronologically by original seconds
    rows.sort(key=lambda r: float(r["seconds"]) if r["seconds"] else 0.0)
    print(f"Loaded {len(rows)} sequential frames for Video #{video_no}.")

    # Read first image to obtain resolution
    sample_img_path = DATASET_DIR / rows[0]["split"] / "images" / (rows[0]["new_name"] + ".jpg")
    first_img = cv2.imread(str(sample_img_path))
    if first_img is None:
        print(f"Failed to read image at {sample_img_path}", file=sys.stderr)
        sys.exit(1)

    height, width = first_img.shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(out_path), fourcc, fps, (width, height))

    print(f"Encoding CCTV video: {width}x{height} @ {fps} FPS -> {out_path}...")
    written_frames = 0

    for r in rows:
        img_path = DATASET_DIR / r["split"] / "images" / (r["new_name"] + ".jpg")
        frame = cv2.imread(str(img_path))
        if frame is not None:
            writer.write(frame)
            written_frames += 1

    # Append 3 test frames demonstrating poor inspection conditions
    # Frame 1: Low light / underexposed frame (simulate crawler headlight failure)
    dark_frame = (first_img * 0.15).astype(np.uint8)
    writer.write(dark_frame)
    written_frames += 1

    # Frame 2 & 3: Heavy blur / lens fogging (simulate condensation)
    blurry_frame = cv2.GaussianBlur(first_img, (55, 55), 0)
    writer.write(blurry_frame)
    writer.write(blurry_frame)
    written_frames += 2

    writer.release()
    print("=" * 60)
    print("Sample CCTV video generated successfully!")
    print(f"File Path    : {out_path}")
    print(f"Total Frames : {written_frames} ({len(rows)} clear + 3 degraded test frames)")
    print(f"Duration     : {written_frames / fps:.2f} seconds")
    print(f"Resolution   : {width}x{height}")
    print("=" * 60)
    return out_path


if __name__ == "__main__":
    build_sample_video()
