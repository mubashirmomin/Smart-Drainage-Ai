"""
ai/tracking/deduplicator.py - Defect Deduplication & Lifecycle Tracker for Sewer CCTV Footage

Project: AI-Powered Underground Drainage Intelligence and Predictive Maintenance Platform
Purpose: Solves the double-counting problem in sewer inspection videos. A CCTV crawler camera
moves slowly, causing the same physical defect (e.g., crack, sediment bed) to appear across
dozens of consecutive frames. This module:
1. Tracks defects across frames using tracker IDs and spatial IoU association.
2. Filters out single-frame false alarms and optical flickering noise (min_hits threshold).
3. Maintains a persistent lifecycle registry for each unique physical defect.
4. Captures the defect's peak confidence, maximum surface area ratio, and best inspection thumbnail.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
import numpy as np


def compute_iou(boxA, boxB) -> float:
    """Compute Intersection over Union (IoU) of two boxes [x1, y1, x2, y2]."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0.0, xB - xA) * max(0.0, yB - yA)
    boxAArea = max(0.0, boxA[2] - boxA[0]) * max(0.0, boxA[3] - boxA[1])
    boxBArea = max(0.0, boxB[2] - boxB[0]) * max(0.0, boxB[3] - boxB[1])
    unionArea = boxAArea + boxBArea - interArea

    return interArea / unionArea if unionArea > 0 else 0.0


