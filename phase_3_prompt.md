# Phase 3: Prompt for Next Session

**Context:**
Welcome to Hacker Society! In the previous session, we completed Phase 2. The core orchestration engine is built, and we now have a robust multi-container environment. Attackers spawn on a public network alongside a vulnerable Defender container (which runs 1 of 21 selectable system-level vulnerabilities via a TUI). The Defender container acts as a bridge to a hidden, internal network where a Database (DB) container holds the secret flag.

**Your Goal for this Session:**
Your objective is to implement **Phase 3: Long-term Memory & Strategy**.

Currently, matches are ephemeral. When a match restarts, the Attacker and Defender AI agents lose all knowledge of the environment, successful exploits, or applied patches. We want agents to build persistent "knowledge bases" across multiple rounds.

Please complete the following:

1. **Review Context:** Read `AGENTS.md`, `ROADMAP.md`, and `README.md` to understand the current architecture and guidelines. Update `ROADMAP.md` to mark Phase 2 as complete and Phase 3 as current.
2. **Implement Persistent Memory Store:** Create a mechanism (e.g., SQLite, a simple JSON-based vector store, or standard file-based memory) in the `src/` directory to persistently store match summaries, successful command sequences, or environment topology.
3. **Agent Summarization:** Update `src/agent.py` or `src/match.py` so that at the *end* of every match, both the Attacker and Defender generate a concise summary of what they learned (e.g., "Found FTP on port 21, it requires anonymous login, DB container is at 172.18.0.3"). Save this summary to the persistent memory store.
4. **Agent Context Injection:** Update the startup sequence in `src/match.py` so that at the *start* of a new match, the agents are provided with their respective historical summaries from the memory store in their system prompt.
5. **Add RAG/Search Tools (Optional/Bonus):** If appropriate, give the agents a new tool (e.g., `search_memory`) allowing them to query their past experiences during a match instead of loading it all in the prompt.
6. **Testing & Verification:** Ensure that running multiple matches sequentially via `src/main.py` demonstrates the agents utilizing knowledge from previous rounds. Ensure everything adheres to standard python libraries where possible and follows the `AGENTS.md` guidelines.

Good luck! You are building the foundation for AI agents that learn and adapt over time.