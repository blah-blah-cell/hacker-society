import json
import pytest
from fastapi.testclient import TestClient
import os
from pathlib import Path
from src.dashboard import app, BASE_DIR

client = TestClient(app)

@pytest.fixture
def mock_logs_dir(tmp_path, monkeypatch):
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()

    # Create some mock log files
    log1 = logs_dir / "match_1_log.json"
    log1.write_text(json.dumps({"match_id": "1", "outcome": "attacker_win"}), encoding="utf-8")

    log2 = logs_dir / "match_2_log.json"
    log2.write_text(json.dumps({"match_id": "2", "outcome": "defender_win"}), encoding="utf-8")

    # Create a non-json file to ensure it's ignored
    not_log = logs_dir / "not_a_log.txt"
    not_log.write_text("Hello World")

    # Monkeypatch BASE_DIR to point to our tmp_path
    monkeypatch.setattr("src.dashboard.BASE_DIR", tmp_path)
    return logs_dir


def test_list_logs(mock_logs_dir):
    response = client.get("/api/logs")
    assert response.status_code == 200
    data = response.json()
    assert "logs" in data
    assert isinstance(data["logs"], list)
    assert len(data["logs"]) == 2
    assert "match_1_log.json" in data["logs"]
    assert "match_2_log.json" in data["logs"]
    assert "not_a_log.txt" not in data["logs"]


def test_get_log(mock_logs_dir):
    response = client.get("/api/logs/match_1_log.json")
    assert response.status_code == 200
    data = response.json()
    assert data["match_id"] == "1"
    assert data["outcome"] == "attacker_win"


def test_get_log_not_found(mock_logs_dir):
    response = client.get("/api/logs/match_999_log.json")
    assert response.status_code == 404
    assert response.json()["detail"] == "Log file not found"


def test_get_log_directory_traversal():
    # Test path traversal attempts (with proper url encoding to hit the endpoint correctly)
    invalid_paths = [
        "..%2Fmatch_1_log.json",
        "..%5Cmatch_1_log.json",
        "some%2Fpath%2Fmatch_1_log.json",
        "some%5Cpath%5Cmatch_1_log.json"
    ]

    for path in invalid_paths:
        response = client.get(f"/api/logs/{path}")
        assert response.status_code == 400
        assert "directory traversal not allowed" in response.json()["detail"].lower()
