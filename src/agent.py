"""
src/agent.py

LLM agent with:
  - Flexible model config via ModelConfig (any provider / endpoint)
  - Multi-round tool call loop (up to MAX_TOOL_ROUNDS)
  - Rolling message-history window to prevent context blowup
  - Thread-safe team channel
"""

from __future__ import annotations

import json

from src.model_config import ModelConfig

MAX_TOOL_ROUNDS = 10


class Agent:
    def __init__(
        self,
        agent_id: str,
        role: str,
        environment,
        model_config: ModelConfig | None = None,
        # Legacy convenience shims — still accepted so existing call-sites don't break
        model: str = "gpt-4o-mini",
        base_url: str | None = None,
        api_key: str | None = None,
        # -------
        system_prompt: str | None = None,
        team_channel: list | None = None,
    ):
        self.agent_id = agent_id
        self.role = role
        self.environment = environment
        self.team_channel = team_channel if team_channel is not None else []

        # ------------------------------------------------------------------ #
        # Model config resolution order:                                       #
        #   1. Explicit ModelConfig object (highest priority)                  #
        #   2. Legacy kwargs (model + base_url + api_key)                      #
        #   3. Env vars via ModelConfig.from_env()                             #
        # ------------------------------------------------------------------ #
        if model_config is not None:
            self.cfg = model_config
        elif base_url is not None:
            self.cfg = ModelConfig(model=model, base_url=base_url, api_key=api_key)
        else:
            self.cfg = ModelConfig(model=model, api_key=api_key)

        self.client = self.cfg.client

        self.messages: list[dict] = []
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})

        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "execute_bash_command",
                    "description": "Execute a bash command in your isolated container environment.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "The bash command to execute."}
                        },
                        "required": ["command"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_memory",
                    "description": "Search long-term memory for past experiences or successful commands.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The keyword or topic to search for."}
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "send_message_to_team",
                    "description": "Broadcast a message to other team members to coordinate.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string", "description": "The message to send to the team."}
                        },
                        "required": ["message"],
                    },
                },
            },
        ]

        self.memory_store = None

    # ------------------------------------------------------------------ #
    # Public helpers                                                       #
    # ------------------------------------------------------------------ #

    def set_memory_store(self, memory_store):
        self.memory_store = memory_store

    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})

    # ------------------------------------------------------------------ #
    # Message-history pruning                                             #
    # ------------------------------------------------------------------ #
    HISTORY_WINDOW = 30

    def _pruned_messages(self) -> list[dict]:
        system_msgs = [m for m in self.messages if m.get("role") == "system"]
        non_system  = [m for m in self.messages if m.get("role") != "system"]
        if len(non_system) > self.HISTORY_WINDOW:
            non_system = non_system[-self.HISTORY_WINDOW:]
        return system_msgs + non_system

    # ------------------------------------------------------------------ #
    # Tool dispatch                                                        #
    # ------------------------------------------------------------------ #

    def _handle_tool_call(self, tool_call) -> dict:
        fn_name = tool_call.function.name
        args    = json.loads(tool_call.function.arguments)

        if fn_name == "execute_bash_command":
            command = args.get("command", "")
            print(f"[{self.agent_id.upper()} EXEC]: {command}")
            output = self.environment.execute_in_container(self.agent_id, self.role, command)
            print(f"[{self.agent_id.upper()} OUT]:\n{output[:500]}{'...' if len(output) > 500 else ''}")

        elif fn_name == "search_memory":
            query = args.get("query", "")
            print(f"[{self.agent_id.upper()} SEARCH_MEMORY]: {query}")
            if self.memory_store:
                results = self.memory_store.search_memory(self.role, query)
                output = (
                    "Found memories:\n" + "\n".join(f"- {r}" for r in results)
                    if results else "No matching memories found."
                )
            else:
                output = "Memory store is not available."

        elif fn_name == "send_message_to_team":
            team_msg = args.get("message", "")
            print(f"[{self.agent_id.upper()} TEAM MSG]: {team_msg}")
            self.team_channel.append({"sender_id": self.agent_id, "message": team_msg})
            output = "Message broadcasted to team."

        else:
            output = f"Unknown tool: {fn_name}"

        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": fn_name,
            "content": output,
        }

    # ------------------------------------------------------------------ #
    # Main turn loop                                                       #
    # ------------------------------------------------------------------ #

    def take_turn(self, instruction: str = None) -> str:
        # Inject team context + instruction
        team_messages_context = ""
        if self.team_channel:
            msgs = [
                f"[{m['sender_id']}]: {m['message']}"
                for m in self.team_channel
                if m["sender_id"] != self.agent_id
            ]
            if msgs:
                team_messages_context = (
                    "\nRecent messages from your team:\n" + "\n".join(msgs[-5:]) + "\n"
                )

        if instruction or team_messages_context:
            self.add_message("user", f"{instruction or ''}\n{team_messages_context}")

        for _ in range(MAX_TOOL_ROUNDS):
            response = self.client.chat.completions.create(
                messages=self._pruned_messages(),
                tools=self.tools,
                tool_choice="auto",
                **self.cfg.api_kwargs(),
            )

            llm_message = response.choices[0].message
            self.messages.append(llm_message)

            if not llm_message.tool_calls:
                return llm_message.content if llm_message.content is not None else ""

            for tc in llm_message.tool_calls:
                result_msg = self._handle_tool_call(tc)
                self.messages.append(result_msg)

        # Exceeded MAX_TOOL_ROUNDS — force plain text response
        print(f"[{self.agent_id.upper()}] WARNING: hit MAX_TOOL_ROUNDS={MAX_TOOL_ROUNDS}, forcing final response.")
        final = self.client.chat.completions.create(
            messages=self._pruned_messages(),
            **{k: v for k, v in self.cfg.api_kwargs().items() if k != "tools"},
        )
        final_msg = final.choices[0].message
        self.messages.append(final_msg)
        return final_msg.content if final_msg.content is not None else ""
