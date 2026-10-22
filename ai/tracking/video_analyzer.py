"""
ai/tracking/video_analyzer.py - Complete Video Inspection, Defect Tracking & Deduplication Engine

Project: AI-Powered Underground Drainage Intelligence and Predictive Maintenance Platform
Role: Core pipeline for processing underground CCTV inspection videos.
1. Reads CCTV video frame-by-frame.
2. Evaluates optical quality per frame (blur, illumination, fogging).
3. Executes YOLO11 tracking (ByteTrack) to track continuous defect trajectories.
4. Deduplicates detections via DefectDeduplicator to prevent double-counting.
5. Saves an annotated inspection video (.mp4) with live telemetry and bounding boxes.
6. Saves high-res thumbnail crops of each confirmed physical defect.
7. Emits an auditable inspection_summary.json report for municipal repair prioritization.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
import cv2
import numpy as np
import torch
from ultralytics import YOLO

# Project root resolution
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from ai.tracking.deduplicator import DefectDeduplicator, DefectRecord
from ai.tracking.quality import VideoQualityAssessor


def draw_hud_overlay(
    frame: np.ndarray,
    frame_idx: int,
    total_frames: int,
    timestamp_sec: float,
    active_defects_count: int,
    confirmed_defects_count: int,
    quality_info: Dict,
) -> np.ndarray:
    """Render a clean telemetry HUD banner at the top of the video frame."""
    h, w = frame.shape[:2]
    # Header bar
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 55), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    # Status text
    progress_pct = int(100 * frame_idx / max(1, total_frames))
    time_str = f"{int(timestamp_sec // 60):02d}:{timestamp_sec % 60:04.1f}"

    hud_text = (
        f"CCTV AI INSPECTION | Frame: {frame_idx}/{total_frames} ({progress_pct}%) | "
        f"Time: {time_str} | Active in Frame: {active_defects_count} | Total Unique Defects: {confirmed_defects_count}"
    )
    cv2.putText(frame, hud_text, (20, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

    # Quality indicator
    if quality_info["is_poor_quality"]:
        alert_text = f"WARNING: {', '.join(quality_info['issues'])}"
        cv2.putText(frame, alert_text, (20, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
    else:
        qual_text = f"Camera Quality: NORMAL ({int(quality_info['quality_score'] * 100)}%)"
        cv2.putText(frame, qual_text, (20, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 230, 0), 1)

    return frame


def save_defect_thumbnail(
    defect: DefectRecord,
    output_dir: Path,
) -> Optional[str]:
    """Save an annotated thumbnail of the defect at its peak confidence frame."""
    if defect.best_frame_image is None or not defect.best_bbox:
        return None

    img = defect.best_frame_image.copy()
    h, w = img.shape[:2]
    x1, y1, x2, y2 = [int(c) for c in defect.best_bbox]

    # Draw highlight box on thumbnail
    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 140, 255), 3)
    label = f"Defect #{defect.defect_id}: {defect.class_name} ({defect.peak_confidence:.2f})"
    cv2.putText(img, label, (x1, max(25, y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 140, 255), 2)

    # Add margin for crop if feasible, otherwise save full frame
    margin = 50
    crop_x1 = max(0, x1 - margin)
    crop_y1 = max(0, y1 - margin)
    crop_x2 = min(w, x2 + margin)
    crop_y2 = min(h, y2 + margin)

    crop = img[crop_y1:crop_y2, crop_x1:crop_x2]
    filename = f"defect_{defect.defect_id:03d}_{defect.class_name}.jpg"
    thumb_path = output_dir / filename
    cv2.imwrite(str(thumb_path), crop if crop.size > 0 else img)
    return str(thumb_path)


class SewerVideoAnalyzer:
    """Main video processing and defect deduplication pipeline."""

    def __init__(
        self,
        model_weights: str,
        conf_threshold: float = 0.25,
        min_hits: int = 2,
        device: str = "0",
    ):
        self.device = device if torch.cuda.is_available() and device != "cpu" else "cpu"
        print(f"Loading YOLO model '{model_weights}' on {self.device}...")
        self.model = YOLO(model_weights)
        self.conf_threshold = conf_threshold
        self.quality_assessor = VideoQualityAssessor()
        self.deduplicator = DefectDeduplicator(min_hits=min_hits)

    def process_video(
        self,
        video_path: str,
        output_dir: str,
        save_annotated_video: bool = True,
    ) -> Dict:
        """
        Process a video, track defects across frames, and output an audit report.
        """
        vpath = Path(video_path)
        if not vpath.exists():
            raise FileNotFoundError(f"Video file not found at {vpath}")

        out_dir = Path(output_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        thumb_dir = out_dir / "thumbnails"
        thumb_dir.mkdir(parents=True, exist_ok=True)

        cap = cv2.VideoCapture(str(vpath))
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open video: {vpath}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration_sec = total_frames / fps

        print("=" * 65)
        print("  AI Sewer Intelligence - Video Processing Engine")
        print("=" * 65)
        print(f"Input Video      : {vpath.name}")
        print(f"Resolution       : {width}x{height}")
        print(f"Total Frames     : {total_frames} ({fps:.1f} FPS, {duration_sec:.2f}s)")
        print(f"Output Directory : {out_dir}")
        print("=" * 65)

        # Video Writer for annotated output
        writer = None
        annotated_video_path = out_dir / f"annotated_{vpath.stem}.mp4"
        if save_annotated_video:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(str(annotated_video_path), fourcc, fps, (width, height))

        frame_idx = 0
        quality_degraded_frames = 0
        quality_log = []
        start_time = time.time()

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            frame_idx += 1
            timestamp_sec = frame_idx / fps

            # 1. Optical Quality Assessment
            qual = self.quality_assessor.evaluate_frame(frame)
            if qual["is_poor_quality"]:
                quality_degraded_frames += 1
                quality_log.append({
                    "frame": frame_idx,
                    "timestamp_sec": round(timestamp_sec, 2),
                    "issues": qual["issues"],
                    "quality_score": qual["quality_score"],
                })

            # 2. Defect Detection & ByteTrack Tracking
            # Ultralytics track() handles multi-object association across consecutive frames
            track_results = self.model.track(
                frame,
                persist=True,
                conf=self.conf_threshold,
                device=self.device,
                tracker="bytetrack.yaml",
                verbose=False,
            )

            # Parse frame detections
            detections = []
            res = track_results[0]
            if res.boxes is not None and len(res.boxes) > 0:
                boxes = res.boxes
                coords = boxes.xyxy.cpu().numpy()
                confs = boxes.conf.cpu().numpy()
                classes = boxes.cls.cpu().numpy()
                # Ultralytics track assigns track IDs in boxes.id
                track_ids = boxes.id.cpu().numpy().astype(int) if boxes.id is not None else [None] * len(boxes)

                for bbox, conf, cid, tid in zip(coords, confs, classes, track_ids):
                    cname = self.model.names[int(cid)]
                    detections.append({
                        "track_id": int(tid) if tid is not None else None,
                        "class_id": int(cid),
                        "class_name": cname,
                        "conf": float(conf),
                        "bbox": bbox.tolist(),
                    })

            # 3. Defect Deduplication & Lifecycle Association
            active_defect_ids = self.deduplicator.update(
                frame_idx=frame_idx,
                timestamp_sec=timestamp_sec,
                detections=detections,
                frame_image=frame,
                frame_width=width,
                frame_height=height,
            )

            # 4. Render Bounding Boxes & Tracking Telemetry
            if writer is not None:
                display_frame = frame.copy()
                for det, def_id in zip(detections, active_defect_ids):
                    x1, y1, x2, y2 = [int(v) for v in det["bbox"]]
                    color = (0, 165, 255)  # Orange for municipal sewer defects
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
                    label = f"Defect #{def_id}: {det['class_name']} ({det['conf']:.2f})"
                    cv2.putText(
                        display_frame,
                        label,
                        (x1, max(20, y1 - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        color,
                        2,
                    )

                # Overlay Header HUD
                hud_frame = draw_hud_overlay(
                    frame=display_frame,
                    frame_idx=frame_idx,
                    total_frames=total_frames,
                    timestamp_sec=timestamp_sec,
                    active_defects_count=len(detections),
                    confirmed_defects_count=len(self.deduplicator.active_defects) + len(self.deduplicator.completed_defects),
                    quality_info=qual,
                )
                writer.write(hud_frame)

            if frame_idx % 10 == 0 or frame_idx == total_frames:
                pct = int(100 * frame_idx / total_frames)
                print(f"Processing: frame {frame_idx}/{total_frames} ({pct}%) | Active Defects: {len(detections)}")

        cap.release()
        if writer is not None:
            writer.release()

        # 5. Finalize Deduplication & Export Thumbnails
        confirmed_defects = self.deduplicator.finalize()
        for defect in confirmed_defects:
            thumb_path = save_defect_thumbnail(defect, thumb_dir)
            defect.thumbnail_path = thumb_path

        elapsed_time = time.time() - start_time
        fps_actual = total_frames / max(0.001, elapsed_time)

        # 6. Aggregate Inspection Summary
        class_summary = {}
        for d in confirmed_defects:
            class_summary[d.class_name] = class_summary.get(d.class_name, 0) + 1

        pct_degraded = round(100 * quality_degraded_frames / max(1, total_frames), 1)

        summary_report = {
            "video_metadata": {
                "filename": vpath.name,
                "resolution": f"{width}x{height}",
                "total_frames": total_frames,
                "fps": round(fps, 2),
                "duration_seconds": round(duration_sec, 2),
                "processing_time_sec": round(elapsed_time, 2),
                "throughput_fps": round(fps_actual, 1),
            },
            "quality_assessment": {
                "total_frames": total_frames,
                "degraded_frames_count": quality_degraded_frames,
                "degraded_percentage": pct_degraded,
                "overall_status": "POOR_QUALITY_FLAGGED" if pct_degraded >= 15.0 else "ACCEPTABLE",
                "quality_flags_log": quality_log[:20],  # first 20 warnings
            },
            "deduplication_summary": {
                "total_unique_physical_defects": len(confirmed_defects),
                "defect_counts_by_class": class_summary,
            },
            "unique_defects": [d.to_dict() for d in confirmed_defects],
        }

        report_path = out_dir / "inspection_summary.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(summary_report, f, indent=2)

        print("\n" + "=" * 65)
        print("  Video Inspection Completed!")
        print("=" * 65)
        print(f"Processed Frames       : {total_frames} in {elapsed_time:.2f}s ({fps_actual:.1f} FPS)")
        print(f"Degraded Frames        : {quality_degraded_frames}/{total_frames} ({pct_degraded}%)")
        print(f"Total Unique Defects   : {len(confirmed_defects)} (Deduplicated)")
        print(f"Defect Breakdown       : {class_summary}")
        if save_annotated_video:
            print(f"Annotated Video Saved  : {annotated_video_path}")
        print(f"Inspection Report JSON : {report_path}")
        print(f"Defect Thumbnails Dir  : {thumb_dir}")
        print("=" * 65)

        return summary_report


def main():
    parser = argparse.ArgumentParser(description="Analyze CCTV sewer video with defect tracking & deduplication.")
    parser.add_argument(
        "--video",
        type=str,
        default=str(PROJECT_ROOT / "dataset" / "sample_videos" / "cctv_inspection_sample.mp4"),
        help="Path to input sewer inspection video file.",
    )
    parser.add_argument(
        "--weights",
        type=str,
        default=str(PROJECT_ROOT / "mlops" / "experiments" / "yolo11s_15cls_test" / "weights" / "best.pt"),
        help="Path to YOLO11 model weights (.pt).",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.25,
        help="Detection confidence threshold.",
    )
    parser.add_argument(
        "--min-hits",
        type=int,
        default=2,
        help="Minimum frame detections required to confirm a real physical defect.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(PROJECT_ROOT / "mlops" / "experiments" / "tracking_output"),
        help="Directory to save output video, thumbnails, and JSON report.",
    )
    args = parser.parse_args()

    analyzer = SewerVideoAnalyzer(
        model_weights=args.weights,
        conf_threshold=args.conf,
        min_hits=args.min_hits,
    )
    analyzer.process_video(
        video_path=args.video,
        output_dir=args.output,
    )


if __name__ == "__main__":
    main()
