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
