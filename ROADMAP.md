# Hacker Society - Roadmap

## Phase 1: Core Orchestration (Current)
- [x] Set up basic project structure and dependencies.
- [x] Create simple Dockerfiles for Attacker (kali/ubuntu with tools) and Defender (vulnerable app).
- [ ] Implement `src/environment.py` to handle Docker lifecycle (build, run, teardown).
- [ ] Implement `src/agent.py` to wrap LLMs and provide bash execution tools.
- [ ] Implement `src/match.py` to run the Red vs Blue loop.
- [ ] Implement CLI to start matches.

## Phase 2: Advanced Environment & Vulnerabilities
- Expand the Defender's environment to multiple containers (e.g., Web, DB, Internal Network).
- Introduce standard, repeatable vulnerabilities (SQLi, SSRF, misconfigurations).
- Allow the Attacker to pivot between containers.

## Phase 3: Long-term Memory & Strategy
- Implement vector databases or persistent memory so agents can read summaries of past matches.
- Allow agents to build a "knowledge base" of the specific environment across multiple rounds.

## Phase 4: Reinforcement Learning & Fine-tuning
- Build data pipelines to export match logs into a dataset (e.g., ShareGPT format).
- Set up an automated fine-tuning pipeline (e.g., using Unsloth or similar tools) to update the model weights after a set of matches based on win/loss outcomes (RLHF/DPO).

## Phase 5: Scalability
- Support large-scale matches with N attackers vs M defenders.
- Support Kubernetes or Swarm for distributed container orchestration.