@dataclass
class DefectRecord:
    defect_id: int
    tracker_ids: Set[int]
    class_id: int
    class_name: str
    class_votes: Dict[str, int] = field(default_factory=dict)
    first_frame: int = 0
    last_frame: int = 0
    first_time_sec: float = 0.0
    last_time_sec: float = 0.0
    hits: int = 0
    peak_confidence: float = 0.0
    max_area_ratio: float = 0.0
    best_bbox: List[float] = field(default_factory=list)
    best_frame_idx: int = 0
    best_frame_image: Optional[np.ndarray] = None
    thumbnail_path: Optional[str] = None
    last_bbox: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Export serializable dictionary representation for JSON/DB storage."""
        duration_sec = round(self.last_time_sec - self.first_time_sec, 2)
        return {
            "defect_id": self.defect_id,
            "class_name": self.class_name,
            "class_id": self.class_id,
            "hits": self.hits,
            "first_frame": self.first_frame,
            "last_frame": self.last_frame,
            "first_time_sec": round(self.first_time_sec, 2),
            "last_time_sec": round(self.last_time_sec, 2),
            "duration_sec": max(0.1, duration_sec),
            "peak_confidence": round(self.peak_confidence, 2),
            "max_area_ratio": round(self.max_area_ratio, 4),
            "best_frame_idx": self.best_frame_idx,
            "best_bbox": [round(c, 1) for c in self.best_bbox],
            "thumbnail_path": self.thumbnail_path,
        }


class DefectDeduplicator:
    """
    Associates continuous defect detections into deduplicated physical defect entities.
    """

    def __init__(self, min_hits: int = 2, max_gap_frames: int = 8, spatial_iou_thresh: float = 0.25):
        """
        Args:
            min_hits: Minimum number of frame detections to confirm a real defect (filters transient noise).
            max_gap_frames: Maximum frame gap to re-link a temporarily occluded defect.
            spatial_iou_thresh: IoU overlap required to re-link lost tracklets.
        """
        self.min_hits = min_hits
        self.max_gap_frames = max_gap_frames
        self.spatial_iou_thresh = spatial_iou_thresh
        self.next_defect_id = 1

        self.active_defects: List[DefectRecord] = []
        self.completed_defects: List[DefectRecord] = []
        self.tracker_to_defect: Dict[int, DefectRecord] = {}

    def update(
        self,
        frame_idx: int,
        timestamp_sec: float,
        detections: List[Dict],
        frame_image: Optional[np.ndarray] = None,
        frame_width: int = 1920,
        frame_height: int = 1080,
    ) -> List[int]:
        """
        Update the deduplicator with detections from the current frame.

        Args:
            detections: List of dicts, each with keys:
                        'track_id' (int), 'class_id' (int), 'class_name' (str),
                        'conf' (float), 'bbox' ([x1, y1, x2, y2])
        Returns:
            List of active defect IDs visible in this frame.
        """
        frame_area = max(1.0, float(frame_width * frame_height))
        current_visible_defect_ids = []
        unmatched_detections = []

        # 1. Match by tracker ID
        for det in detections:
            tid = det.get("track_id")
            bbox = det["bbox"]
            conf = det["conf"]
            cname = det["class_name"]
            cid = det["class_id"]
            box_area = max(0.0, bbox[2] - bbox[0]) * max(0.0, bbox[3] - bbox[1])
            area_ratio = box_area / frame_area

            matched_defect = None
            if tid is not None and tid in self.tracker_to_defect:
                matched_defect = self.tracker_to_defect[tid]

            if matched_defect is not None:
                self._update_record(matched_defect, tid, cid, cname, conf, bbox, area_ratio, frame_idx, timestamp_sec, frame_image)
                current_visible_defect_ids.append(matched_defect.defect_id)
            else:
                unmatched_detections.append(det)

        # 2. Match remaining unmatched detections via Spatial IoU & Class compatibility
        for det in unmatched_detections:
            tid = det.get("track_id")
            bbox = det["bbox"]
            conf = det["conf"]
            cname = det["class_name"]
            cid = det["class_id"]
            box_area = max(0.0, bbox[2] - bbox[0]) * max(0.0, bbox[3] - bbox[1])
            area_ratio = box_area / frame_area

            best_iou = 0.0
            best_defect = None

            for defect in self.active_defects:
                if defect.class_name == cname and (frame_idx - defect.last_frame) <= self.max_gap_frames:
                    iou = compute_iou(bbox, defect.last_bbox)
                    if iou > self.spatial_iou_thresh and iou > best_iou:
                        best_iou = iou
                        best_defect = defect

            if best_defect is not None:
                self._update_record(best_defect, tid, cid, cname, conf, bbox, area_ratio, frame_idx, timestamp_sec, frame_image)
                current_visible_defect_ids.append(best_defect.defect_id)
            else:
                # 3. Initialize a new defect candidate
                new_defect = DefectRecord(
                    defect_id=self.next_defect_id,
                    tracker_ids={tid} if tid is not None else set(),
                    class_id=cid,
                    class_name=cname,
                    class_votes={cname: 1},
                    first_frame=frame_idx,
                    last_frame=frame_idx,
                    first_time_sec=timestamp_sec,
                    last_time_sec=timestamp_sec,
                    hits=1,
                    peak_confidence=conf,
                    max_area_ratio=area_ratio,
                    best_bbox=bbox,
                    best_frame_idx=frame_idx,
                    best_frame_image=frame_image.copy() if frame_image is not None else None,
                    last_bbox=bbox,
                )
                self.next_defect_id += 1
                self.active_defects.append(new_defect)
                if tid is not None:
                    self.tracker_to_defect[tid] = new_defect
                current_visible_defect_ids.append(new_defect.defect_id)

        # 4. Retire stale active defects that haven't been seen for max_gap_frames
        still_active = []
        for defect in self.active_defects:
            if (frame_idx - defect.last_frame) > self.max_gap_frames:
                self.completed_defects.append(defect)
            else:
                still_active.append(defect)
        self.active_defects = still_active

        return current_visible_defect_ids

    def _update_record(self, defect: DefectRecord, tid, cid, cname, conf, bbox, area_ratio, frame_idx, timestamp_sec, frame_image):
        """Update defect running metrics."""
        defect.hits += 1
        defect.last_frame = frame_idx
        defect.last_time_sec = timestamp_sec
        defect.last_bbox = bbox
        if tid is not None:
            defect.tracker_ids.add(tid)
            self.tracker_to_defect[tid] = defect

        defect.class_votes[cname] = defect.class_votes.get(cname, 0) + 1
        # Resolve class by majority vote
        defect.class_name = max(defect.class_votes, key=defect.class_votes.get)

        # Keep highest confidence frame
        if conf > defect.peak_confidence:
            defect.peak_confidence = conf
            defect.best_bbox = bbox
            defect.best_frame_idx = frame_idx
            if frame_image is not None:
                defect.best_frame_image = frame_image.copy()

        if area_ratio > defect.max_area_ratio:
            defect.max_area_ratio = area_ratio

    def finalize(self) -> List[DefectRecord]:
        """Retire all remaining active defects and return the list of confirmed defects."""
        self.completed_defects.extend(self.active_defects)
        self.active_defects = []
        # Filter by min_hits to eliminate 1-frame spurious detections
        confirmed = [d for d in self.completed_defects if d.hits >= self.min_hits]
        return sorted(confirmed, key=lambda d: d.first_frame)
