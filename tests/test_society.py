import os
import unittest
from unittest.mock import patch
from src.environment import Environment
from src.agent import Agent
from src.model_config import ModelConfig

class TestSociety(unittest.TestCase):
    @patch.dict(os.environ, {"MOCK_DOCKER_NO_CONTAINERS": "1"})
    def test_environment_mock_docker_init(self):
        env = Environment()
        self.assertIsNone(env.client)
        res = env.execute_in_container("attacker_0", "attacker", "cat /tmp/flag.txt")
        self.assertEqual(res, "0123456789abcdef0123456789abcdef")

    @patch.dict(os.environ, {"MOCK_DOCKER_NO_CONTAINERS": "1"})
    def test_agent_context_pinning(self):
        env = Environment()
        cfg = ModelConfig(model="mock-model", base_url="http://localhost:8000/v1", api_key="dummy")
        agent = Agent(agent_id="attacker_0", role="attacker", environment=env, model_config=cfg, system_prompt="SYSTEM PROMPT")

        agent.add_message("user", "INITIAL OBJECTIVE")
        for i in range(40):
            agent.add_message("user", f"Follow up message {i}")

        pruned = agent._pruned_messages()
        self.assertEqual(pruned[0]["content"], "SYSTEM PROMPT")
        self.assertEqual(pruned[1]["content"], "INITIAL OBJECTIVE")
        self.assertLessEqual(len(pruned), agent.HISTORY_WINDOW + 2)

if __name__ == '__main__':
    unittest.main()
