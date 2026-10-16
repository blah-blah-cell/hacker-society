import json
import pytest
from fastapi.testclient import TestClient
from src.dashboard import app, LOGS_DIR

client = TestClient(app)

def test_list_logs_empty(tmp_path):
    # Temporarily point LOGS_DIR to an empty directory
    original_logs_dir = LOGS_DIR
    import src.dashboard
    src.dashboard.LOGS_DIR = tmp_path

    response = client.get("/api/logs")
    assert response.status_code == 200
    assert response.json() == []

    # Restore
    src.dashboard.LOGS_DIR = original_logs_dir

def test_list_logs_and_get_log(tmp_path):
    # Create some dummy log files
    log1 = tmp_path / "match_1_log.json"
    log1.write_text(json.dumps({"test": "data1"}))

    log2 = tmp_path / "match_2_log.json"
    log2.write_text(json.dumps({"test": "data2"}))

    # Non-json file should be ignored
    txt_file = tmp_path / "ignore.txt"
    txt_file.write_text("hello")

    original_logs_dir = LOGS_DIR
    import src.dashboard
    src.dashboard.LOGS_DIR = tmp_path

    try:
        # Test listing logs
        response = client.get("/api/logs")
        assert response.status_code == 200
        logs = response.json()
        assert len(logs) == 2
        assert "match_1_log.json" in logs
        assert "match_2_log.json" in logs

        # Test getting specific log
        response = client.get(f"/api/logs/match_1_log.json")
        assert response.status_code == 200
        assert response.json() == {"test": "data1"}

        # Test getting non-existent log
        response = client.get("/api/logs/match_3_log.json")
        assert response.status_code == 404

    finally:
        src.dashboard.LOGS_DIR = original_logs_dir

def test_get_log_directory_traversal():
    # Test path traversal attempts

    # Using parent directory
    response = client.get("/api/logs/..%2F..%2Fetc%2Fpasswd")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid log_id format"

    # Using slashes directly
    response = client.get("/api/logs/some/dir/file.json")
    assert response.status_code == 400

    # Using backslashes
    response = client.get("/api/logs/some\\dir\\file.json")
    assert response.status_code == 400

    # Starlette unencoded traversals usually result in 404 directly from the router,
    # but we can test our logic directly if we want
