import unittest
from unittest.mock import patch
import io
import json
import os
import sys

# Ensure src can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.replay import display_replay

class TestReplayViewer(unittest.TestCase):
    def setUp(self):
        self.mock_log_file = "test_mock_log.json"
        self.mock_data = {
            "match_id": "test_match_123",
            "outcome": "attacker_win",
            "turns": [
                {
                    "turn_number": 1,
                    "events": [
                        {
                            "role": "attacker",
                            "agent_id": "att_1",
                            "action": "nmap scan",
                            "shaped_reward": 0.5
                        },
                        {
                            "role": "defender",
                            "agent_id": "def_1",
                            "action": "iptables drop",
                            "shaped_reward": 0.2
                        }
                    ]
                }
            ]
        }
        with open(self.mock_log_file, "w") as f:
            json.dump(self.mock_data, f)

    def tearDown(self):
        if os.path.exists(self.mock_log_file):
            os.remove(self.mock_log_file)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_display_replay(self, mock_stdout):
        display_replay(self.mock_log_file)
        output = mock_stdout.getvalue()

        self.assertIn("--- REPLAY FOR MATCH test_match_123 ---", output)
        self.assertIn("Outcome: ATTACKER_WIN", output)
        self.assertIn("=== TURN 1 ===", output)
        self.assertIn("[att_1 (ATTACKER) | Reward: 0.50]:\nnmap scan", output)
        self.assertIn("[def_1 (DEFENDER) | Reward: 0.20]:\niptables drop", output)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_display_replay_file_not_found(self, mock_stdout):
        with self.assertRaises(SystemExit) as cm:
            display_replay("non_existent_file.json")
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Error: Log file 'non_existent_file.json' not found.", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_display_replay_invalid_json(self, mock_stdout):
        invalid_json_file = "invalid.json"
        with open(invalid_json_file, "w") as f:
            f.write("{invalid_json: true")

        with self.assertRaises(SystemExit) as cm:
            display_replay(invalid_json_file)
        self.assertEqual(cm.exception.code, 1)
        self.assertIn(f"Error: Log file '{invalid_json_file}' is not valid JSON.", mock_stdout.getvalue())

        os.remove(invalid_json_file)


if __name__ == "__main__":
    unittest.main()
