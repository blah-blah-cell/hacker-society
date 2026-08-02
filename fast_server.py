from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import torch
import traceback
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
    temperature: float = 0.8
    max_tokens: int = 512

@app.get("/v1/models")
def list_models():
    return {"data": [{"id": MODEL_NAME}]}

@app.post("/v1/chat/completions")
def chat_completions(req: ChatCompletionRequest):
    try:
        clean_messages = []
        is_attacker = False
        
        for m in req.messages:
            role = "user" if m.role not in ["user", "assistant", "system"] else m.role
            content = str(m.content)
            if "red team" in content.lower() or "attacker" in content.lower():
                is_attacker = True
            clean_messages.append({"role": role, "content": content})

        # Add turn-specific tactical pressure to avoid nmap repetition loops
        if is_attacker:
            clean_messages.append({
                "role": "user",
                "content": "DO NOT RUN NMAP AGAIN. Try searching for flags using 'cat /tmp/flag.txt', 'find / -name flag.txt', 'curl', or exfiltrating data."
            })
        else:
            clean_messages.append({
                "role": "user",
                "content": "DO NOT RUN NMAP AGAIN. Execute defensive actions like 'ufw default deny', 'chmod 400 /tmp/flag.txt', or 'pkill vsftpd'."
            })

        outputs = pipe(
            clean_messages,
            max_new_tokens=req.max_tokens,
            temperature=0.8,
            repetition_penalty=1.3,
            do_sample=True
        )
        
        res_text = outputs[0]["generated_text"]
        if isinstance(res_text, list):
            res_text = res_text[-1]["content"]
        else:
            res_text = str(res_text)

        return {
            "id": "chatcmpl-live",
            "object": "chat.completion",
            "created": 123456789,
            "model": MODEL_NAME,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": res_text},
                "finish_reason": "stop"
            }]
        }
    except Exception as e:
        print(f"Server Processing Error: {e}")
        traceback.print_exc()
        fallback_cmd = "[EXEC]: cat /tmp/flag.txt" if is_attacker else "[EXEC]: ufw enable"
        return {
            "id": "chatcmpl-live",
            "object": "chat.completion",
            "created": 123456789,
            "model": MODEL_NAME,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": fallback_cmd},
                "finish_reason": "stop"
            }]
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
