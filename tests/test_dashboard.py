import json
from pathlib import Path
from fastapi.testclient import TestClient
from src.dashboard import app

client = TestClient(app)

def test_list_logs_empty(tmp_path, monkeypatch):
    monkeypatch.setattr("src.dashboard.BASE_DIR", tmp_path)
    response = client.get("/api/logs")
    assert response.status_code == 200
    assert response.json() == {"logs": []}

def test_list_logs_with_files(tmp_path, monkeypatch):
    monkeypatch.setattr("src.dashboard.BASE_DIR", tmp_path)
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    (logs_dir / "match_1.json").write_text('{"event": "test"}')
    (logs_dir / "not_json.txt").write_text("test")

    response = client.get("/api/logs")
    assert response.status_code == 200
    assert "match_1.json" in response.json()["logs"]
    assert "not_json.txt" not in response.json()["logs"]

def test_get_log_success(tmp_path, monkeypatch):
    monkeypatch.setattr("src.dashboard.BASE_DIR", tmp_path)
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    (logs_dir / "match_1.json").write_text('{"event": "test"}')

    response = client.get("/api/logs/match_1.json")
    assert response.status_code == 200
    assert response.json() == {"event": "test"}

def test_get_log_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr("src.dashboard.BASE_DIR", tmp_path)
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()

    response = client.get("/api/logs/match_99.json")
    assert response.status_code == 404

def test_get_log_path_traversal_dots(tmp_path, monkeypatch):
    monkeypatch.setattr("src.dashboard.BASE_DIR", tmp_path)
    response = client.get("/api/logs/..%2Fmatch_1.json")
    assert response.status_code == 400

def test_get_log_path_traversal_slash(tmp_path, monkeypatch):
    monkeypatch.setattr("src.dashboard.BASE_DIR", tmp_path)
    # Using %2F to pass the slash in the path parameter
    response = client.get("/api/logs/some%2Fdir%2Fmatch_1.json")
    assert response.status_code == 400
