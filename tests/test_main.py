import subprocess
import sys

def test_cli_version_flag():
    result = subprocess.run(
        [sys.executable, "-m", "src.main", "--version"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Hacker Society 1.0.0" in result.stdout or "Hacker Society 1.0.0" in result.stderr

def test_cli_vuln_bypass():
    import os
    env = os.environ.copy()
    env["MOCK_DOCKER_NO_CONTAINERS"] = "1"

    result = subprocess.run(
        [
            sys.executable, "-m", "src.main",
            "--vuln", "1",
            "--turns", "1",
            "--model", "mock-model",
            "--attacker-provider", "mock",
            "--defender-provider", "mock",
        ],
        capture_output=True,
        text=True,
        env=env
    )
    # the interactive prompt "Enter choice [1-21]" should NOT be in the output
    assert "Enter choice" not in result.stdout
    # it should output that it's initializing
    assert "Initializing Hacker Society Engine" in result.stdout
