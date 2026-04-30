# Hacker Society - AI Agent Guide

Welcome to the Hacker Society codebase! This document provides context and guidelines for any AI agent (like Jules) working on this repository.

## Purpose
This project is an autonomous dual-model cyber range. It orchestrates matches between an "Attacker" (Red) AI agent and a "Defender" (Blue) AI agent.
- **Red Team:** Attempts to explore the environment, find vulnerabilities, and exfiltrate a secret flag.
- **Blue Team:** Attempts to secure the environment, patch vulnerabilities, and prevent exfiltration.

## Environment & Constraints
- **Docker:** All environments are sandboxed in Docker containers. Red and Blue execute commands *inside* their respective containers. Do NOT execute untrusted AI-generated bash commands on the host machine.
- **Models:** We use local Large Language Models (LLMs) running via compatible APIs (e.g., Ollama, vLLM, LM Studio) using the standard OpenAI Python client. We must support custom base URLs.
- **Tools:** Agents interact via tool calling (e.g., executing a bash command).

## Project Structure
- `docker/`: Dockerfiles and assets for container images.
- `src/`: Python source code.
  - `environment.py`: Docker orchestration (building, networks, containers).
  - `agent.py`: LLM wrapper and tool calling logic.
  - `match.py`: The main loop orchestrating turns/time and logging.
  - `main.py`: CLI entry point (includes TUI for vulnerability selection).

## Agent Guidelines
1. Always prioritize isolation: ensure Docker networks and containers are isolated correctly (e.g., internal networks must not be accessible to the attacker directly).
2. Rely on standard Python libraries when possible to keep dependencies light.
3. Make sure error handling is robust, especially for Docker daemon connections and LLM API timeouts.
4. Keep the RL/Fine-tuning goal in mind: ensure comprehensive logging of the state, agent prompt, tool usage, and output.
