import http.server
import socketserver
import json
import uuid

PORT = 8000


class MockLLMHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress default request logging noise

    def do_POST(self):
        if self.path == "/v1/chat/completions":
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            request_json = json.loads(post_data.decode("utf-8"))

            messages = request_json.get("messages", [])
            last_message = (
                messages[-1]["content"] if messages and "content" in messages[-1] else ""
            )
            last_role = messages[-1]["role"] if messages else ""

            # Detect role from system prompt
            is_attacker = any(
                "red team" in msg.get("content", "")
                for msg in messages
                if msg.get("role") in ("system", "user")
            )

            # ---- Build base response skeleton (FIX: tool_calls starts as None) ----
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
                        "tool_calls": None,    # FIX: was [] which violates OAI schema
                    },
                    "finish_reason": "stop",
                }],
                "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
            }

            def make_tool_call(fn_name, arguments: dict):
                return {
                    "id": f"call_{uuid.uuid4().hex}",
                    "type": "function",
                    "function": {
                        "name": fn_name,
                        "arguments": json.dumps(arguments),
                    },
                }

            def set_tool_response(tool_calls: list):
                """Switch response to a tool_calls finish."""
                response_data["choices"][0]["message"]["tool_calls"] = tool_calls
                response_data["choices"][0]["message"]["content"] = None
                response_data["choices"][0]["finish_reason"] = "tool_calls"

            def set_text_response(text: str):
                """Switch response to a plain text finish."""
                response_data["choices"][0]["message"]["content"] = text
                response_data["choices"][0]["message"]["tool_calls"] = None
                response_data["choices"][0]["finish_reason"] = "stop"

            # ---- Routing logic ----
            if "Summarize your findings" in str(last_message):
                set_text_response("This is a mock summary.")

            elif last_role == "tool":
                # After tool execution: return a simple acknowledgement
                set_text_response("Tool executed successfully. Continuing analysis.")

            elif is_attacker:
                msg_count = len(messages)
                if msg_count < 4:
                    set_tool_response([make_tool_call("execute_bash_command", {"command": "nmap -sV 10.0.0.0/24"})])
                elif msg_count < 8:
                    set_tool_response([make_tool_call("send_message_to_team", {"message": "Found open ports on 10.0.0.2, attempting exploitation."})])
                else:
                    # Simulate failed exfil (correct format but wrong flag)
                    set_text_response("Attempted flag read. EXFILTRATED dummy_flag_to_test_fail")

            else:  # defender
                msg_count = len(messages)
                if msg_count < 4:
                    set_tool_response([make_tool_call("execute_bash_command", {"command": "iptables -A INPUT -p tcp --dport 21 -j DROP"})])
                else:
                    set_tool_response([make_tool_call("send_message_to_team", {"message": "Hardened FTP port. Monitoring logs."})])

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), MockLLMHandler) as httpd:
        print(f"Mock LLM Server listening on port {PORT}")
        httpd.serve_forever()
