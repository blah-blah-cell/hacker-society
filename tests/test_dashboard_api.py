import json
import os
import tempfile
from fastapi.testclient import TestClient

from src.dashboard import app, BASE_DIR

client = TestClient(app)

def test_api_logs_list():
    # Setup: Create a temporary logs directory
    logs_dir = BASE_DIR / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Create dummy JSON log files
    dummy_files = ["test_log_1.json", "test_log_2.json"]
    for file_name in dummy_files:
        with open(logs_dir / file_name, "w", encoding="utf-8") as f:
            json.dump({"message": "test"}, f)

    # Also create a non-JSON file to make sure it's not included
    with open(logs_dir / "test_log_3.txt", "w", encoding="utf-8") as f:
        f.write("text log")

    try:
        response = client.get("/api/logs")
        assert response.status_code == 200
        logs = response.json()
        assert isinstance(logs, list)
        assert "test_log_1.json" in logs
        assert "test_log_2.json" in logs
        assert "test_log_3.txt" not in logs
    finally:
        # Cleanup
        for file_name in dummy_files + ["test_log_3.txt"]:
            file_path = logs_dir / file_name
            if file_path.exists():
                file_path.unlink()

def test_api_logs_get_valid():
    logs_dir = BASE_DIR / "logs"
    logs_dir.mkdir(exist_ok=True)

    file_name = "test_log_valid.json"
    content = {"key": "value", "id": 123}

    with open(logs_dir / file_name, "w", encoding="utf-8") as f:
        json.dump(content, f)

    try:
        response = client.get(f"/api/logs/{file_name}")
        assert response.status_code == 200
        assert response.json() == content
    finally:
        file_path = logs_dir / file_name
        if file_path.exists():
            file_path.unlink()

def test_api_logs_path_traversal():
    # Test typical directory traversal paths, encoded and unencoded
    traversal_paths = [
        "../test.json",
        "..%2Ftest.json",
        "some/dir/test.json",
        "some%2Fdir%2Ftest.json",
        "..\\test.json"
    ]

    for path in traversal_paths:
        response = client.get(f"/api/logs/{path}")
        # Depending on path handling by TestClient/Starlette, we might get a 400 (our code) or a 404
        assert response.status_code in (400, 404)
        if response.status_code == 400:
            assert "Directory traversal is not allowed" in response.json()["detail"]

def test_api_logs_not_found():
    response = client.get("/api/logs/nonexistent_file.json")
    assert response.status_code == 404
    assert "Log file not found" in response.json()["detail"]
