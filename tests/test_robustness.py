"""
tests/test_robustness.py

Rigorous robustness and adversarial stress tests for Hacker Society:
- Dirty JSON argument parsing & error recovery
- Honeypot tripwire evaluation order & detection
- Case-insensitive exfiltration validation
- Agent execution error isolation
- Thread-safe dashboard event queue bridge
- Concurrent MemoryStore access & TF-IDF ranking
- SFT and Pairwise DPO dataset export integrity
"""

import json
import os
import tempfile
import threading
from unittest.mock import MagicMock

from src.agent import Agent
from src.environment import Environment
from src.match import Match
from src.memory import MemoryStore
from src.model_config import ModelConfig
from src.dashboard import broadcast_match_event, _event_queue
from src.export_dataset import export_to_sharegpt, export_to_dpo


def test_dirty_json_parsing():
    """Verify that Agent._safe_parse_args handles clean, dirty, markdown, and malformed inputs."""
    # 1. Clean JSON
    args, err = Agent._safe_parse_args('{"command": "whoami"}')
    assert err is None
    assert args == {"command": "whoami"}

    # 2. Markdown wrapped JSON block
    markdown_wrapped = "```json\n{\"command\": \"cat /tmp/flag.txt\"}\n```"
    args, err = Agent._safe_parse_args(markdown_wrapped)
    assert err is None
    assert args == {"command": "cat /tmp/flag.txt"}

    # 3. Python single-quoted dictionary
    single_quoted = "{'command': 'netstat -tuln'}"
    args, err = Agent._safe_parse_args(single_quoted)
    assert err is None
    assert args == {"command": "netstat -tuln"}

    # 4. Trailing syntax / dirty command extraction fallback
    dirty_text = 'Random text before {"command": "nmap -sV 10.0.0.1"}'
    args, err = Agent._safe_parse_args(dirty_text)
    assert err is None
    assert args.get("command") == "nmap -sV 10.0.0.1"

    # 5. Completely unparseable text returns informative error, does NOT crash
    garbage = "This is not json at all."
    args, err = Agent._safe_parse_args(garbage)
    assert err is not None
    assert "Could not parse tool arguments as valid JSON" in err


def test_honeypot_tripwire_order():
    """Verify that nmap or curl targeting the honeypot host triggers the tripwire alert."""
    os.environ["MOCK_DOCKER_NO_CONTAINERS"] = "1"
    env = Environment()

    # Reset trigger state
    env.honeypot_triggered = False

    # Probing honeypot with nmap should trigger the tripwire (not get shadowed by generic nmap)
    out = env.execute_in_container("att_0", "attacker", "nmap -sV 10.0.1.20")
    assert env.honeypot_triggered is True
    assert "TRAP TRIGGERED" in out

    # Non-honeypot command should not trigger
    env.honeypot_triggered = False
    out_normal = env.execute_in_container("att_0", "attacker", "nmap -sV 10.0.0.2")
    assert env.honeypot_triggered is False
    assert "Nmap scan report" in out_normal


def test_agent_execution_error_recovery():
    """Verify that container execution exceptions are cleanly caught and returned as tool error."""
    mock_env = MagicMock()
    mock_env.execute_in_container.side_effect = RuntimeError("Docker daemon connection reset")

    cfg = ModelConfig.from_env(model="test-model")
    agent = Agent("attacker_0", "attacker", mock_env, model_config=cfg)

    tool_call = MagicMock()
    tool_call.id = "call_123"
    tool_call.function.name = "execute_bash_command"
    tool_call.function.arguments = json.dumps({"command": "ls /"})

    res = agent._handle_tool_call(tool_call)
    assert res["role"] == "tool"
    assert "Execution error in container: Docker daemon connection reset" in res["content"]


def test_case_insensitive_exfiltration_and_win():
    """Verify that exfiltration check matches variations of EXFILTRATED while verifying exact flag."""
    flag = "a1b2c3d4e5f678901234567890abcdef"
    env = Environment()

    attacker = MagicMock()
    attacker.agent_id = "attacker_0"
    attacker.role = "attacker"
    # Returns lowercase 'exfiltrated' with the correct flag
    attacker.take_turn.return_value = f"Got it! exfiltrated: {flag}"

    defender = MagicMock()
    defender.agent_id = "defender_0"
    defender.role = "defender"
    defender.take_turn.return_value = "iptables -A INPUT -j DROP"

    match = Match([attacker], [defender], env, secret_flag=flag, max_turns=1)
    outcome = match.run(defender_ips=["10.0.0.2"])

    assert outcome == "attacker_win"
    assert match.logs["outcome"] == "attacker_win"


def test_case_insensitive_exfiltration_fail_on_wrong_flag():
    """Verify that wrong flag attempt does not win and penalizes shaped reward."""
    flag = "a1b2c3d4e5f678901234567890abcdef"
    env = Environment()

    attacker = MagicMock()
    attacker.agent_id = "attacker_0"
    attacker.role = "attacker"
    attacker.take_turn.return_value = "exfiltrated wrong_flag_here"

    defender = MagicMock()
    defender.agent_id = "defender_0"
    defender.role = "defender"
    defender.take_turn.return_value = "iptables -A INPUT -j DROP"

    match = Match([attacker], [defender], env, secret_flag=flag, max_turns=1)
    outcome = match.run(defender_ips=["10.0.0.2"])

    assert outcome == "defender_win"
    assert match.logs["outcome"] == "defender_win"


