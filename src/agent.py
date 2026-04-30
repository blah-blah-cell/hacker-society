import json
import os
from openai import OpenAI

class Agent:
    def __init__(self, role: str, environment, model="gpt-4o-mini", system_prompt=None):
        self.role = role
        self.environment = environment
        self.model = model

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
            }
        ]

    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})

    def take_turn(self, instruction: str = None) -> str:
        """
        Gives the agent a turn to act. The agent can use tools.
        Returns a summary of what the agent did (or its final response).
        """
        if instruction:
            self.add_message("user", instruction)

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

                    print(f"[{self.role.upper()} EXEC]: {command}")

                    # Execute in environment
                    output = self.environment.execute_in_container(self.role, command)

                    print(f"[{self.role.upper()} OUT]:\n{output[:500]}{'...' if len(output) > 500 else ''}")

                    # Feed output back to agent
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": output
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
