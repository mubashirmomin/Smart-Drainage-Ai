"""
tests/test_assessment.py - Verification Suite for Tracking, Deduplication & Condition Assessment

Project: AI-Powered Underground Drainage Intelligence and Predictive Maintenance Platform
Uses standard library unittest.
"""

import unittest
import numpy as np
from ai.tracking.quality import VideoQualityAssessor
from ai.tracking.deduplicator import DefectDeduplicator
from ai.assessment.severity import DefectSeverityAssessor
from ai.assessment.blockage import HydraulicBlockageAssessor
from ai.assessment.condition_index import PipeConditionEvaluator


class TestQualityAssessor(unittest.TestCase):
    def setUp(self):
        self.assessor = VideoQualityAssessor()

    def test_clear_frame(self):
        # Balanced checkerboard frame with good illumination and sharp edges
        clear = np.zeros((200, 200, 3), dtype=np.uint8)
        for y in range(0, 200, 20):
            for x in range(0, 200, 20):
                if (x // 20 + y // 20) % 2 == 0:
                    clear[y:y+20, x:x+20] = 180
                else:
                    clear[y:y+20, x:x+20] = 70
        res = self.assessor.evaluate_frame(clear)
        self.assertFalse(res["is_poor_quality"])
        self.assertGreaterEqual(res["quality_score"], 0.4)

    def test_dark_frame_flagged(self):
        # Low light / underexposed
        dark = np.ones((200, 200, 3), dtype=np.uint8) * 10
        res = self.assessor.evaluate_frame(dark)
        self.assertTrue(res["is_poor_quality"])
        self.assertTrue(any("UNDEREXPOSED" in issue for issue in res["issues"]))

    def test_blurry_frame_flagged(self):
        # Uniform gray image (zero Laplacian edge variance)
        blur = np.ones((200, 200, 3), dtype=np.uint8) * 128
        res = self.assessor.evaluate_frame(blur)
        self.assertTrue(res["is_poor_quality"])
        self.assertTrue(any("BLURRY" in issue for issue in res["issues"]))


class TestDeduplication(unittest.TestCase):
    def setUp(self):
        self.dedup = DefectDeduplicator(min_hits=2)

    def test_multiframe_deduplication(self):
        # Simulate defect ID 1 appearing across 5 consecutive frames
        for frame in range(1, 6):
            dets = [{
                "track_id": 1,
                "class_id": 8,
                "class_name": "PL_Crack",
                "conf": 0.65 + 0.05 * frame,
                "bbox": [100.0, 100.0, 300.0, 250.0],
            }]
            self.dedup.update(frame, frame * 0.1, dets, frame_width=1000, frame_height=1000)

        confirmed = self.dedup.finalize()
        self.assertEqual(len(confirmed), 1, "Expected exactly 1 deduplicated defect")
        d = confirmed[0]
        self.assertEqual(d.defect_id, 1)
        self.assertEqual(d.class_name, "PL_Crack")
        self.assertEqual(d.hits, 5)
        self.assertAlmostEqual(d.peak_confidence, 0.90, places=2)

    def test_single_frame_noise_filtered(self):
        # Spurious 1-frame detection (flicker noise)
        dets = [{
            "track_id": 99,
            "class_id": 2,
            "class_name": "CJ_Sediment",
            "conf": 0.35,
            "bbox": [50.0, 50.0, 80.0, 80.0],
        }]
        self.dedup.update(1, 0.1, dets, frame_width=1000, frame_height=1000)
        confirmed = self.dedup.finalize()
        self.assertEqual(len(confirmed), 0, "1-frame noise must be filtered out")


class TestConditionAssessment(unittest.TestCase):
    def setUp(self):
        self.sev_assessor = DefectSeverityAssessor()
        self.block_assessor = HydraulicBlockageAssessor()
        self.pci_evaluator = PipeConditionEvaluator()

    def test_critical_blockage_and_emergency_priority(self):
        # Heavy root intrusion and sediment
        defects = [
            {
                "defect_id": 1,
                "class_name": "SG_Root_Intrusion",
                "peak_confidence": 0.85,
                "duration_sec": 4.5,
                "max_area_ratio": 0.35,  # 35% of pipe
                "hits": 20,
            },
            {
                "defect_id": 2,
                "class_name": "CJ_Sediment",
                "peak_confidence": 0.80,
                "duration_sec": 5.0,
                "max_area_ratio": 0.30,  # 30% of pipe
                "hits": 25,
            },
        ]
        eval_defects = [self.sev_assessor.evaluate_defect(d) for d in defects]
        block_rep = self.block_assessor.evaluate_blockage(eval_defects)
        cond_rep = self.pci_evaluator.evaluate_pipe_health(eval_defects, block_rep)

        # Blockage should exceed 60%
        self.assertGreaterEqual(block_rep["blockage_percentage"], 60.0)
        self.assertTrue(block_rep["immediate_cleaning_required"])
        # Priority should be P1 Emergency
        self.assertEqual(cond_rep["work_order_priority"], "P1_EMERGENCY")
        # Action must recommend root cutting / jetting
        self.assertTrue(any("root cutting" in d["recommended_repair_action"].lower() for d in eval_defects))

    def test_structural_collapse_risk(self):
        # Severe pipe deformation and cracking
        defects = [
            {
                "defect_id": 1,
                "class_name": "BX_Deformation",
                "peak_confidence": 0.90,
                "duration_sec": 3.0,
                "max_area_ratio": 0.40,
                "hits": 15,
            }
        ]
        eval_defects = [self.sev_assessor.evaluate_defect(d) for d in defects]
        block_rep = self.block_assessor.evaluate_blockage(eval_defects)
        cond_rep = self.pci_evaluator.evaluate_pipe_health(eval_defects, block_rep)

        # Deformation should receive Grade 4 or 5
        self.assertGreaterEqual(eval_defects[0]["severity_grade"], 4)
        # Structural Condition Index should experience heavy deduction
        self.assertLess(cond_rep["structural_index_sci"], 70.0)
        self.assertEqual(cond_rep["work_order_priority"], "P1_EMERGENCY")


if __name__ == "__main__":
    unittest.main()
