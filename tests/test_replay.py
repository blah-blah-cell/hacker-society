import unittest
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.replay import load_log, print_turn

class TestReplay(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.json')
        self.valid_data = {
            "match_id": "test_123",
            "outcome": "attacker_win",
            "turns": [
                {
                    "turn_number": 1,
                    "events": [
                        {
                            "role": "attacker",
                            "agent_id": "attacker_0",
                            "action": "test action",
                            "shaped_reward": 1.0
                        }
                    ]
                }
            ]
        }
        json.dump(self.valid_data, self.temp_file)
        self.temp_file.close()

    def tearDown(self):
        os.remove(self.temp_file.name)

    def test_load_log_valid(self):
        data = load_log(self.temp_file.name)
        self.assertEqual(data["match_id"], "test_123")
        self.assertEqual(data["outcome"], "attacker_win")
        self.assertEqual(len(data["turns"]), 1)

    def test_load_log_missing(self):
        with self.assertRaises(FileNotFoundError):
            load_log("nonexistent_file.json")

if __name__ == '__main__':
    unittest.main()
