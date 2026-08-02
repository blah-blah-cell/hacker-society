from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import torch
import traceback
from transformers import AutoModelForCausalLM, AutoTokenizer

app = FastAPI()

# 14B Model for Advanced Autonomous Cyber Operations
MODEL_NAME = "Qwen/Qwen2.5-14B-Instruct-1M"

print(f"Loading 14B Model ({MODEL_NAME}) onto GPU with 4-bit/8-bit precision...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    device_map="auto",
    torch_dtype=torch.float16,
    trust_remote_code=True
)
print("14B Model loaded successfully!")

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    temperature: float = 0.7
    max_tokens: int = 1024

@app.get("/v1/models")
def list_models():
    return {"data": [{"id": MODEL_NAME}]}

@app.post("/v1/chat/completions")
def chat_completions(req: ChatCompletionRequest):
    try:
        clean_messages = [{"role": m.role, "content": m.content} for m in req.messages]
        
        # Apply model chat template
        prompt = tokenizer.apply_chat_template(clean_messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=req.max_tokens,
                temperature=req.temperature,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
            
        generated_ids = outputs[0][inputs.input_ids.shape[1]:]
        response_text = tokenizer.decode(generated_ids, skip_special_tokens=True)

        return {
            "id": "chatcmpl-14b",
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
        print(f"14B Model Execution Error: {e}")
        traceback.print_exc()
        return {
            "id": "chatcmpl-14b",
            "object": "chat.completion",
            "created": 123456789,
            "model": MODEL_NAME,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": "Error during 14B model generation."},
                "finish_reason": "stop"
            }]
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
