import json
import pytest
from fastapi.testclient import TestClient
from src.dashboard import app, LOGS_DIR

client = TestClient(app)

@pytest.fixture
def mock_log_file():
    test_log = LOGS_DIR / "test_match_log.json"
    data = {"status": "ok", "match_id": "test"}
    test_log.write_text(json.dumps(data), encoding="utf-8")
    yield test_log
    if test_log.exists():
        test_log.unlink()

def test_api_logs(mock_log_file):
    response = client.get("/api/logs")
    assert response.status_code == 200
    assert "test_match_log.json" in response.json()["logs"]

def test_api_log_id(mock_log_file):
    response = client.get("/api/logs/test_match_log.json")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "match_id": "test"}

def test_api_log_not_found():
    response = client.get("/api/logs/does_not_exist.json")
    assert response.status_code == 404

def test_api_log_invalid_format():
    response = client.get("/api/logs/some_log.txt")
    assert response.status_code == 404

def test_api_log_traversal():
    response = client.get("/api/logs/..%2F..%2Fetc%2Fpasswd")
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid log_id format"}

    response = client.get("/api/logs/subdir%2Ffile.json")
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid log_id format"}
