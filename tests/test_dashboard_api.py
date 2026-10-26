import os
import json
import pytest
from fastapi.testclient import TestClient
from pathlib import Path

from src.dashboard import app, BASE_DIR

client = TestClient(app)

@pytest.fixture
def mock_log_dir(tmp_path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    log_file1 = log_dir / "match_1_log.json"
    log_file1.write_text(json.dumps({"test": "data 1"}))

    log_file2 = log_dir / "match_2_log.json"
    log_file2.write_text(json.dumps({"test": "data 2"}))

    # We patch the BASE_DIR in dashboard.py to point to our tmp_path
    # but instead of mocking we can just change the directory
    import src.dashboard
    old_base_dir = src.dashboard.BASE_DIR
    src.dashboard.BASE_DIR = tmp_path
    yield log_dir
    src.dashboard.BASE_DIR = old_base_dir

def test_get_logs_list(mock_log_dir):
    response = client.get("/api/logs")
    assert response.status_code == 200
    logs = response.json()
    assert isinstance(logs, list)
    assert len(logs) == 2
    assert "match_1_log.json" in logs
    assert "match_2_log.json" in logs

def test_get_log_content(mock_log_dir):
    response = client.get("/api/logs/match_1_log.json")
    assert response.status_code == 200
    data = response.json()
    assert data == {"test": "data 1"}

def test_get_log_content_not_found(mock_log_dir):
    response = client.get("/api/logs/does_not_exist.json")
    assert response.status_code == 404

def test_get_log_content_directory_traversal_encoded(mock_log_dir):
    # Test directory traversal prevention
    response = client.get("/api/logs/..%2F..%2Fetc%2Fpasswd")
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid log ID"}

def test_get_log_content_directory_traversal_unencoded(mock_log_dir):
    # Starlette/FastAPI will likely resolve this to 404 naturally
    # before our handler is even called, but we test anyway
    response = client.get("/api/logs/../../etc/passwd")
    assert response.status_code == 404
