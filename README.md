# Hacker Society

An autonomous dual-model cyber range where one local AI acts as the red-team brain and another local AI acts as the blue-team brain. They run in isolated sandboxed containers to battle for control of a vulnerable server. Over time, matches are logged to provide datasets for Reinforcement Learning (RL) and fine-tuning.

## Phase 1: Core Orchestration

This phase implements the orchestration engine:
1. Building and managing isolated Docker environments.
2. An Agent framework connecting standard/local LLMs to bash execution tools.
3. A Match loop to coordinate Red and Blue turns, log output, and track win conditions.

## Requirements
- Python 3.10+
- Docker installed and the daemon running (`sudo dockerd`).

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure your LLM.
   If you want to use OpenAI (default `gpt-4o-mini`), set your API key:
   ```bash
   export LLM_API_KEY="sk-..."
   ```
   If you want to use a local LLM (like Ollama or vLLM), you can pass the base URL to the CLI. Ensure the server supports standard OpenAI tool calling.

## Running a Match

To start a match with the default parameters (5 turns):

```bash
PYTHONPATH=. python3 src/main.py
```

To use a local model via a custom endpoint:

```bash
PYTHONPATH=. python3 src/main.py --turns 10 --model "llama3" --base-url "http://localhost:11434/v1"
```

## Logs

After each match, full state logs and tool calls are saved to the `logs/` directory for future fine-tuning pipelines. See `ROADMAP.md` for details on future plans.
