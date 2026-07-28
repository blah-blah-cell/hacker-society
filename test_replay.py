import unittest
from unittest.mock import patch
import sys
import io
import json
import os
import tempfile
import importlib

import src.replay as replay

class TestReplay(unittest.TestCase):
    def setUp(self):
        self.mock_log = {
            "match_id": "test_id_123",
            "outcome": "attacker_win",
            "secret_flag_sha256": "fake_hash",
            "turns": [
                {
                    "turn_number": 1,
                    "events": [
                        {
                            "role": "defender",
                            "agent_id": "def_0",
                            "action": "block port 21",
                            "shaped_reward": 0.2
                        },
                        {
                            "role": "attacker",
                            "agent_id": "att_0",
                            "action": "nmap scan",
                            "shaped_reward": 0.1
                        }
                    ]
                }
            ]
        }

        self.temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json')
        json.dump(self.mock_log, self.temp_file)
        self.temp_file.close()

    def tearDown(self):
        os.remove(self.temp_file.name)

    @patch('builtins.input', side_effect=['']) # Mock pressing Enter
    @patch('sys.argv', new_callable=lambda: ['replay.py'])
    def test_replay_valid_log(self, mock_argv, mock_input):
        mock_argv.append(self.temp_file.name)

        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            replay.main()
        finally:
            sys.stdout = sys.__stdout__

        output = captured_output.getvalue()

        self.assertIn("--- MATCH REPLAY STARTING: test_id_123 ---", output)
        self.assertIn("Outcome: attacker_win", output)
        self.assertIn("=== TURN 1 ===", output)
        self.assertIn("[DEF_0 (DEFENDER)]", output)
        self.assertIn("Reward: +0.20", output)
        self.assertIn("Action: block port 21", output)
        self.assertIn("[ATT_0 (ATTACKER)]", output)
        self.assertIn("Reward: +0.10", output)
        self.assertIn("Action: nmap scan", output)
        self.assertIn("--- MATCH REPLAY FINISHED ---", output)

    @patch('sys.argv', new_callable=lambda: ['replay.py', 'nonexistent_file.json'])
    def test_replay_file_not_found(self, mock_argv):
        captured_output = io.StringIO()
        sys.stdout = captured_output

        with self.assertRaises(SystemExit) as cm:
            replay.main()

        sys.stdout = sys.__stdout__
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Error: Log file not found", captured_output.getvalue())

    def test_replay_invalid_json(self):
        bad_temp = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json')
        bad_temp.write("{bad json")
        bad_temp.close()

        with patch('sys.argv', ['replay.py', bad_temp.name]):
            captured_output = io.StringIO()
            sys.stdout = captured_output

            with self.assertRaises(SystemExit) as cm:
                replay.main()

            sys.stdout = sys.__stdout__
            self.assertEqual(cm.exception.code, 1)
            self.assertIn("Error: Could not parse JSON", captured_output.getvalue())

        os.remove(bad_temp.name)

if __name__ == '__main__':
    unittest.main()