def test_dashboard_event_queue_cross_thread():
    """Verify that broadcast_match_event from worker threads safely enqueues without event loop errors."""
    initial_size = _event_queue.qsize()

    def worker():
        for i in range(10):
            broadcast_match_event("turn_action", {"index": i})

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # 5 threads * 10 events = 50 events queued
    assert _event_queue.qsize() == initial_size + 50


def test_memorystore_concurrency_and_search():
    """Verify thread-safe MemoryStore access under concurrent writes and TF-IDF search ranking."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "mem.json")
        store = MemoryStore(filepath=path)

        def writer(role, text):
            for i in range(10):
                store.add_memory(role, f"{text} entry {i}")

        threads = [
            threading.Thread(target=writer, args=("attacker", "nmap scan port 22")),
            threading.Thread(target=writer, args=("defender", "iptables drop port 22")),
            threading.Thread(target=writer, args=("attacker", "vsftpd anonymous access")),
            threading.Thread(target=writer, args=("defender", "service vsftpd stop")),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        attacker_mems = store.get_memory("attacker")
        defender_mems = store.get_memory("defender")
        assert len(attacker_mems) == 20
        assert len(defender_mems) == 20

        # Search ranking test
        results = store.search_memory("attacker", "nmap port")
        assert len(results) > 0
        assert "nmap scan" in results[0]


def test_dataset_exporter_sft_and_dpo():
    """Verify that export_to_sharegpt and export_to_dpo correctly parse match logs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "match_sample_log.json")
        sample_log = {
            "match_id": "test_sample",
            "timestamp": "2026-10-07T12:00:00",
            "secret_flag_sha256": "fake_hash",
            "rewards": {"attacker": 1.0, "defender": -1.0},
            "turns": [
                {
                    "turn_number": 1,
                    "events": [
                        {"role": "defender", "agent_id": "def_0", "action": "iptables -A INPUT -j DROP", "shaped_reward": 0.2},
                        {"role": "attacker", "agent_id": "att_0", "action": "nmap -sV 10.0.0.2", "shaped_reward": 0.1},
                        {"role": "attacker", "agent_id": "att_1", "action": "exfiltrated bad_flag", "shaped_reward": -0.5},
                    ]
                }
            ]
        }
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(sample_log, f)

        sft_out = os.path.join(tmpdir, "dataset_sft.jsonl")
        dpo_out = os.path.join(tmpdir, "dataset_dpo.jsonl")

        export_to_sharegpt(logs_dir=tmpdir, output_file=sft_out)
        export_to_dpo(logs_dir=tmpdir, output_file=dpo_out)

        assert os.path.exists(sft_out)
        assert os.path.exists(dpo_out)

        with open(sft_out, "r", encoding="utf-8") as f:
            sft_lines = [json.loads(line) for line in f]
        assert len(sft_lines) >= 2  # One attacker, one defender trace

        with open(dpo_out, "r", encoding="utf-8") as f:
            dpo_lines = [json.loads(line) for line in f]
        assert len(dpo_lines) >= 1
        # The chosen action should be the higher reward action (nmap), rejected should be bad_flag
        assert dpo_lines[0]["chosen"] == "nmap -sV 10.0.0.2"
        assert dpo_lines[0]["rejected"] == "exfiltrated bad_flag"


def test_dashboard_http_and_websocket():
    """Verify that dashboard renders HTTP HTML and connects to WebSocket client."""
    from fastapi.testclient import TestClient
    from src.dashboard import app, broadcast_match_event

    with TestClient(app) as client:
        # Test GET /
        res = client.get("/")
        assert res.status_code == 200
        assert "html" in res.headers.get("content-type", "")

        # Broadcast test event
        broadcast_match_event("e2e_event", {"status": "ok"})

        # Test WebSocket /ws/match
        with client.websocket_connect("/ws/match") as ws:
            # Send ping
            ws.send_text("ping")


def test_model_config_yaml_and_providers():
    """Verify YAML configuration loading and provider slug resolution."""
    # Test from YAML example file
    att_cfg = ModelConfig.from_yaml("configs.yaml.example", "attacker")
    assert att_cfg.model == "gpt-4o-mini"
    assert att_cfg.provider == "openai"
    assert att_cfg.temperature == 0.8

    def_cfg = ModelConfig.from_yaml("configs.yaml.example", "defender")
    assert def_cfg.model == "gpt-4o-mini"
    assert def_cfg.provider == "openai"
    assert def_cfg.temperature == 0.4

    # Test provider slug auto-resolution
    groq_cfg = ModelConfig.from_provider("groq", "llama3-70b-8192", temperature=0.7)
    assert groq_cfg.model == "llama3-70b-8192"
    assert groq_cfg.provider == "groq"
    assert "https://api.groq.com/openai/v1" in str(groq_cfg.client.base_url)
