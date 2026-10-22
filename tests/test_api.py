"""
tests/test_api.py - Complete API Integration Test Suite for FastAPI Backend

Project: AI-Powered Underground Drainage Intelligence and Predictive Maintenance Platform
"""

import unittest
from fastapi.testclient import TestClient
from backend.app.main import app


class TestFastAPIBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_root_endpoint(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ONLINE")
        self.assertIn("documentation", data)

    def test_health_endpoint(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "HEALTHY")
        self.assertIn("device", data)
        self.assertIn("cuda_available", data)
        self.assertIn("model_loaded", data)
        self.assertGreater(data["total_pipes_monitored"], 0)

    def test_list_pipes(self):
        response = self.client.get("/api/v1/pipes/")
        self.assertEqual(response.status_code, 200)
        pipes = response.json()
        self.assertIsInstance(pipes, list)
        self.assertGreaterEqual(len(pipes), 5)
        # Verify first pipe asset has GIS coordinates and ward
        p1 = pipes[0]
        self.assertIn("pipe_id", p1)
        self.assertIn("start_coords", p1)
        self.assertIn("end_coords", p1)
        self.assertEqual(len(p1["start_coords"]), 2)

    def test_get_single_pipe(self):
        response = self.client.get("/api/v1/pipes/PIPE-MUM-001")
        self.assertEqual(response.status_code, 200)
        pipe = response.json()
        self.assertEqual(pipe["pipe_id"], "PIPE-MUM-001")
        self.assertIn("Hindmata", pipe["street_name"])

    def test_get_invalid_pipe(self):
        response = self.client.get("/api/v1/pipes/PIPE-NONEXISTENT")
        self.assertEqual(response.status_code, 404)

    def test_list_inspections(self):
        response = self.client.get("/api/v1/inspections/")
        self.assertEqual(response.status_code, 200)
        inspections = response.json()
        self.assertIsInstance(inspections, list)
        self.assertGreaterEqual(len(inspections), 1)

    def test_get_demo_inspection_detail(self):
        response = self.client.get("/api/v1/inspections/INSP-MUM-DEMO-001")
        self.assertEqual(response.status_code, 200)
        detail = response.json()
        self.assertEqual(detail["inspection_id"], "INSP-MUM-DEMO-001")
        self.assertEqual(detail["status"], "COMPLETED")
        self.assertIsNotNone(detail["pipe_health_indices"])
        self.assertIsNotNone(detail["hydraulic_conveyance_assessment"])
        self.assertIsNotNone(detail["maintenance_dispatch_prioritization"])
        self.assertGreaterEqual(len(detail["detailed_defect_inventory"]), 1)

    def test_work_order_queue(self):
        response = self.client.get("/api/v1/queue")
        self.assertEqual(response.status_code, 200)
        queue_data = response.json()
        self.assertIn("summary", queue_data)
        self.assertIn("work_order_queue", queue_data)
        q = queue_data["work_order_queue"]
        self.assertIn("P1_EMERGENCY", q)
        self.assertIn("P2_HIGH_PRIORITY", q)
        self.assertIn("P3_MEDIUM_PRIORITY", q)
        self.assertIn("P4_ROUTINE_MONITORING", q)

    def test_stream_video(self):
        response = self.client.get("/api/v1/inspections/INSP-MUM-DEMO-001/video")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "video/mp4")

    def test_get_thumbnail(self):
        response = self.client.get("/api/v1/inspections/INSP-MUM-DEMO-001/thumbnails/defect_001_SL_Infiltration.jpg")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "image/jpeg")


if __name__ == "__main__":
    unittest.main()
