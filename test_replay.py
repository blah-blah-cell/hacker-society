import json
import os
import subprocess
import unittest


class TestReplay(unittest.TestCase):
    def setUp(self):
        self.test_log_path = "test_match_log.json"

        # Create a mock log file
        self.mock_log_data = {
            "match_id": "mock_match_123",
            "outcome": "attacker_win",
            "rewards": {
                "attacker": 1.0,
                "defender": -1.0
            },
            "shaped_rewards": {
                "attacker": 1.3,
                "defender": -0.8
            },
            "turns": [
                {
                    "turn_number": 1,
                    "events": [
                        {
                            "role": "defender",
                            "agent_id": "defender_0",
                            "action": "iptables -A INPUT -p tcp --dport 21 -j DROP",
                            "shaped_reward": 0.2
                        },
                        {
                            "role": "attacker",
                            "agent_id": "attacker_0",
                            "action": "nmap -sV 10.0.0.0/24",
                            "shaped_reward": 0.1
                        }
                    ]
                }
            ]
        }

        with open(self.test_log_path, 'w') as f:
            json.dump(self.mock_log_data, f)

    def tearDown(self):
        if os.path.exists(self.test_log_path):
            os.remove(self.test_log_path)

    def test_replay_script_output(self):
        result = subprocess.run(
            ["python3", "src/replay.py", self.test_log_path],
            capture_output=True,
            text=True
        )

        self.assertEqual(result.returncode, 0)
        output = result.stdout

        self.assertIn("Match ID: mock_match_123", output)
        self.assertIn("Outcome: ATTACKER_WIN", output)
        self.assertIn("Final Rewards - Attacker: 1.0 | Defender: -1.0", output)
        self.assertIn("Shaped Rewards - Attacker: 1.30 | Defender: -0.80", output)
        self.assertIn("--- Turn 1 ---", output)
        self.assertIn("[DEFENDER - defender_0]", output)
        self.assertIn("Action: iptables -A INPUT -p tcp --dport 21 -j DROP", output)
        self.assertIn("[ATTACKER - attacker_0]", output)
        self.assertIn("Action: nmap -sV 10.0.0.0/24", output)


if __name__ == "__main__":
    unittest.main()
