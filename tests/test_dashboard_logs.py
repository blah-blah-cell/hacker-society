import pytest
from fastapi.testclient import TestClient
from src.dashboard import app, BASE_DIR
import json
import os

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_logs():
    logs_dir = BASE_DIR / "logs"
    logs_dir.mkdir(exist_ok=True)

    test_log_path = logs_dir / "test_match_log.json"
    with open(test_log_path, "w") as f:
        json.dump({"test": "data"}, f)

    yield

    if test_log_path.exists():
        os.remove(test_log_path)


def test_get_logs():
    response = client.get("/api/logs")
    assert response.status_code == 200
    data = response.json()
    assert any(log["id"] == "test_match_log.json" for log in data)

def test_get_log_success():
    response = client.get("/api/logs/test_match_log.json")
    assert response.status_code == 200
    data = response.json()
    assert data == {"test": "data"}

def test_get_log_not_found():
    response = client.get("/api/logs/non_existent.json")
    assert response.status_code == 404
    assert response.json() == {"detail": "Log not found"}

def test_get_log_path_traversal():
    # Attempting to access parent directory directly (FastAPI handles Unencoded)
    response = client.get("/api/logs/../dashboard.py")
    assert response.status_code == 404

    # URL encoded traversal
    response = client.get("/api/logs/..%2Fdashboard.py")
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid log ID"}

    response = client.get("/api/logs/..%5Cdashboard.py")
    assert response.status_code == 400

    response = client.get("/api/logs/some_dir%2Ftest.json")
    assert response.status_code == 400
