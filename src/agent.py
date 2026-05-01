import json
import os
from openai import OpenAI

class Agent:
    def __init__(self, agent_id: str, role: str, environment, model="gpt-4o-mini", system_prompt=None, team_channel=None):
        self.agent_id = agent_id
        self.role = role
        self.environment = environment
        self.model = model
        self.team_channel = team_channel if team_channel is not None else []

        # Support configuring a custom base URL for local models via environment variable
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
                    "description": "Execute a bash command in your isolated container environment. Use this to explore the network, read files, or configure services.",
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
                    "description": "Search your long-term memory for past experiences or successful commands related to a specific query.",
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
                    "description": "Broadcast a message to your other team members to coordinate and assign tasks.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "The message to send to your team."
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

    def take_turn(self, instruction: str = None) -> str:
        """
        Gives the agent a turn to act. The agent can use tools.
        Returns a summary of what the agent did (or its final response).
        """
        # Inject recent team messages into instruction
        team_messages_context = ""
        if self.team_channel:
            # We take all messages and inject them to ensure the agent knows the team's status
            msgs = [f"[{m['sender_id']}]: {m['message']}" for m in self.team_channel if m['sender_id'] != self.agent_id]
            if msgs:
                team_messages_context = "\nRecent messages from your team:\n" + "\n".join(msgs[-5:]) + "\n"

        if instruction or team_messages_context:
            self.add_message("user", f"{instruction or ''}\n{team_messages_context}")

        # Call LLM with tools
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            tools=self.tools,
            tool_choice="auto"
        )

        message = response.choices[0].message
        self.messages.append(message)

        # Handle tool calls
        if message.tool_calls:
            for tool_call in message.tool_calls:
                if tool_call.function.name == "execute_bash_command":
                    args = json.loads(tool_call.function.arguments)
                    command = args.get("command", "")

                    print(f"[{self.agent_id.upper()} EXEC]: {command}")

                    # Execute in environment
                    output = self.environment.execute_in_container(self.agent_id, self.role, command)

                    print(f"[{self.agent_id.upper()} OUT]:\n{output[:500]}{'...' if len(output) > 500 else ''}")

                    # Feed output back to agent
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": output
                    })
                elif tool_call.function.name == "search_memory":
                    args = json.loads(tool_call.function.arguments)
                    query = args.get("query", "")

                    print(f"[{self.agent_id.upper()} SEARCH_MEMORY]: {query}")

                    if self.memory_store:
                        results = self.memory_store.search_memory(self.role, query)
                        if results:
                            output = "Found memories:\n" + "\n".join(f"- {res}" for res in results)
                        else:
                            output = "No matching memories found."
                    else:
                        output = "Memory store is not available."

                    # Feed output back to agent
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": output
                    })
                elif tool_call.function.name == "send_message_to_team":
                    args = json.loads(tool_call.function.arguments)
                    message = args.get("message", "")

                    print(f"[{self.agent_id.upper()} TEAM MSG]: {message}")

                    self.team_channel.append({
                        "sender_id": self.agent_id,
                        "message": message
                    })

                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": "Message broadcasted to team."
                    })

            # Get the final response after tool execution
            second_response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages
            )
            final_message = second_response.choices[0].message
            self.messages.append(final_message)
            return final_message.content if final_message.content is not None else ""

        return message.content if message.content is not None else ""
