from fastapi.testclient import TestClient
from src.dashboard import app, BASE_DIR
import json

client = TestClient(app)

def test_get_logs(monkeypatch, tmp_path):
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    (logs_dir / "test1.json").write_text("{}")
    (logs_dir / "test2.json").write_text("{}")

    # Mock BASE_DIR to tmp_path
    monkeypatch.setattr("src.dashboard.BASE_DIR", tmp_path)

    response = client.get("/api/logs")
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) == 2
    assert {"id": "test1.json"} in logs
    assert {"id": "test2.json"} in logs

def test_get_log_success(monkeypatch, tmp_path):
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    (logs_dir / "test1.json").write_text(json.dumps({"key": "value"}))

    monkeypatch.setattr("src.dashboard.BASE_DIR", tmp_path)

    response = client.get("/api/logs/test1.json")
    assert response.status_code == 200
    assert response.json() == {"key": "value"}

def test_get_log_not_found(monkeypatch, tmp_path):
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()

    monkeypatch.setattr("src.dashboard.BASE_DIR", tmp_path)

    response = client.get("/api/logs/nonexistent.json")
    assert response.status_code == 404

def test_get_log_directory_traversal(monkeypatch, tmp_path):
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()

    monkeypatch.setattr("src.dashboard.BASE_DIR", tmp_path)

    response = client.get("/api/logs/..%2F..%2Fetc%2Fpasswd")
    assert response.status_code == 400

    response = client.get("/api/logs/sub%2Fdir%2Ftest.json")
    assert response.status_code == 400
