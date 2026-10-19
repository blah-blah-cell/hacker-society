import hashlib

from src.match import Match


class _Agent:
    def __init__(self, agent_id, response):
        self.agent_id = agent_id
        self.response = response

    def take_turn(self, _prompt):
        return self.response


class _Environment:
    pass


def test_match_does_not_rotate_or_expose_the_vault_flag(monkeypatch, capsys, tmp_path):
    """The flag injected at setup must remain the only valid match flag."""
    monkeypatch.chdir(tmp_path)
    flag = "0123456789abcdef0123456789abcdef"
    environment = _Environment()
    environment.secret_flag = flag
    match = Match(
        attackers=[_Agent("attacker_0", f"EXFILTRATED {flag}")],
        defenders=[],
        environment=environment,
        secret_flag=flag,
        max_turns=1,
    )

    assert match.run([]) == "attacker_win"
    assert match.secret_flag == flag
    assert environment.secret_flag == flag
    assert match.logs["secret_flag_sha256"] == hashlib.sha256(flag.encode()).hexdigest()
    assert flag not in capsys.readouterr().out
    assert flag not in match.logs["turns"][0]["events"][0]["action"]

from fastapi.testclient import TestClient
from src.dashboard import app

def test_api_logs_path_traversal():
    client = TestClient(app)

    # Encoded path traversal
    response = client.get("/api/logs/..%2F..%2Fetc%2Fpasswd")
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid log_id"}

    # Direct path traversal should also fail or be 404 handled by Starlette
    response = client.get("/api/logs/../../etc/passwd")
    assert response.status_code in [400, 404]

    # Valid log
    response = client.get("/api/logs/valid_log.json")
    # It might be 404 since it doesn't exist, but it shouldn't be 400
    assert response.status_code == 404
