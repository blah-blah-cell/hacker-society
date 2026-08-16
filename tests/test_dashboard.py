import os
import json
import pytest
from fastapi.testclient import TestClient
from src.dashboard import app, LOGS_DIR

client = TestClient(app)

@pytest.fixture
def setup_logs(tmp_path):
    # Temporarily override LOGS_DIR for testing
    import src.dashboard
    old_logs_dir = src.dashboard.LOGS_DIR
    src.dashboard.LOGS_DIR = tmp_path

    # Create mock log files
    log1 = tmp_path / "match_1.json"
    log1.write_text(json.dumps({"id": 1, "status": "finished"}))

    log2 = tmp_path / "match_2.json"
    log2.write_text(json.dumps({"id": 2, "status": "running"}))

    # Add a non-json file to test filtering
    (tmp_path / "ignore.txt").write_text("ignore me")

    yield tmp_path

    # Restore original LOGS_DIR
    src.dashboard.LOGS_DIR = old_logs_dir


def test_list_logs(setup_logs):
    response = client.get("/api/logs")
    assert response.status_code == 200
    data = response.json()
    assert "logs" in data

    logs = data["logs"]
    assert len(logs) == 2
    assert "match_1.json" in logs
    assert "match_2.json" in logs
    assert "ignore.txt" not in logs

def test_get_log_success(setup_logs):
    response = client.get("/api/logs/match_1.json")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["status"] == "finished"

def test_get_log_not_found(setup_logs):
    response = client.get("/api/logs/missing.json")
    assert response.status_code == 404
    assert response.json()["detail"] == "Log not found"

def test_get_log_directory_traversal_slashes(setup_logs):
    # These should be caught by our manual check
    response = client.get("/api/logs/..%2Fmatch_1.json")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid log ID"

    response = client.get("/api/logs/some%2Fdir%2Fmatch.json")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid log ID"

def test_get_log_directory_traversal_dots(setup_logs):
    # Even if they try to use .. without slashes (unlikely to work for traversal anyway, but good to test)
    response = client.get("/api/logs/..match_1.json")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid log ID"
