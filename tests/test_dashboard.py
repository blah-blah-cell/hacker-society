import os
import json
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from src.dashboard import app, BASE_DIR

client = TestClient(app)

class TestDashboard(unittest.TestCase):
    def setUp(self):
        self.logs_dir = BASE_DIR / "logs"
        os.makedirs(self.logs_dir, exist_ok=True)

        self.match_id = "test_123"
        self.log_file = self.logs_dir / f"match_{self.match_id}_log.json"

        self.mock_log = {"match_id": self.match_id, "turns": []}
        with open(self.log_file, "w") as f:
            json.dump(self.mock_log, f)

    def tearDown(self):
        if self.log_file.exists():
            os.remove(self.log_file)

    def test_get_logs(self):
        response = client.get("/api/logs")
        self.assertEqual(response.status_code, 200)
        self.assertIn("logs", response.json())
        self.assertIn(self.match_id, response.json()["logs"])

    def test_get_match_log_success(self):
        response = client.get(f"/api/logs/{self.match_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), self.mock_log)

    def test_get_match_log_not_found(self):
        response = client.get("/api/logs/nonexistent")
        self.assertEqual(response.status_code, 404)

    def test_get_match_log_path_traversal(self):
        response = client.get("/api/logs/..%2Fdashboard")
        self.assertEqual(response.status_code, 400)

        response = client.get("/api/logs/%2E%2E%2Fdashboard")
        self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main()
