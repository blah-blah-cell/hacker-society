"""
fast_server.py — Autonomous Cyber Range LLM Server

Serves Qwen/Qwen2.5-7B-Instruct with 8-bit quantization (bitsandbytes)
compatible across all GPU architectures (Tesla P100 sm_60, T4 sm_75, A100 sm_80).
"""
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import torch
import traceback
import json
import re
import uuid
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

app = FastAPI()

MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"

print(f"Loading {MODEL_NAME} with 8-bit quantization for universal GPU compatibility...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)

# 8-bit quantization works on all GPUs including P100 (sm_60) & T4 (sm_75)
quantization_config = BitsAndBytesConfig(load_in_8bit=True)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=quantization_config,
    device_map="auto",
    trust_remote_code=True
)
print(f"{MODEL_NAME} 8-bit loaded successfully!")


class ChatMessage(BaseModel):
    role: str
    content: str | None = None
    tool_calls: list | None = None
    tool_call_id: str | None = None

class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    temperature: float = 0.7
    max_tokens: int = 1024
    tools: list | None = None
    tool_choice: str | None = None


def build_tool_aware_prompt(messages: list[ChatMessage], tools: list | None) -> list[dict]:
    tool_description = ""
    if tools:
        for t in tools:
            fn = t.get("function", {})
            name = fn.get("name", "")
            desc = fn.get("description", "")
            params = json.dumps(fn.get("parameters", {}))
            tool_description += f"\n- {name}: {desc}\n  Parameters: {params}\n"

    system_inject = (
        "You are an autonomous cybersecurity AI agent operating in a live Linux environment.\n"
        "You have access to the following tools:\n"
        f"{tool_description}\n"
        "To use a tool, respond with EXACTLY this JSON format (no other text before or after):\n"
        '{"tool_call": {"name": "execute_bash_command", "arguments": {"command": "YOUR_BASH_COMMAND"}}}\n\n'
        "Rules:\n"
        "- You MUST call execute_bash_command with a real Linux bash command.\n"
        "- Analyze the terminal output you receive and plan your next move.\n"
        "- Be creative, aggressive, and strategic. Use diverse commands.\n"
        "- Never explain what you're doing. Just output the JSON tool call.\n"
    )

    clean_messages = []
    for m in messages:
        role = m.role
        content = m.content or ""

        if role == "system":
            role = "system"
            content = system_inject + "\n" + content
        elif role == "tool":
            role = "user"
            content = f"Terminal Output:\n```\n{content}\n```\nNow choose your next action. Respond with ONLY a JSON tool call."
        elif role not in ("user", "assistant", "system"):
            role = "user"

        if clean_messages and clean_messages[-1]["role"] == role:
            clean_messages[-1]["content"] += "\n" + content
        else:
            clean_messages.append({"role": role, "content": content})

    if not clean_messages or clean_messages[0]["role"] != "system":
        clean_messages.insert(0, {"role": "system", "content": system_inject})

    return clean_messages


def parse_tool_call(text: str):
    patterns = [
        r'\{\s*"tool_call"\s*:\s*\{.*?\}\s*\}',
        r'\{\s*"name"\s*:\s*"execute_bash_command".*?\}',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
                if "tool_call" in data:
                    return data["tool_call"]
                elif "name" in data:
                    return data
            except json.JSONDecodeError:
                continue

    cmd_patterns = [
        r'```bash\s*\n(.*?)\n```',
        r'```\s*\n(.*?)\n```',
        r'\[EXEC\]:\s*(.*)',
        r'`([^`]{3,})`',
    ]
    for pattern in cmd_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            cmd = match.group(1).strip()
            if cmd and len(cmd) < 500:
                return {"name": "execute_bash_command", "arguments": {"command": cmd}}

    return None


@app.get("/v1/models")
def list_models():
    return {"data": [{"id": MODEL_NAME}]}


@app.post("/v1/chat/completions")
def chat_completions(req: ChatCompletionRequest):
    try:
        clean_messages = build_tool_aware_prompt(req.messages, req.tools)

        prompt = tokenizer.apply_chat_template(
            clean_messages, tokenize=False, add_generation_prompt=True
        )
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=4096).to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=req.max_tokens,
                temperature=req.temperature,
                do_sample=True,
                repetition_penalty=1.15,
                pad_token_id=tokenizer.eos_token_id
            )

        generated_ids = outputs[0][inputs.input_ids.shape[1]:]
        response_text = tokenizer.decode(generated_ids, skip_special_tokens=True).strip()

        tool_call = parse_tool_call(response_text)

        if tool_call and req.tools:
            call_id = f"call_{uuid.uuid4().hex[:8]}"
            return {
                "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                "object": "chat.completion",
                "created": 123456789,
                "model": MODEL_NAME,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": call_id,
                            "type": "function",
                            "function": {
                                "name": tool_call["name"],
                                "arguments": json.dumps(tool_call.get("arguments", {}))
                            }
                        }]
                    },
                    "finish_reason": "tool_calls"
                }]
            }
        else:
            return {
                "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                "object": "chat.completion",
                "created": 123456789,
                "model": MODEL_NAME,
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": response_text},
                    "finish_reason": "stop"
                }]
            }

    except Exception as e:
        print(f"Qwen 8-Bit Server Error: {e}")
        traceback.print_exc()
        return {
            "id": f"chatcmpl-err",
            "object": "chat.completion",
            "created": 123456789,
            "model": MODEL_NAME,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": f"Server error: {str(e)}"},
                "finish_reason": "stop"
            }]
        }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
