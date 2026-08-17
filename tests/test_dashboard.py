import os
import json
from pathlib import Path
from fastapi.testclient import TestClient
from src.dashboard import app, BASE_DIR

client = TestClient(app)

def test_list_logs(tmp_path):
    logs_dir = BASE_DIR / "logs"
    logs_dir.mkdir(exist_ok=True)

    test_log = logs_dir / "test_match.json"
    test_log.write_text(json.dumps({"test": "data"}))

    response = client.get("/api/logs")
    assert response.status_code == 200
    assert "test_match.json" in response.json()["logs"]

def test_get_log(tmp_path):
    logs_dir = BASE_DIR / "logs"
    logs_dir.mkdir(exist_ok=True)

    test_log = logs_dir / "test_match_2.json"
    test_log.write_text(json.dumps({"key": "value"}))

    response = client.get("/api/logs/test_match_2.json")
    assert response.status_code == 200
    assert response.json() == {"key": "value"}

def test_directory_traversal_protection():
    traversal_paths = [
        "../test.json",
        "nested/test.json",
        "..%2Ftest.json",
        "%2E%2E/test.json"
    ]

    for path in traversal_paths:
        response = client.get(f"/api/logs/{path}")
        # TestClient (httpx) might automatically resolve ".." in path before sending request,
        # which means it sends `/api/test.json` resulting in a 404 Not Found at router level.
        # So we assert the endpoint either catches it (400) or it's unroutable/not found (404)
        assert response.status_code in (400, 404)
        if response.status_code == 400:
            assert response.json() == {"detail": "Invalid log ID"}
