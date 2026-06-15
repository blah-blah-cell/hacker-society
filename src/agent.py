import json
import os
from openai import OpenAI

MAX_TOOL_ROUNDS = 10  # safety ceiling to prevent infinite loops


class Agent:
    def __init__(self, agent_id: str, role: str, environment, model="gpt-4o-mini",
                 system_prompt=None, team_channel=None):
        self.agent_id = agent_id
        self.role = role
        self.environment = environment
        self.model = model
        self.team_channel = team_channel if team_channel is not None else []

        base_url = os.getenv("LLM_BASE_URL")
        api_key = os.getenv("LLM_API_KEY", "dummy-key-for-local")

        if base_url:
            self.client = OpenAI(base_url=base_url, api_key=api_key)
        else:
            self.client = OpenAI(api_key=api_key)

        self.messages = []
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
                            "command": {
                                "type": "string",
                                "description": "The bash command to execute."
                            }
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_memory",
                    "description": "Search long-term memory for past experiences or successful commands.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The keyword or topic to search for."
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "send_message_to_team",
                    "description": "Broadcast a message to other team members to coordinate.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "The message to send to the team."
                            }
                        },
                        "required": ["message"]
                    }
                }
            }
        ]

        self.memory_store = None

    def set_memory_store(self, memory_store):
        self.memory_store = memory_store

    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})

    # ------------------------------------------------------------------ #
    # Message-history pruning: keep system prompt + last N messages       #
    # ------------------------------------------------------------------ #
    HISTORY_WINDOW = 30

    def _pruned_messages(self):
        """Return a capped slice of message history to avoid context blowup."""
        system_msgs = [m for m in self.messages if m.get("role") == "system"]
        non_system = [m for m in self.messages if m.get("role") != "system"]
        if len(non_system) > self.HISTORY_WINDOW:
            non_system = non_system[-self.HISTORY_WINDOW:]
        return system_msgs + non_system

    def _handle_tool_call(self, tool_call) -> dict:
        """Execute a single tool call and return the tool-result message."""
        fn_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

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
                output = ("Found memories:\n" + "\n".join(f"- {r}" for r in results)
                          if results else "No matching memories found.")
            else:
                output = "Memory store is not available."

        elif fn_name == "send_message_to_team":
            team_msg = args.get("message", "")   # renamed to avoid shadowing
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

    def take_turn(self, instruction: str = None) -> str:
        """
        Gives the agent a turn to act. Supports multi-round tool calls.
        Returns a summary of what the agent did (or its final text response).
        """
        # Inject team context + instruction
        team_messages_context = ""
        if self.team_channel:
            msgs = [
                f"[{m['sender_id']}]: {m['message']}"
                for m in self.team_channel
                if m['sender_id'] != self.agent_id
            ]
            if msgs:
                team_messages_context = (
                    "\nRecent messages from your team:\n" + "\n".join(msgs[-5:]) + "\n"
                )

        if instruction or team_messages_context:
            self.add_message("user", f"{instruction or ''}\n{team_messages_context}")

        # ---- Multi-round tool loop (FIX: was single-shot if/else) ---- #
        for _ in range(MAX_TOOL_ROUNDS):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self._pruned_messages(),
                tools=self.tools,
                tool_choice="auto",
            )

            llm_message = response.choices[0].message
            self.messages.append(llm_message)

            # No tool calls → agent is done, return text
            if not llm_message.tool_calls:
                return llm_message.content if llm_message.content is not None else ""

            # Execute every tool call in this round
            for tc in llm_message.tool_calls:
                result_msg = self._handle_tool_call(tc)
                self.messages.append(result_msg)

        # Safety: exceeded MAX_TOOL_ROUNDS — force a final text response
        print(f"[{self.agent_id.upper()}] WARNING: hit MAX_TOOL_ROUNDS={MAX_TOOL_ROUNDS}, forcing final response.")
        final = self.client.chat.completions.create(
            model=self.model,
            messages=self._pruned_messages(),
        )
        final_msg = final.choices[0].message
        self.messages.append(final_msg)
        return final_msg.content if final_msg.content is not None else ""
