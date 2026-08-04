import json
import os
import sys
import unittest
from unittest.mock import patch
import io
import tempfile

# Ensure src is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.replay import replay_match

class TestReplay(unittest.TestCase):
    def setUp(self):
        self.mock_log = {
            "match_id": "test_id_123",
            "timestamp": "2023-10-27T10:00:00.000",
            "outcome": "attacker_win",
            "turns": [
                {
                    "turn_number": 1,
                    "events": [
                        {
                            "role": "defender",
                            "agent_id": "def_0",
                            "action": "iptables -A INPUT -p tcp --dport 22 -j DROP",
                            "shaped_reward": 0.2
                        },
                        {
                            "role": "attacker",
                            "agent_id": "att_0",
                            "action": "nmap -sS 10.0.0.1",
                            "shaped_reward": 0.1
                        }
                    ]
                }
            ]
        }
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file_path = os.path.join(self.temp_dir.name, "test_log.json")
        with open(self.log_file_path, "w") as f:
            json.dump(self.mock_log, f)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_replay_match_output(self):
        captured_output = io.StringIO()
        with patch('sys.stdout', new=captured_output):
            replay_match(self.log_file_path)

        output = captured_output.getvalue()
        self.assertIn("=== REPLAY: Match test_id_123 ===", output)
        self.assertIn("Timestamp: 2023-10-27T10:00:00.000", output)
        self.assertIn("Outcome: ATTACKER_WIN", output)
        self.assertIn("[Turn 1]", output)
        self.assertIn("[DEFENDER | def_0 | Reward: +0.20]", output)
        self.assertIn("Action: iptables -A INPUT -p tcp --dport 22 -j DROP", output)
        self.assertIn("[ATTACKER | att_0 | Reward: +0.10]", output)
        self.assertIn("Action: nmap -sS 10.0.0.1", output)

    @patch('sys.exit')
    def test_replay_match_file_not_found(self, mock_exit):
        captured_output = io.StringIO()
        with patch('sys.stdout', new=captured_output):
            replay_match("nonexistent_file.json")

        output = captured_output.getvalue()
        self.assertIn("Error: Log file nonexistent_file.json not found.", output)
        mock_exit.assert_called_with(1)

    @patch('sys.exit')
    def test_replay_match_invalid_json(self, mock_exit):
        bad_json_path = os.path.join(self.temp_dir.name, "bad.json")
        with open(bad_json_path, "w") as f:
            f.write("{ invalid json")

        captured_output = io.StringIO()
        with patch('sys.stdout', new=captured_output):
            replay_match(bad_json_path)

        output = captured_output.getvalue()
        self.assertIn(f"Error: {bad_json_path} is not a valid JSON file.", output)
        mock_exit.assert_called_with(1)

if __name__ == '__main__':
    unittest.main()
