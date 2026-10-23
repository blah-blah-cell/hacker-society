import pytest
import os
import json
from fastapi.testclient import TestClient
from src.dashboard import app, BASE_DIR

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_teardown_logs():
    # Setup
    logs_dir = BASE_DIR / "logs"
    os.makedirs(logs_dir, exist_ok=True)

    # Create some mock log files
    log_file_1 = logs_dir / "match_test1_log.json"
    with open(log_file_1, "w") as f:
        json.dump({"test": "data1"}, f)

    log_file_2 = logs_dir / "match_test2_log.json"
    with open(log_file_2, "w") as f:
        json.dump({"test": "data2"}, f)

    # Create a non-match JSON file
    other_file = logs_dir / "other.json"
    with open(other_file, "w") as f:
        json.dump({"test": "other"}, f)

    yield

    # Teardown
    for file in [log_file_1, log_file_2, other_file]:
        if file.exists():
            os.remove(file)

def test_list_logs():
    response = client.get("/api/logs")
    assert response.status_code == 200
    data = response.json()
    assert "logs" in data
    # Check that match logs are returned, but not other.json
    logs = data["logs"]
    assert "match_test1_log.json" in logs
    assert "match_test2_log.json" in logs
    assert "other.json" not in logs

def test_get_log():
    response = client.get("/api/logs/match_test1_log.json")
    assert response.status_code == 200
    data = response.json()
    assert data == {"test": "data1"}

def test_get_log_not_found():
    response = client.get("/api/logs/match_missing_log.json")
    assert response.status_code == 404
    assert response.json()["detail"] == "Log not found"

def test_get_log_directory_traversal():
    # Attempt directory traversal
    response = client.get("/api/logs/..%2F..%2Fsrc%2Fmain.py")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid log_id"

    response = client.get("/api/logs/..\\..\\src\\main.py")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid log_id"
