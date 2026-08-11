import pytest
import argparse
from unittest.mock import patch, MagicMock

from src.main import _build_parser, main


def test_disable_memory_flag_parsing():
    parser = _build_parser()

    # Test without flag
    args = parser.parse_args([])
    assert args.disable_memory is False

    # Test with flag
    args = parser.parse_args(["--disable-memory"])
    assert args.disable_memory is True


@patch("src.main.Environment")
@patch("src.main.Agent")
@patch("src.main.Match")
@patch("src.main.MemoryStore")
@patch("builtins.input", return_value="1")
def test_disable_memory_in_system_prompt(mock_input, mock_memory_store, mock_match, mock_agent, mock_env):
    # Setup mock memory
    mock_memory_store.return_value.get_memory.return_value = ["Test memory"]

    # Patch sys.argv for the test
    with patch("sys.argv", ["main.py", "--disable-memory", "--model", "mock-model", "--attackers", "1", "--defenders", "1"]):
        main()

        # We need to manually invoke `main()` in a way where we can assert the arguments.
        # Since testing Agent instantiations is difficult because of context manager usage inside main
        # (e.g. `with Environment(...) as env:` causes exceptions if not mocked thoroughly)
        # we can just test the inner _memory_str function via mock or refactor test.

        # Let's intercept memory_store.get_memory to see if it was called
        # If --disable-memory is passed, it should NOT be called.
        mock_memory_store.return_value.get_memory.assert_not_called()

    # Test WITHOUT the flag
    with patch("sys.argv", ["main.py", "--model", "mock-model", "--attackers", "1", "--defenders", "1"]):
        mock_memory_store.return_value.get_memory.reset_mock()
        main()

        # It should have been called
        assert mock_memory_store.return_value.get_memory.called
