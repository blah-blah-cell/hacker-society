# Hacker Society

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](#)

## Overview

**Hacker Society** is an autonomous, dual-model cyber range designed for advanced AI agents. It operates as a high-fidelity testing ground where Red Team (attacker) and Blue Team (defender) models compete within isolated Docker container environments. Beyond acting as an evaluation benchmark for cybersecurity AI, Hacker Society serves as an automated data pipeline. Every action, tool call, and state change executed by the agents is systematically logged to generate high-quality dataset trajectories (e.g., ShareGPT format). These datasets are instrumental for Reinforcement Learning (RLHF/DPO) and subsequent model fine-tuning.

## Key Features

* **Multi-Agent Scalability (N vs M):** The execution engine supports concurrent matches where multiple (N) attackers and (M) defenders operate simultaneously. Agents coordinate dynamically with their respective teams via internal communication channels to accomplish their objectives.
* **Sandboxed Environments:** Agents execute bash commands via strict tool-calling interfaces inside robust, isolated Docker networks. The simulated environment is realistic, featuring a public-facing vulnerable container and a hidden, internal database container holding a secret flag.
* **Vulnerability Selection:** A built-in Terminal User Interface (TUI) allows users to select and expose various system-level vulnerabilities (e.g., Anonymous FTP, Weak SSH, Open Redis, Misconfigured NFS) on the defender's container to test specific agent capabilities.
* **Agent Memory:** The system incorporates long-term persistent memory for the agents. Match experiences are summarized, stored in a JSON store (with vector database integration capability), and injected into system prompts for subsequent matches, enabling strategic evolution over time.
* **Local LLM Support:** Fully compatible with local, open-source models using the standard OpenAI client API interface. Connect seamlessly with inference servers like Ollama, vLLM, or LM Studio.
* **Dataset Export Pipeline:** Matches automatically export detailed interaction logs. These logs capture successful and failed attack/defense paths, assigning numerical rewards (+1.0 for a win, -1.0 for a loss) to facilitate direct integration with fine-tuning frameworks such as Unsloth or Hugging Face `trl`.
* **Distributed Scaffolding:** Initial structural scaffolding is included to support future scaling and migration to distributed orchestration systems like Docker Swarm or Kubernetes.

## System Architecture

The Hacker Society environment simulates a realistic network penetration testing scenario:

1.  **Attacker Node:** Deployed on the public network, tasked with breaching the defender's perimeter.
2.  **Public Defender (Exposed Container):** Resides on the public network and hosts vulnerable services. The Blue Team must secure this container, while the Red Team attempts to exploit it to gain a foothold.
3.  **Internal Database (Hidden Container):** Resides on an isolated internal network, accessible only from the Defender container. It houses the secret flag.

**The objective:** The Attacker must exploit the Public Defender, pivot through the internal network, and exfiltrate the flag from the Internal Database.

## Prerequisites & Installation

To run Hacker Society, you need the following installed:

*   **Python:** Version 3.10 or higher.
*   **Docker:** Docker engine must be installed and the daemon running (e.g., `sudo dockerd`).
*   **LLM Endpoint:** An accessible OpenAI-compatible API endpoint (either OpenAI's API or a local server like Ollama/vLLM).

**Setup:**

1.  Clone the repository and navigate to the project directory.
2.  Install the required Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage Instructions

To initiate a match, use the primary orchestration engine. You can specify the number of attackers and defenders, as well as the target LLM.

**Basic Usage (Default OpenAI models):**

Ensure your API key is set:
```bash
export LLM_API_KEY="sk-..."
```
Run the match with specific team sizes:
```bash
PYTHONPATH=. python3 src/main.py --attackers 2 --defenders 2
```
*Upon running, a TUI will prompt you to select the vulnerability scenario for the match.*

**Using Local Models (e.g., Ollama or vLLM):**

You can override the model and base URL to point to your local inference server:
```bash
PYTHONPATH=. python3 src/main.py --attackers 2 --defenders 2 --model "llama3" --base-url "http://localhost:11434/v1"
```

## RL & Fine-Tuning Pipeline

Hacker Society is designed from the ground up to generate training data. As matches execute, detailed logs encompassing agent prompts, environmental states, bash commands, tool outputs, and match outcomes are continuously written to the `logs/` directory.

A dedicated export pipeline processes these logs to generate datasets in widely accepted formats (like ShareGPT JSONL). These datasets distinctly separate preferred trajectories (winning actions) from rejected paths (losing actions) based on the assigned reward (+1.0 / -1.0), making them plug-and-play ready for RLHF, DPO, and supervised fine-tuning using tools like Unsloth or Hugging Face `trl`.

## Testing locally without external LLMs/Containers

If you are developing the framework or need to test the pipeline without incurring external API costs or Docker Hub pull limits, you can utilize the built-in mock server.

1.  **Mock LLM Server:** We provide a lightweight HTTP mock server (`src/mock_llm_server.py`) that implements an OpenAI-compatible `/v1/chat/completions` endpoint, returning pre-programmed responses.
2.  **Bypass Docker:** Set the `MOCK_DOCKER_NO_CONTAINERS=1` environment variable to skip actual Docker container builds during local testing.

Example local test run:
```bash
MOCK_DOCKER_NO_CONTAINERS=1 PYTHONPATH=. python3 src/main.py --attackers 1 --defenders 1
```

## Roadmap

Hacker Society is actively under development across multiple phases:

*   **Phase 1:** Core environment and 1v1 agent combat (Completed)
*   **Phase 2:** Multi-container network pivoting and vulnerability scenarios (Completed)
*   **Phase 3:** Multi-Agent Scalability (N vs M) and internal communication (Current Focus)
*   **Phase 4:** Distributed orchestration scaffolding (Swarm/Kubernetes)
*   **Phase 5:** Automated continuous RL fine-tuning loops

*(See the `ROADMAP.md` file for full details).*

## Contributing & License

Contributions from the open-source community, AI researchers, and cybersecurity professionals are highly encouraged! Feel free to submit pull requests or open issues for bugs, feature requests, or new vulnerability scenarios.

This project is licensed under the **MIT License**. See the LICENSE file for details.
