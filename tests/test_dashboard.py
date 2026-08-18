import os
import json
import tempfile
import pytest
from fastapi.testclient import TestClient

from src.dashboard import app, BASE_DIR

client = TestClient(app)

@pytest.fixture
def setup_logs_dir():
    logs_dir = BASE_DIR / "logs"
    logs_dir.mkdir(exist_ok=True)

    test_log_path = logs_dir / "test_match_log.json"
    with open(test_log_path, "w") as f:
        json.dump({"match_id": "test", "status": "completed"}, f)

    yield logs_dir

    # Cleanup
    if test_log_path.exists():
        test_log_path.unlink()

def test_list_logs(setup_logs_dir):
    response = client.get("/api/logs")
    assert response.status_code == 200
    data = response.json()
    assert "logs" in data
    assert "test_match_log.json" in data["logs"]

def test_get_log(setup_logs_dir):
    response = client.get("/api/logs/test_match_log.json")
    assert response.status_code == 200
    data = response.json()
    assert data["match_id"] == "test"

def test_get_log_not_found():
    response = client.get("/api/logs/nonexistent.json")
    assert response.status_code == 404

def test_get_log_directory_traversal():
    # Test path traversal attempts
    attempts = [
        "../test.json",
        "..%2Ftest.json",
        "some_dir/test.json",
        "some_dir%2Ftest.json",
        "..\\test.json",
        "some_dir\\test.json"
    ]

    for attempt in attempts:
        response = client.get(f"/api/logs/{attempt}")
        # When unencoded `..` is used, the client/Starlette often resolves the path before the handler, resulting in a 404 on a non-existent route like `/api/test.json`
        if attempt == "../test.json":
            assert response.status_code == 404
        else:
            assert response.status_code == 400
            assert "Invalid log_id path parameter" in response.json()["detail"]
