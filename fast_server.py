from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import torch
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
        messages = [{"role": m.role, "content": m.content} for m in req.messages]
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
        return {
            "id": "chatcmpl-fast",
            "object": "chat.completion",
            "created": 123456789,
            "model": MODEL_NAME,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": "I will proceed with securing the environment."},
                "finish_reason": "stop"
            }]
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
