import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from src.dashboard import app, LOGS_DIR

client = TestClient(app)

@pytest.fixture
def mock_logs_dir(tmp_path, monkeypatch):
    """Fixture to mock LOGS_DIR to a temporary directory for testing."""
    monkeypatch.setattr("src.dashboard.LOGS_DIR", tmp_path)
    return tmp_path

def test_list_logs_empty(mock_logs_dir):
    """Test listing logs when directory is empty."""
    response = client.get("/api/logs")
    assert response.status_code == 200
    assert response.json() == []

def test_list_logs_with_files(mock_logs_dir):
    """Test listing logs with files present."""
    log_file_1 = mock_logs_dir / "match_123_log.json"
    log_file_2 = mock_logs_dir / "match_456_log.json"
    log_file_3 = mock_logs_dir / "other_file.txt" # Should be ignored

    log_file_1.write_text("{}")
    log_file_2.write_text("{}")
    log_file_3.write_text("not a log")

    response = client.get("/api/logs")
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) == 2
    assert "match_123_log.json" in logs
    assert "match_456_log.json" in logs
    assert "other_file.txt" not in logs

def test_get_log_success(mock_logs_dir):
    """Test successfully retrieving a log."""
    log_file = mock_logs_dir / "match_123_log.json"
    log_data = {"test": "data"}
    log_file.write_text(json.dumps(log_data))

    response = client.get("/api/logs/match_123_log.json")
    assert response.status_code == 200
    assert response.json() == log_data

def test_get_log_not_found(mock_logs_dir):
    """Test retrieving a log that does not exist."""
    response = client.get("/api/logs/nonexistent_log.json")
    assert response.status_code == 404
    assert response.json() == {"detail": "Log not found"}

def test_get_log_path_traversal(mock_logs_dir):
    """Test path traversal mitigation."""
    # Attempt directory traversal with encoded ../
    response = client.get("/api/logs/..%2F..%2Fetc%2Fpasswd")
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid log ID"}

    # Attempt directory traversal with /
    response = client.get("/api/logs/some%2Fdir%2Ffile.json")
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid log ID"}

def test_get_log_invalid_json(mock_logs_dir):
    """Test retrieving a log with invalid JSON content."""
    log_file = mock_logs_dir / "match_bad_log.json"
    log_file.write_text("invalid json {")

    response = client.get("/api/logs/match_bad_log.json")
    assert response.status_code == 500
    assert response.json() == {"detail": "Error reading log file"}
