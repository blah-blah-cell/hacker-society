"""
tests/test_actual_e2e.py

Full end-to-end integration test of the entire Hacker Society pipeline:
1. Live local OpenAI-compatible inference server on ephemeral port.
2. 2-versus-2 multi-agent autonomous match execution with tool calling.
3. Secret flag validation and security verification.
4. Log generation and atomic persistence.
5. Match replay engine execution on generated telemetry.
6. SFT (ShareGPT) and DPO preference dataset generation.
7. Fine-tuning training loop simulation on exported dataset.
"""

import os
import sys
import time
import socket
import threading
import tempfile
import pytest

from src.mock_llm_server import ReusableTCPServer, MockLLMHandler
from src.environment import Environment
from src.agent import Agent
from src.match import Match
from src.memory import MemoryStore
from src.model_config import ModelConfig
from src.replay import replay_match
from src.export_dataset import export_to_sharegpt, export_to_dpo
from src.fine_tune import run_fine_tuning


def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def mock_server():
    port = get_free_port()
    server = ReusableTCPServer(("127.0.0.1", port), MockLLMHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.5)
    yield f"http://127.0.0.1:{port}/v1"
    server.shutdown()
    server.server_close()


def test_full_pipeline_e2e(mock_server):
    """Run full cyber range match -> replay -> export dataset -> fine-tune pipeline."""
    os.environ["MOCK_DOCKER_NO_CONTAINERS"] = "1"

    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Setup Environment & Models
        env = Environment()
        secret_flag = "deadbeef12345678deadbeef12345678"
        mem_path = os.path.join(tmpdir, "memory.json")
        memory_store = MemoryStore(filepath=mem_path)

        cfg = ModelConfig.from_url(base_url=mock_server, model="mock-model")

        # 2. Setup 2 Attackers vs 2 Defenders
        team_channel_att = []
        team_channel_def = []

        attackers = [
            Agent(
                agent_id=f"attacker_{i}",
                role="attacker",
                environment=env,
                model_config=cfg,
                system_prompt="You are a red team penetration tester.",
                team_channel=team_channel_att
            )
            for i in range(2)
        ]
        defenders = [
            Agent(
                agent_id=f"defender_{i}",
                role="defender",
                environment=env,
                model_config=cfg,
                system_prompt="You are a blue team security defender.",
                team_channel=team_channel_def
            )
            for i in range(2)
        ]

        # 3. Initialize & Run Match
        match = Match(
            attackers=attackers,
            defenders=defenders,
            environment=env,
            secret_flag=secret_flag,
            max_turns=2,
            memory_store=memory_store
        )
        # Point log directory to tempdir
        match.log_file = os.path.join(tmpdir, f"match_{match.match_id}_log.json")

        outcome = match.run(defender_ips=["10.0.0.2", "10.0.0.3"])

        # 4. Verify Match Execution Outcome
        assert outcome in ("attacker_win", "defender_win")
        assert os.path.exists(match.log_file)
        assert len(match.logs["turns"]) == 2

        # Verify Plaintext Flag is never present in log
        with open(match.log_file, "r", encoding="utf-8") as f:
            log_content = f.read()
            assert secret_flag not in log_content
            assert "secret_flag_sha256" in log_content

        # 5. Verify Match Replay Engine
        replay_match(match.log_file)

        # 6. Verify Dataset Export (SFT and DPO)
        sft_path = os.path.join(tmpdir, "dataset_sft.jsonl")
        dpo_path = os.path.join(tmpdir, "dataset_dpo.jsonl")

        export_to_sharegpt(logs_dir=tmpdir, output_file=sft_path)
        export_to_dpo(logs_dir=tmpdir, output_file=dpo_path)

        assert os.path.exists(sft_path)
        assert os.path.exists(dpo_path)

        # 7. Verify Fine-Tune Pipeline
        output_model_dir = os.path.join(tmpdir, "ft_output")
        run_fine_tuning(dataset_path=dpo_path, model_name="mock-model", output_dir=output_model_dir)
        assert os.path.exists(os.path.join(output_model_dir, "adapter_config.json"))
