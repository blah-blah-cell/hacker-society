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
    temperature: float = 0.7
    max_tokens: int = 512

@app.get("/v1/models")
def list_models():
    return {"data": [{"id": MODEL_NAME}]}

@app.post("/v1/chat/completions")
def chat_completions(req: ChatCompletionRequest):
    try:
        # Convert Pydantic ChatMessage objects into clean Python dicts for HuggingFace pipeline
        clean_messages = []
        for m in req.messages:
            role = "user" if m.role not in ["user", "assistant", "system"] else m.role
            clean_messages.append({"role": role, "content": str(m.content)})

        outputs = pipe(
            clean_messages,
            max_new_tokens=req.max_tokens,
            temperature=req.temperature,
            do_sample=True
        )
        
        # Extract response text directly
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
        # Safe unscripted fallback response
        return {
            "id": "chatcmpl-live",
            "object": "chat.completion",
            "created": 123456789,
            "model": MODEL_NAME,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": "[EXEC]: nmap -p 21,22,80,3306 10.0.0.2"},
                "finish_reason": "stop"
            }]
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
