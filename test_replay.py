import os
import json
import subprocess
import unittest

class TestReplayViewer(unittest.TestCase):
    def setUp(self):
        self.mock_log_data = {
            "match_id": "test_1234",
            "timestamp": "2023-10-27T10:00:00",
            "secret_flag_sha256": "fakehash",
            "outcome": "attacker_win",
            "rewards": {"attacker": 1.0, "defender": -1.0},
            "shaped_rewards": {"attacker": 0.5, "defender": 0.2},
            "turns": [
                {
                    "turn_number": 1,
                    "events": [
                        {"role": "defender", "agent_id": "def_1", "action": "iptables -A INPUT -j DROP", "shaped_reward": 0.2},
                        {"role": "attacker", "agent_id": "att_1", "action": "nmap -p- 10.0.0.2", "shaped_reward": 0.1}
                    ]
                },
                {
                    "turn_number": 2,
                    "events": [
                        {"role": "attacker", "agent_id": "att_1", "action": "cat /tmp/flag.txt EXFILTRATED fake_flag", "shaped_reward": 0.4}
                    ]
                }
            ]
        }

        self.test_log_file = "test_match_log.json"
        with open(self.test_log_file, "w") as f:
            json.dump(self.mock_log_data, f)

    def tearDown(self):
        if os.path.exists(self.test_log_file):
            os.remove(self.test_log_file)

    def test_replay_script_output(self):
        import sys
        result = subprocess.run([sys.executable, "src/replay.py", self.test_log_file], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, f"Script failed with error: {result.stderr}")

        output = result.stdout
        self.assertIn("HACKER SOCIETY - MATCH REPLAY VIEWER", output)
        self.assertIn("Match ID: test_1234", output)
        self.assertIn("Outcome: ATTACKER_WIN", output)
        self.assertIn("--- TURN 1 ---", output)
        self.assertIn("[DEFENDER - def_1] (Reward: +0.20) -> iptables -A INPUT -j DROP", output)
        self.assertIn("[ATTACKER - att_1] (Reward: +0.10) -> nmap -p- 10.0.0.2", output)
        self.assertIn("--- TURN 2 ---", output)
        self.assertIn("[ATTACKER - att_1] (Reward: +0.40) -> cat /tmp/flag.txt EXFILTRATED fake_flag", output)
        self.assertIn("REPLAY COMPLETE", output)

if __name__ == "__main__":
    unittest.main()
