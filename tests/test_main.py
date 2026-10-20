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
