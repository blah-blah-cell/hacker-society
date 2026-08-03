import unittest
import tempfile
import json
import os
import sys
import subprocess

class TestReplayViewer(unittest.TestCase):
    def setUp(self):
        # Create a temporary file with mock log data
        self.fd, self.temp_log_path = tempfile.mkstemp(suffix=".json")
        mock_data = {
            "match_id": "test_match",
            "outcome": "attacker_win",
            "rewards": {"attacker": 1.0, "defender": -1.0},
            "turns": [
                {
                    "turn_number": 1,
                    "events": [
                        {"agent_id": "defender_0", "role": "defender", "action": "ufw enable"},
                        {"agent_id": "attacker_0", "role": "attacker", "action": "nmap scan"}
                    ]
                }
            ]
        }
        with os.fdopen(self.fd, 'w') as f:
            json.dump(mock_data, f)

        self.replay_script_path = os.path.join(os.path.dirname(__file__), "..", "src", "replay.py")

    def tearDown(self):
        # Remove the temporary file
        os.remove(self.temp_log_path)

    def test_replay_viewer_success(self):
        # Use sys.executable to run the test against the script
        result = subprocess.run(
            [sys.executable, self.replay_script_path, self.temp_log_path],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Match ID: test_match", result.stdout)
        self.assertIn("Outcome: attacker_win", result.stdout)
        self.assertIn("Turn 1", result.stdout)
        self.assertIn("[defender_0 (DEFENDER)]", result.stdout)
        self.assertIn("ufw enable", result.stdout)
        self.assertIn("[attacker_0 (ATTACKER)]", result.stdout)
        self.assertIn("nmap scan", result.stdout)

    def test_replay_viewer_file_not_found(self):
        result = subprocess.run(
            [sys.executable, self.replay_script_path, "non_existent_file.json"],
            capture_output=True,
            text=True
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Error: Log file not found", result.stdout)

if __name__ == "__main__":
    unittest.main()
