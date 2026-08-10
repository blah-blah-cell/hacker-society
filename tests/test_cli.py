import json
import os
import sys
from unittest.mock import patch, mock_open
import pytest

from src.main import main

@patch("src.main._build_parser")
@patch("glob.glob")
@patch("builtins.print")
def test_list_matches_empty(mock_print, mock_glob, mock_build_parser):
    mock_glob.return_value = []

    mock_parser = mock_build_parser.return_value
    mock_parser.parse_args.return_value.list_matches = True

    with pytest.raises(SystemExit) as e:
        main()

    assert e.value.code == 0
    mock_print.assert_any_call("No match logs found.")

@patch("src.main._build_parser")
@patch("glob.glob")
@patch("builtins.print")
def test_list_matches_with_data(mock_print, mock_glob, mock_build_parser):
    mock_glob.side_effect = [["match_123_log.json"], []]

    mock_parser = mock_build_parser.return_value
    mock_parser.parse_args.return_value.list_matches = True

    mock_data = {
        "match_id": "123",
        "timestamp": "2023-10-01",
        "outcome": "attacker_win"
    }

    m_open = mock_open(read_data=json.dumps(mock_data))
    with patch("builtins.open", m_open):
        with pytest.raises(SystemExit) as e:
            main()

    assert e.value.code == 0
    mock_print.assert_any_call("Match ID     | Timestamp                    | Outcome        ")
    mock_print.assert_any_call("123          | 2023-10-01                   | Attacker Win   ")
