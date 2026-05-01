import argparse
import time
import json
import os

def mock_fine_tune(dataset_path: str, model_name: str, output_dir: str):
    print(f"--- Starting Fine-Tuning Pipeline (MOCK) ---")
    print(f"Base Model: {model_name}")
    print(f"Dataset: {dataset_path}")
    print(f"Output Directory: {output_dir}")
    print("\nLoading dataset...")

    if not os.path.exists(dataset_path):
        print(f"Error: Dataset {dataset_path} not found.")
        return

    with open(dataset_path, "r") as f:
        lines = f.readlines()

    print(f"Found {len(lines)} examples in the dataset.")

    winning_paths = 0
    losing_paths = 0
    for line in lines:
        try:
            entry = json.loads(line)
            reward = entry.get("reward", 0.0)
            if reward > 0:
                winning_paths += 1
            elif reward < 0:
                losing_paths += 1
        except Exception:
            pass

    print(f"Dataset split: {winning_paths} winning paths (preferred), {losing_paths} losing paths (rejected).")

    print("\nInitializing model and tokenizer (Unsloth/HuggingFace mock)...")
    time.sleep(1)

    print("Applying LoRA adapters...")
    time.sleep(0.5)

    print("Configuring DPO (Direct Preference Optimization) Trainer...")
    time.sleep(0.5)

    print("\nStarting training loop...")
    epochs = 3
    for epoch in range(1, epochs + 1):
        print(f"  Epoch {epoch}/{epochs} [====================] - loss: {0.5 / epoch:.4f}")
        time.sleep(1)

    print("\nTraining complete!")
    os.makedirs(output_dir, exist_ok=True)
    final_model_path = os.path.join(output_dir, "fine_tuned_model")
    print(f"Saving fine-tuned model and LoRA weights to {final_model_path}...")

    # Just touch a file to mock saving
    with open(os.path.join(output_dir, "adapter_config.json"), "w") as f:
        json.dump({"mock": True, "base_model": model_name}, f)

    print(f"\n--- Fine-tuning successful! Model available at: {final_model_path} ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mock Fine-tuning Script for Hacker Society")
    parser.add_argument("--dataset", type=str, default="dataset.jsonl", help="Path to the JSONL dataset")
    parser.add_argument("--model", type=str, default="llama3-8b-instruct", help="Base model name")
    parser.add_argument("--output", type=str, default="models/ft_agent", help="Output directory")

    args = parser.parse_args()
    mock_fine_tune(args.dataset, args.model, args.output)
