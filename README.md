# Hacker Society

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Docker Required](https://img.shields.io/badge/docker-required-blue)](#)

> **Autonomous AI Cyber Range** — Red-team LLM agents attack, blue-team LLM agents defend, all inside isolated Docker networks. Every match generates structured RL training data.

---

## Overview

Hacker Society is a dual-agent autonomous cyber range where **Red Team (attacker)** and **Blue Team (defender)** LLM agents compete inside sandboxed Docker environments. Beyond pure benchmarking it acts as an automated data pipeline: every action, tool call, and shaped reward is logged to JSONL and exported as a DPO/RLHF-ready dataset for fine-tuning local models.

---

## Key Features

| Feature | Detail |
|---|---|
| **N-vs-M Multi-Agent** | Any number of attacker and defender agents, all running concurrently via `ThreadPoolExecutor` |
| **Sandboxed Docker Networks** | Agents execute bash inside isolated containers — one public vulnerable container, one hidden internal DB |
| **21 Vulnerability Scenarios** | FTP, SSH, Redis, SMB, VNC, Telnet, NFS, Elasticsearch, Jenkins, etcd, and more |
| **Shaped Reward Signals** | Per-action partial rewards (recon, foothold, pivot, hardening) on top of the binary match outcome |
| **Persistent Memory** | Match summaries stored in JSON, injected into future system prompts; keyword + score-ranked search |
| **Local LLM / Multi-GPU** | Works with Ollama, vLLM, LM Studio — multi-GPU tensor parallelism supported via vLLM |
| **RL / Fine-Tune Pipeline** | Export to ShareGPT JSONL → DPO via Unsloth or HuggingFace `trl` |
| **Mock Mode** | Full offline test run with zero Docker containers and zero API calls |

---

## Architecture

```
┌─────────────────────────── Public Docker Network ───────────────────────────┐
│                                                                              │
│   [Attacker Container(s)]  ──────►  [Defender Container(s)]                 │
│        Red Team LLM                  Blue Team LLM                          │
│        bash tool calls               bash / iptables tool calls             │
│                                              │                              │
└──────────────────────────────────────────────┼──────────────────────────────┘
                                               │ pivot (if attacker wins)
                              ┌─── Internal Network ───┐
                              │  [DB Container]         │
                              │  /tmp/flag.txt          │
                              └─────────────────────────┘
```

**Match loop:**
1. Defenders act first each turn (harden, firewall, patch)
2. Attackers act concurrently (recon, exploit, pivot)
3. Win check: attacker must output `EXFILTRATED <32-char-hex-flag>` with the **exact** flag
4. Shaped reward logged per action; binary outcome reward at match end
5. Both sides summarize → summaries written to `memory.json` for the next match

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10+ | 3.11 recommended |
| Docker | 24+ | Daemon must be running (`sudo systemctl start docker`) |
| NVIDIA Driver | 525+ | Only required for multi-GPU local inference |
| CUDA Toolkit | 12.1+ | Only required for multi-GPU local inference |
| LLM Endpoint | — | OpenAI API **or** local inference server |

---

## Installation

### 1 — Clone the repo

```bash
git clone https://github.com/blah-blah-cell/hacker-society.git
cd hacker-society
```

### 2 — Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

### 3 — Install Python dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Or install as an editable package (adds the `hacker-society` CLI command):

```bash
pip install -e .
```

### 4 — Configure environment variables

Create a `.env` file in the project root (never commit this):

```bash
# .env

# Option A: OpenAI cloud
LLM_API_KEY=sk-...

# Option B: Local inference server (overrides cloud)
# LLM_BASE_URL=http://localhost:8000/v1
# LLM_API_KEY=dummy-key-for-local
```

### 5 — Verify Docker is running

```bash
docker info          # should print server info, not an error
```

If Docker requires sudo on Linux, add your user to the docker group:

```bash
sudo usermod -aG docker $USER && newgrp docker
```

---

## Usage

### Basic run (OpenAI cloud)

```bash
python -m src.main --attackers 1 --defenders 1 --turns 5
# or if installed with pip install -e .
hacker-society --attackers 1 --defenders 1 --turns 5
```

The CLI will prompt you to select a vulnerability scenario (1–21), then the match begins.

### N-vs-M multi-agent run

```bash
python -m src.main --attackers 3 --defenders 2 --turns 10 --model gpt-4o
```

### Local model via Ollama

```bash
# Start Ollama (separate terminal)
ollama serve
ollama pull llama3

# Run match against local Llama 3
python -m src.main \
  --model llama3 \
  --base-url http://localhost:11434/v1 \
  --attackers 1 --defenders 1
```

### Local model via vLLM (single GPU)

```bash
# Start vLLM server
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Meta-Llama-3-8B-Instruct \
  --port 8000

# Run match
python -m src.main \
  --model meta-llama/Meta-Llama-3-8B-Instruct \
  --base-url http://localhost:8000/v1
```

---

## Multi-GPU Support

Hacker Society uses the standard OpenAI client and is inference-server agnostic. Multi-GPU support is handled entirely by the **inference layer** — vLLM is the recommended backend.

### vLLM Tensor Parallelism

vLLM distributes a single model across multiple GPUs with `--tensor-parallel-size`. This is the correct approach for large models (≥ 13B parameters) that do not fit on one GPU.

```bash
# 2-GPU tensor parallel (splits model layers across both GPUs)
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Meta-Llama-3-70B-Instruct \
  --tensor-parallel-size 2 \
  --port 8000
```

```bash
# 4-GPU tensor parallel (recommended for 70B+ models)
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Meta-Llama-3-70B-Instruct \
  --tensor-parallel-size 4 \
  --dtype bfloat16 \
  --port 8000
```

Then point Hacker Society at it:

```bash
python -m src.main \
  --model meta-llama/Meta-Llama-3-70B-Instruct \
  --base-url http://localhost:8000/v1 \
  --attackers 2 --defenders 2
```

### vLLM Pipeline Parallelism (multi-node)

For multi-node setups (e.g. 2 × 8 GPU nodes via Ray):

```bash
# On the head node
ray start --head

# On worker nodes
ray start --address=<head-node-ip>:6379

# Launch vLLM across all nodes
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Meta-Llama-3-70B-Instruct \
  --tensor-parallel-size 8 \
  --pipeline-parallel-size 2 \
  --port 8000
```

### GPU Assignment Reference

| Model Size | Recommended Setup | `--tensor-parallel-size` |
|---|---|---|
| 7B – 8B | 1× A100 40GB / 3090 24GB | 1 |
| 13B | 1× A100 80GB or 2× A100 40GB | 1 or 2 |
| 34B | 2× A100 80GB | 2 |
| 70B | 4× A100 80GB | 4 |
| 405B | 8× H100 80GB | 8 |

### Running Multiple Agent Models on Different GPUs

You can run **attacker** and **defender** agents against **different models** on different GPUs by launching two vLLM servers on separate ports:

```bash
# GPU 0 — attacker model
CUDA_VISIBLE_DEVICES=0 python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Meta-Llama-3-8B-Instruct \
  --port 8000

# GPU 1 — defender model
CUDA_VISIBLE_DEVICES=1 python -m vllm.entrypoints.openai.api_server \
  --model mistralai/Mistral-7B-Instruct-v0.3 \
  --port 8001
```

Then edit `src/main.py` to pass per-team base URLs when constructing agents:

```python
# In main.py — pass separate base URLs per role
attacker_base_url = os.getenv("ATTACKER_LLM_BASE_URL", os.getenv("LLM_BASE_URL"))
defender_base_url = os.getenv("DEFENDER_LLM_BASE_URL", os.getenv("LLM_BASE_URL"))
```

And add to `.env`:

```bash
ATTACKER_LLM_BASE_URL=http://localhost:8000/v1
DEFENDER_LLM_BASE_URL=http://localhost:8001/v1
```

> **Note on CUDA visibility:** vLLM respects `CUDA_VISIBLE_DEVICES`. For Docker-based deployments use `--gpus device=0` and `--gpus device=1` on separate `docker run` invocations.

---

## Mock / Offline Testing

Full test run with **zero Docker containers, zero API keys, zero cost**:

```bash
# Terminal 1 — start the mock LLM server
python -m src.mock_llm_server

# Terminal 2 — run match against mock server
MOCK_DOCKER_NO_CONTAINERS=1 python -m src.main \
  --model mock-model \
  --base-url http://localhost:8000/v1 \
  --attackers 1 --defenders 1 --turns 3
```

The mock server implements an OpenAI-compatible `/v1/chat/completions` endpoint with deterministic attacker (nmap → exploit → exfil) and defender (iptables hardening) behaviour. It correctly returns `finish_reason: "tool_calls"` with non-null `tool_calls` arrays.

---

## RL & Fine-Tuning Pipeline

Every match writes a structured JSON log to `logs/match_<id>_log.json`. The log contains:
- Full turn-by-turn event history
- Per-action shaped rewards (`shaped_rewards` field)
- Binary match outcome rewards
- `secret_flag_sha256` — the flag hash (plaintext flag is **never** logged)

### Export to JSONL dataset

```bash
python -m src.export_dataset          # writes dataset.jsonl
```

Each line in `dataset.jsonl` is a ShareGPT-format trace with a `reward` field (`+1.0` win, `-1.0` loss) — ready for DPO or RLHF.

### Fine-tune (mock pipeline — real Unsloth/HF integration WIP)

```bash
python -m src.fine_tune \
  --dataset dataset.jsonl \
  --model llama3-8b-instruct \
  --output models/ft_agent
```

> Real training integration with Unsloth + HuggingFace `trl` DPOTrainer is tracked in Phase 5 of the roadmap.

---

## Project Structure

```
hacker-society/
├── src/
│   ├── __init__.py
│   ├── main.py              # CLI entry point
│   ├── agent.py             # LLM agent (multi-round tool loop, history pruning)
│   ├── environment.py       # Docker orchestration
│   ├── match.py             # Turn engine, shaped rewards, thread safety
│   ├── memory.py            # Persistent memory store (thread-safe)
│   ├── mock_llm_server.py   # Offline OpenAI-compatible mock server
│   ├── export_dataset.py    # Log → JSONL dataset exporter
│   └── fine_tune.py         # Fine-tune pipeline scaffolding
├── docker/
│   ├── Dockerfile.attacker
│   ├── Dockerfile.defender
│   ├── Dockerfile.db
│   └── start_vuln.py        # Vulnerability setup dispatcher (21 scenarios)
├── logs/                    # Auto-created; match JSON logs written here
├── memory.json              # Persistent agent memory across matches
├── requirements.txt
├── pyproject.toml
└── .env                     # Not committed — API keys live here
```

---

## Roadmap

| Phase | Status | Description |
|---|---|---|
| 1 | ✅ Done | Core environment, 1v1 agent combat |
| 2 | ✅ Done | Multi-container pivoting, 21 vulnerability scenarios |
| 3 | ✅ Done | N-vs-M multi-agent, team communication, shaped rewards |
| 4 | 🔧 Scaffolded | Docker Swarm / Kubernetes distributed orchestration |
| 5 | 🔧 Scaffolded | Real Unsloth/HF DPO fine-tuning loop |
| 6 | 📋 Planned | Per-team model routing (attacker vs defender on separate GPUs) |
| 7 | 📋 Planned | Web UI match replay viewer |

---

## Contributing

Pull requests are welcome. For major changes open an issue first to discuss scope. New vulnerability scenarios can be added to `docker/start_vuln.py` following the existing `setup_vuln_N()` pattern.

## License

MIT — see `LICENSE`.
