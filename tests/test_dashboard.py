import pytest
from fastapi.testclient import TestClient
from unittest import mock
import json
from pathlib import Path
import os

from src.dashboard import app, BASE_DIR

client = TestClient(app)

@pytest.fixture
def mock_logs_dir(tmp_path):
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()

    # Create a dummy log file
    log_data = {
        "match_id": "test_match_123",
        "outcome": "attacker_win",
        "turns": [{"turn_number": 1}]
    }
    log_file = logs_dir / "match_test_log.json"
    with open(log_file, "w") as f:
        json.dump(log_data, f)

    # Patch BASE_DIR in the module so it uses tmp_path instead of the real directory
    with mock.patch("src.dashboard.BASE_DIR", tmp_path):
        yield logs_dir

def test_get_logs(mock_logs_dir):
    response = client.get("/api/logs")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["log_id"] == "match_test_log.json"
    assert data[0]["match_id"] == "test_match_123"
    assert data[0]["outcome"] == "attacker_win"
    assert data[0]["turns"] == 1

def test_get_logs_empty(tmp_path):
    # Pass a tmp_path with no logs directory
    with mock.patch("src.dashboard.BASE_DIR", tmp_path):
        response = client.get("/api/logs")
        assert response.status_code == 200
        assert response.json() == []

def test_get_log_by_id(mock_logs_dir):
    response = client.get("/api/logs/match_test_log.json")
    assert response.status_code == 200
    data = response.json()
    assert data["match_id"] == "test_match_123"

def test_get_log_by_id_not_found(mock_logs_dir):
    response = client.get("/api/logs/match_nonexistent_log.json")
    assert response.status_code == 404
    assert response.json() == {"detail": "Log not found"}

@pytest.mark.parametrize("malicious_path", [
    "..%2Fpasswd",
    "/etc/passwd",
    "some\\path",
])
def test_get_log_by_id_path_traversal(mock_logs_dir, malicious_path):
    response = client.get(f"/api/logs/{malicious_path}")
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid log ID"}

def test_get_log_by_id_path_traversal_starlette(mock_logs_dir):
    response = client.get("/api/logs/../passwd")
    assert response.status_code == 404
