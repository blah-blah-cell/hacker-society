import pytest
from fastapi.testclient import TestClient
import json
import os
from pathlib import Path
from src.dashboard import app, LOGS_DIR

client = TestClient(app)

def test_api_logs_list(tmp_path, monkeypatch):
    monkeypatch.setattr("src.dashboard.LOGS_DIR", tmp_path)
    # Create some dummy log files
    (tmp_path / "log1.json").write_text('{"foo": "bar"}')
    (tmp_path / "log2.json").write_text('{"baz": "qux"}')
    (tmp_path / "not_a_log.txt").write_text("ignore me")

    response = client.get("/api/logs")
    assert response.status_code == 200
    data = response.json()
    assert "logs" in data
    assert len(data["logs"]) == 2
    assert "log1.json" in data["logs"]
    assert "log2.json" in data["logs"]

def test_api_logs_get_success(tmp_path, monkeypatch):
    monkeypatch.setattr("src.dashboard.LOGS_DIR", tmp_path)
    log_content = {"status": "ok"}
    (tmp_path / "mylog.json").write_text(json.dumps(log_content))

    response = client.get("/api/logs/mylog.json")
    assert response.status_code == 200
    assert response.json() == log_content

def test_api_logs_get_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr("src.dashboard.LOGS_DIR", tmp_path)
    response = client.get("/api/logs/nonexistent.json")
    assert response.status_code == 404

def test_api_logs_get_directory_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr("src.dashboard.LOGS_DIR", tmp_path)
    # The client might normalize standard '..', so we test encoded traversing
    # Fastapi will not decode standard %2F before matching path parameter in our manual checks unless we encode it properly

    response = client.get("/api/logs/..%2F..%2Fetc%2Fpasswd")
    # According to our checks in get_log, "/" and ".." are checked.
    # With TestClient, if we pass literal ".." in URL string, it's often resolved by httpx.
    # The vulnerability specifically asks to check for 400 Bad Request responses.
    # Our manual check: `if "/" in log_id or "\\" in log_id or ".." in log_id:`

    # Path parameter might decode it before giving to our handler, let's test typical encoded attempts

    # Actually, httpx / Starlette resolves '..' so it never hits our route if it goes out of scope,
    # But if we send URL encoded %2F and %2E it might hit it.
    assert response.status_code == 400
    assert "Invalid log_id" in response.json()["detail"]

    response2 = client.get("/api/logs/..%5Cwindows%5Csystem32")
    assert response2.status_code == 400
    assert "Invalid log_id" in response2.json()["detail"]
