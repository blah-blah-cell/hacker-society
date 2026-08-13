import os
import sys
from unittest.mock import patch
from src.main import main


def test_disable_memory_flag(monkeypatch):
    """Test that the --disable-memory flag sets Match.memory_store to None."""
    # Run the main function with mock inputs
    test_args = [
        "src/main.py",
        "--attackers", "1",
        "--defenders", "1",
        "--turns", "1",
        "--disable-memory",
        "--model", "mock-model",
        "--base-url", "http://localhost:8000/v1"
    ]
    monkeypatch.setattr(sys, "argv", test_args)
    monkeypatch.setenv("MOCK_DOCKER_NO_CONTAINERS", "1")

    # Mock the Match class to intercept its initialization
    with patch("src.main.Match") as mock_match:
        # Mock run method to return dummy string
        mock_instance = mock_match.return_value
        mock_instance.run.return_value = "attacker_win"
        mock_instance.log_file = "test_log.json"

        # Mock the vulnerability choice input
        with patch("builtins.input", return_value="1"):
            # Mock load_dotenv
            with patch("src.main.load_dotenv"):
                # Mock uuid.uuid4 to return a fixed hex
                with patch("src.main.uuid.uuid4") as mock_uuid:
                    class DummyUUID:
                        hex = "mocked-uuid-1234"
                    mock_uuid.return_value = DummyUUID()

                    try:
                        main()
                    except Exception as e:
                        # Should not raise exception if mock works
                        print(e)
                        pass

        # Check if Match was called and its memory_store argument
        assert mock_match.call_count == 1
        _, kwargs = mock_match.call_args
        assert "memory_store" in kwargs
        assert kwargs["memory_store"] is None
