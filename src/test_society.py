import os
import pytest
from src.environment import Environment
from src.agent import Agent
from src.model_config import ModelConfig

def test_environment_mock_docker_init(monkeypatch):
    monkeypatch.setenv("MOCK_DOCKER_NO_CONTAINERS", "1")
    env = Environment()
    assert env.client is None
    res = env.execute_in_container("attacker_0", "attacker", "cat /tmp/flag.txt")
    assert res == "0123456789abcdef0123456789abcdef"

def test_agent_context_pinning(monkeypatch):
    monkeypatch.setenv("MOCK_DOCKER_NO_CONTAINERS", "1")
    env = Environment()
    cfg = ModelConfig(model="mock-model", base_url="http://localhost:8000/v1", api_key="dummy")
    agent = Agent(agent_id="attacker_0", role="attacker", environment=env, model_config=cfg, system_prompt="SYSTEM PROMPT")
    
    agent.add_message("user", "INITIAL OBJECTIVE")
    for i in range(40):
        agent.add_message("user", f"Follow up message {i}")
        
    pruned = agent._pruned_messages()
    assert pruned[0]["content"] == "SYSTEM PROMPT"
    assert pruned[1]["content"] == "INITIAL OBJECTIVE"
    assert len(pruned) <= agent.HISTORY_WINDOW + 2
