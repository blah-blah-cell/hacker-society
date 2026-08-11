import json
import os
from pathlib import Path
from fastapi.testclient import TestClient
from src.dashboard import app

client = TestClient(app)

def test_list_matches(tmp_path, monkeypatch):
    # Mock BASE_DIR to point to tmp_path
    monkeypatch.setattr("src.dashboard.BASE_DIR", tmp_path)

    # Create logs directory and a dummy match log
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    log_file1 = logs_dir / "match_test123_log.json"
    log_file2 = logs_dir / "match_test456_log.json"
    log_file1.write_text("{}")
    log_file2.write_text("{}")

    response = client.get("/api/matches")
    assert response.status_code == 200
    data = response.json()
    assert "matches" in data
    assert len(data["matches"]) == 2
    assert "match_test123_log.json" in data["matches"]
    assert "match_test456_log.json" in data["matches"]

def test_get_match(tmp_path, monkeypatch):
    monkeypatch.setattr("src.dashboard.BASE_DIR", tmp_path)

    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    log_file = logs_dir / "match_test123_log.json"
    log_data = {"match_id": "test123_log"}
    log_file.write_text(json.dumps(log_data))

    # Test with full filename
    response = client.get("/api/matches/match_test123_log.json")
    assert response.status_code == 200
    assert response.json() == log_data

    # Test with just ID
    response2 = client.get("/api/matches/test123")
    assert response2.status_code == 200
    assert response2.json() == log_data

    # Test not found
    response3 = client.get("/api/matches/nonexistent")
    assert response3.status_code == 404
    assert response3.json() == {"error": "Match log not found"}

def test_get_match_path_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr("src.dashboard.BASE_DIR", tmp_path)

    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()

    # Try directory traversal
    # Test client URL decodes %2F to / and passes it down
    # But wait, actually starlette might intercept it. Let's send a raw match_id.
    response = client.get("/api/matches/..%2f..%2fetc%2fpasswd.json")
    assert response.status_code in (400, 404)

def test_get_match_invalid_json(tmp_path, monkeypatch):
    monkeypatch.setattr("src.dashboard.BASE_DIR", tmp_path)

    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    log_file = logs_dir / "match_test123_log.json"
    log_file.write_text("invalid json format")

    response = client.get("/api/matches/test123")
    assert response.status_code == 500
    assert response.json() == {"error": "Failed to parse match log"}

def test_list_matches_no_logs_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("src.dashboard.BASE_DIR", tmp_path)
    # Don't create logs dir
    response = client.get("/api/matches")
    assert response.status_code == 200
    assert response.json() == {"matches": []}
