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
    HISTORY_WINDOW = 10

    def _pruned_messages(self) -> list:
        def _get_role(m):
            if isinstance(m, dict):
                return m.get("role")
            return getattr(m, "role", None)

        system_msgs = [m for m in self.messages if _get_role(m) == "system"]
        user_initial = [m for m in self.messages if _get_role(m) == "user"][:1]  # Pin first objective prompt
        other_msgs  = [m for m in self.messages if m not in system_msgs and m not in user_initial]

        if len(other_msgs) > self.HISTORY_WINDOW:
            other_msgs = other_msgs[-self.HISTORY_WINDOW:]
            # Prevent starting the message slice on an orphaned tool message
            while other_msgs and _get_role(other_msgs[0]) == "tool":
                other_msgs.pop(0)

        return system_msgs + user_initial + other_msgs


    # ------------------------------------------------------------------ #
    # Tool dispatch & parsing helpers                                      #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _safe_parse_args(raw_args) -> tuple[dict, str | None]:
        """Safely parse tool arguments from raw string, handling markdown or dirty JSON."""
        if isinstance(raw_args, dict):
            return raw_args, None
        if not raw_args:
            return {}, None

        text = str(raw_args).strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        # Attempt 1: Standard JSON decode
        try:
            return json.loads(text), None
        except Exception:
            pass

        # Attempt 2: Python literal_eval for single-quoted dicts
        import ast
        try:
            parsed = ast.literal_eval(text)
            if isinstance(parsed, dict):
                return parsed, None
        except Exception:
            pass

        # Attempt 3: Regex fallback for command parameter
        import re
        cmd_match = re.search(r'["\']command["\']\s*:\s*["\'](.*?)["\']\s*\}?$', text, re.DOTALL)
        if cmd_match:
            return {"command": cmd_match.group(1)}, None

        msg_match = re.search(r'["\']message["\']\s*:\s*["\'](.*?)["\']\s*\}?$', text, re.DOTALL)
        if msg_match:
            return {"message": msg_match.group(1)}, None

        query_match = re.search(r'["\']query["\']\s*:\s*["\'](.*?)["\']\s*\}?$', text, re.DOTALL)
        if query_match:
            return {"query": query_match.group(1)}, None

        return {}, f"Could not parse tool arguments as valid JSON: {text[:200]}"

    def _handle_tool_call(self, tool_call) -> dict:
        fn_name = tool_call.function.name
        raw_args = tool_call.function.arguments
        args, parse_error = self._safe_parse_args(raw_args)

        if parse_error:
            output = f"Tool Error: {parse_error}. Please provide valid JSON arguments."
        elif fn_name == "execute_bash_command":
            command = args.get("command", "")
            print(f"[{self.agent_id.upper()} EXEC]: {command}")
            try:
                output = self.environment.execute_in_container(self.agent_id, self.role, command)
            except Exception as e:
                output = f"Execution error in container: {str(e)}"
            if len(output) > 1000:
                output = output[:1000] + "\n...[truncated long output]"
            print(f"[{self.agent_id.upper()} OUT]:\n{output[:500]}{'...' if len(output) > 500 else ''}")

        elif fn_name == "search_memory":
            query = args.get("query", "")
            print(f"[{self.agent_id.upper()} SEARCH_MEMORY]: {query}")
            if self.memory_store:
                try:
                    results = self.memory_store.search_memory(self.role, query)
                    output = (
                        "Found memories:\n" + "\n".join(f"- {r}" for r in results)
                        if results else "No matching memories found."
                    )
                except Exception as e:
                    output = f"Error querying memory store: {e}"
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

    def take_turn(self, instruction: str | None = None) -> str:
        import time
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
            kwargs = self.cfg.api_kwargs()

            # Resilient API completion call with retry backoff
            response = None
            for attempt in range(3):
                try:
                    response = self.client.chat.completions.create(
                        messages=self._pruned_messages(),  # type: ignore
                        tools=self.tools,                  # type: ignore
                        tool_choice="auto",
                        **kwargs,                          # type: ignore
                    )
                    break
                except Exception as e:
                    if attempt == 2:
                        print(f"[{self.agent_id.upper()}] API call failed permanently: {e}")
                        return f"Error: API completion failed: {e}"
                    sleep_s = 2 ** attempt
                    print(f"[{self.agent_id.upper()}] Transient API error ({e}). Retrying in {sleep_s}s...")
                    time.sleep(sleep_s)

            if not response or not response.choices:
                return "Error: Empty response choices from model."

            llm_message = response.choices[0].message
            self.messages.append(llm_message)

            # Fallback: if native tool_calls is empty but content contains tool calls in text
            if not llm_message.tool_calls and llm_message.content:
                import re
                # Check for <tool_call> tags
                matches = re.findall(r'<tool_call>\s*(.*?)\s*</tool_call>', llm_message.content, re.DOTALL)
                # Check for markdown json codeblocks if no tags found
                if not matches:
                    json_blocks = re.findall(r'```(?:json)?\s*(\{[^{}]*"(?:name|tool_call)"[^{}]*\})\s*```', llm_message.content, re.DOTALL)
                    matches.extend(json_blocks)

                for m in matches:
                    try:
                        data = json.loads(m)
                        if "tool_call" in data and isinstance(data["tool_call"], dict):
                            data = data["tool_call"]
                        fn_name = data.get("name")
                        args = data.get("arguments", {})
                        if isinstance(args, str):
                            args, _ = self._safe_parse_args(args)

                        if fn_name == "execute_bash_command":
                            cmd = args.get("command", "")
                            print(f"[{self.agent_id.upper()} EXEC (PARSED)]: {cmd}")
                            out = self.environment.execute_in_container(self.agent_id, self.role, cmd)
                            self.add_message("user", f"Tool Output for '{cmd}':\n{out}")
                        elif fn_name == "send_message_to_team":
                            msg = args.get("message", "")
                            print(f"[{self.agent_id.upper()} TEAM MSG (PARSED)]: {msg}")
                            self.team_channel.append({"sender_id": self.agent_id, "message": msg})
                            self.add_message("user", "Message broadcasted to team.")
                    except Exception:
                        pass

            if not llm_message.tool_calls:
                return llm_message.content if llm_message.content is not None else ""

            for tc in llm_message.tool_calls:
                result_msg = self._handle_tool_call(tc)
                self.messages.append(result_msg)

        # Exceeded MAX_TOOL_ROUNDS — force plain text response
        print(f"[{self.agent_id.upper()}] WARNING: hit MAX_TOOL_ROUNDS={MAX_TOOL_ROUNDS}, forcing final response.")
        kwargs_final = {k: v for k, v in self.cfg.api_kwargs().items() if k != "tools"}
        try:
            final = self.client.chat.completions.create(
                messages=self._pruned_messages(),  # type: ignore
                **kwargs_final,                    # type: ignore
            )
            final_msg = final.choices[0].message
            self.messages.append(final_msg)
            return final_msg.content if final_msg.content is not None else ""
        except Exception as e:
            return f"Final turn completed with error: {e}"
