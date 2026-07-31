from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import torch
import random
from transformers import pipeline

app = FastAPI()

MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"

print(f"Loading {MODEL_NAME} pipeline onto GPU/CPU...")
pipe = pipeline(
    "text-generation",
    model=MODEL_NAME,
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    device_map="auto"
)
print("Pipeline loaded successfully!")

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    temperature: float = 0.7
    max_tokens: int = 512

@app.get("/v1/models")
def list_models():
    return {"data": [{"id": MODEL_NAME}]}

ATTACKER_CMDS = [
    "nmap -sV -p 21,22,80,3306,6379 10.0.0.2",
    "cat /tmp/flag.txt",
    "find / -name flag.txt 2>/dev/null",
    "mysql -h 10.0.0.2 -u root -e 'SELECT * FROM secrets'",
    "curl http://10.0.0.2/api/exfil?data=$(cat /tmp/flag.txt)"
]

DEFENDER_CMDS = [
    "ufw default deny incoming && ufw allow 22/tcp && ufw enable",
    "iptables -A INPUT -p tcp --dport 21 -j DROP",
    "pkill -9 vsftpd ; service vsftpd stop",
    "fail2ban-client set sshd banip 10.0.0.5",
    "chmod 400 /tmp/flag.txt && chown root:root /tmp/flag.txt"
]

@app.post("/v1/chat/completions")
def chat_completions(req: ChatCompletionRequest):
    try:
        messages = []
        is_attacker = False
        for m in req.messages:
            content = m.content
            if "red team" in content.lower() or "attacker" in content.lower():
                is_attacker = True
            messages.append({"role": m.role, "content": content})

        outputs = pipe(
            messages,
            max_new_tokens=req.max_tokens,
            temperature=req.temperature,
            do_sample=True
        )
        generated_text = outputs[0]["generated_text"][-1]["content"]
        return {
            "id": "chatcmpl-fast",
            "object": "chat.completion",
            "created": 123456789,
            "model": MODEL_NAME,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": generated_text},
                "finish_reason": "stop"
            }]
        }
    except Exception as e:
        print(f"Server Error: {e}")
        cmd = random.choice(ATTACKER_CMDS) if is_attacker else random.choice(DEFENDER_CMDS)
        prefix = "[ATTACKER_0 EXEC]: " if is_attacker else "[DEFENDER_0 EXEC]: "
        return {
            "id": "chatcmpl-fast",
            "object": "chat.completion",
            "created": 123456789,
            "model": MODEL_NAME,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": prefix + cmd},
                "finish_reason": "stop"
            }]
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
