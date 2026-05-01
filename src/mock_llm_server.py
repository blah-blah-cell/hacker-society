import http.server
import socketserver
import json
import uuid

PORT = 8000

class MockLLMHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/v1/chat/completions':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_json = json.loads(post_data.decode('utf-8'))

            messages = request_json.get('messages', [])
            last_message = messages[-1]['content'] if messages and 'content' in messages[-1] else ""

            response_data = {
                "id": f"chatcmpl-{uuid.uuid4().hex}",
                "object": "chat.completion",
                "created": 1234567890,
                "model": "mock-model",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": []
                    },
                    "finish_reason": "tool_calls"
                }],
                "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20}
            }

            # Simple logic to determine what mock response to send
            is_attacker = any("red team" in msg.get("content", "") for msg in messages if msg.get("role") == "system" or msg.get("role") == "user")
            last_role = messages[-1]['role'] if messages else ""

            # If the last role was a tool call output, we must return a text response to avoid infinite loops
            # If we are summarizing, just return text
            if "Summarize your findings" in str(last_message):
                response_data["choices"][0]["message"]["content"] = "This is a mock summary."
                response_data["choices"][0]["finish_reason"] = "stop"
                del response_data["choices"][0]["message"]["tool_calls"]
            elif last_role == "tool":
                response_data["choices"][0]["message"]["content"] = "Tool executed successfully."
                response_data["choices"][0]["finish_reason"] = "stop"
                del response_data["choices"][0]["message"]["tool_calls"]
            elif is_attacker:
                # Randomize slightly based on message count to simulate progress
                msg_count = len(messages)
                if msg_count < 4:
                    # Explore
                    response_data["choices"][0]["message"]["tool_calls"].append({
                        "id": f"call_{uuid.uuid4().hex}",
                        "type": "function",
                        "function": {
                            "name": "execute_bash_command",
                            "arguments": json.dumps({"command": "ls -la"})
                        }
                    })
                elif msg_count < 8:
                    # Communicate
                    response_data["choices"][0]["message"]["tool_calls"].append({
                        "id": f"call_{uuid.uuid4().hex}",
                        "type": "function",
                        "function": {
                            "name": "send_message_to_team",
                            "arguments": json.dumps({"message": "I am exploring the public container."})
                        }
                    })
                else:
                    # Try to exfiltrate
                    response_data["choices"][0]["message"]["content"] = "I found it! EXFILTRATED dummy_flag_to_test_fail"
                    response_data["choices"][0]["finish_reason"] = "stop"
                    del response_data["choices"][0]["message"]["tool_calls"]
            else:
                # Defender mock
                msg_count = len(messages)
                if msg_count < 4:
                    # Explore
                    response_data["choices"][0]["message"]["tool_calls"].append({
                        "id": f"call_{uuid.uuid4().hex}",
                        "type": "function",
                        "function": {
                            "name": "execute_bash_command",
                            "arguments": json.dumps({"command": "ps aux"})
                        }
                    })
                else:
                    # Communicate
                    response_data["choices"][0]["message"]["tool_calls"].append({
                        "id": f"call_{uuid.uuid4().hex}",
                        "type": "function",
                        "function": {
                            "name": "send_message_to_team",
                            "arguments": json.dumps({"message": "Looking good here."})
                        }
                    })

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), MockLLMHandler) as httpd:
        print(f"Mock LLM Server listening at port {PORT}")
        httpd.serve_forever()