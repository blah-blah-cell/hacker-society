import unittest
import subprocess
import json
import os
import sys

class TestReplayViewer(unittest.TestCase):
    def setUp(self):
        self.test_log_path = "test_match_log.json"
        self.test_data = {
            "match_id": "test1234",
            "timestamp": "2023-10-27T10:00:00",
            "outcome": "attacker_win",
            "turns": [
                {
                    "turn_number": 1,
                    "events": [
                        {
                            "agent_id": "defender_0",
                            "role": "defender",
                            "action": "enabled ufw"
                        },
                        {
                            "agent_id": "attacker_0",
                            "role": "attacker",
                            "action": "EXFILTRATED 1234abcd"
                        }
                    ]
                }
            ],
            "rewards": {
                "attacker": 1.0,
                "defender": -1.0
            }
        }

        with open(self.test_log_path, "w") as f:
            json.dump(self.test_data, f)

    def tearDown(self):
        if os.path.exists(self.test_log_path):
            os.remove(self.test_log_path)

    def test_replay_output(self):
        result = subprocess.run(
            [sys.executable, "src/replay.py", self.test_log_path],
            capture_output=True,
            text=True
        )

        self.assertEqual(result.returncode, 0)
        output = result.stdout

        # Verify essential parts of output
        self.assertIn("--- MATCH REPLAY: test1234 ---", output)
        self.assertIn("Outcome: attacker_win", output)
        self.assertIn("=== TURN 1 ===", output)
        self.assertIn("[DEFENDER_0] (defender):", output)
        self.assertIn("enabled ufw", output)
        self.assertIn("[ATTACKER_0] (attacker):", output)
        self.assertIn("EXFILTRATED 1234abcd", output)
        self.assertIn("--- REPLAY COMPLETE ---", output)

if __name__ == "__main__":
    unittest.main()
