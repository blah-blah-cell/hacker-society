# Hacker Society

An autonomous dual-model cyber range where one local AI acts as the Red Team (Attacker) and another local AI acts as the Blue Team (Defender). The agents are deployed into sandboxed Docker containers to battle for control of vulnerable services. Over time, all matches are logged to provide high-quality datasets for Reinforcement Learning (RL) and model fine-tuning.

## Architecture

As of **Phase 2**, Hacker Society utilizes a multi-container, multi-network architecture to simulate realistic network pivoting:

1. **Public Network:** Contains the Attacker container and the exposed, vulnerable Defender container.
2. **Internal Network:** An isolated network containing the Defender container and a hidden Database (DB) container.
3. **The Goal:** The Attacker must exploit a vulnerable service on the public Defender container to gain a foothold, then pivot into the internal network to exfiltrate the secret flag hidden on the DB container. The Defender must patch the vulnerabilities and secure the environment before the Attacker succeeds.

## System-Level Vulnerabilities

Hacker Society supports 21 selectable system-level vulnerabilities and misconfigurations for the Defender's exposed container. When you start a match, you will be prompted to select a scenario via the Terminal User Interface (TUI). Options include:

- Anonymous FTP Server
- Weak SSH Credentials
- Open Redis / Memcached
- Cleartext Telnet
- Misconfigured NFS
- Exposed Docker Socket
- ... and a "Hard Mode" featuring a secure container requiring zero-days or advanced local privilege escalation!

## Requirements

- Python 3.10+
- Docker installed and the daemon running (`sudo dockerd`).

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure your LLM:
   If you want to use OpenAI (default `gpt-4o-mini`), set your API key:
   ```bash
   export LLM_API_KEY="sk-..."
   ```
   If you want to use a local LLM (like Ollama or vLLM), you can pass the base URL to the CLI. Ensure the server supports standard OpenAI tool calling.

## Running a Match

To start a match, run the orchestration engine:

```bash
PYTHONPATH=. python3 src/main.py
```
You will be prompted to select one of the 21 vulnerability scenarios, after which the Docker environment will build and the AI battle will commence!

To configure the turn count or use a local model via a custom endpoint:

```bash
PYTHONPATH=. python3 src/main.py --turns 10 --model "llama3" --base-url "http://localhost:11434/v1"
```

## Logs & Datasets

After each match, full state logs, agent prompts, tool calls, and outputs are saved to the `logs/` directory. These logs will be utilized in future phases to automate Reinforcement Learning from Human Feedback (RLHF) and Direct Preference Optimization (DPO) pipelines.

See `ROADMAP.md` for details on future plans and `AGENTS.md` for AI agent guidelines!
