import pytest
from fastapi.testclient import TestClient
from src.dashboard import app, BASE_DIR

client = TestClient(app)

def test_api_logs_list(tmp_path, monkeypatch):
    monkeypatch.setattr("src.dashboard.BASE_DIR", tmp_path)
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()

    (logs_dir / "test1.json").write_text('{"id": 1}')
    (logs_dir / "test2.json").write_text('{"id": 2}')
    (logs_dir / "not_a_log.txt").write_text('hello')

    response = client.get("/api/logs")
    assert response.status_code == 200
    assert set(response.json()) == {"test1.json", "test2.json"}

def test_api_logs_get_valid(tmp_path, monkeypatch):
    monkeypatch.setattr("src.dashboard.BASE_DIR", tmp_path)
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()

    (logs_dir / "test1.json").write_text('{"hello": "world"}')

    response = client.get("/api/logs/test1.json")
    assert response.status_code == 200
    assert response.json() == {"hello": "world"}

def test_api_logs_get_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr("src.dashboard.BASE_DIR", tmp_path)
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()

    response = client.get("/api/logs/does_not_exist.json")
    assert response.status_code == 404

def test_api_logs_get_path_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr("src.dashboard.BASE_DIR", tmp_path)
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()

    # URL encoded payload for ../../etc/passwd
    response = client.get("/api/logs/..%2F..%2Fetc%2Fpasswd")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid log_id"
