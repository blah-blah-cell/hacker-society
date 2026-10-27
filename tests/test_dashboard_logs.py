import json
import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from src.dashboard import app, LOGS_DIR

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_logs():
    # Ensure logs directory exists
    os.makedirs(LOGS_DIR, exist_ok=True)

    # Create some dummy log files
    log1 = LOGS_DIR / "match_1.json"
    log2 = LOGS_DIR / "match_2.json"

    with open(log1, "w", encoding="utf-8") as f:
        json.dump({"match_id": "1", "status": "win"}, f)

    with open(log2, "w", encoding="utf-8") as f:
        json.dump({"match_id": "2", "status": "loss"}, f)

    yield

    # Cleanup
    if log1.exists():
        log1.unlink()
    if log2.exists():
        log2.unlink()

def test_get_logs_list():
    response = client.get("/api/logs")
    assert response.status_code == 200
    data = response.json()
    assert "logs" in data
    assert "match_1.json" in data["logs"]
    assert "match_2.json" in data["logs"]

def test_get_log_content():
    response = client.get("/api/logs/match_1.json")
    assert response.status_code == 200
    data = response.json()
    assert data["match_id"] == "1"
    assert data["status"] == "win"

def test_get_log_not_found():
    response = client.get("/api/logs/nonexistent.json")
    assert response.status_code == 404
    assert response.json()["detail"] == "Log file not found."

def test_path_traversal_blocked():
    # Test typical traversal attempts
    attempts = [
        "../match_1.json",
        "..%2Fmatch_1.json",
        "%2E%2E%2Fmatch_1.json",
        "\\..\\match_1.json",
        "/etc/passwd"
    ]

    for attempt in attempts:
        response = client.get(f"/api/logs/{attempt}")
        # Note: Starlette/FastAPI might return 404 before our route handler runs for some unencoded paths like ../
        # but our specific check should return 400 when it reaches the handler (e.g. for URL encoded).
        assert response.status_code in [400, 404], f"Failed traversal block for {attempt}, got {response.status_code}"
        if response.status_code == 400:
            assert "path traversal attempt detected" in response.json()["detail"]
