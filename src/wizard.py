"""
src/wizard.py

Interactive onboarding wizard for Hacker Society.
Automates model pulling, server startup, and match execution based on hardware profile.
"""

import os
import sys
import time
import subprocess
import requests
import platform
import shutil

def detect_hardware():
    hw_info = {
        "os": platform.system(),
        "arch": platform.machine(),
        "has_nvidia": False,
        "vram_mb": 0,
        "gpu_name": "None",
        "recommended_profile": "1"
    }
    
    if shutil.which("nvidia-smi"):
        try:
            hw_info["has_nvidia"] = True
            # Get GPU Name
            res_name = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True, text=True, check=True
            )
            hw_info["gpu_name"] = res_name.stdout.strip().split("\n")[0]
            
            # Get VRAM
            res_mem = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, check=True
            )
            hw_info["vram_mb"] = int(res_mem.stdout.strip().split("\n")[0])
        except Exception:
            pass

    # Decision Matrix
    if hw_info["has_nvidia"] and hw_info["vram_mb"] >= 7800:
        hw_info["recommended_profile"] = "2"
    else:
        hw_info["recommended_profile"] = "1"
        
    return hw_info

def print_header():
    print("=" * 65)
    print(" WELCOME TO HACKER SOCIETY - INTERACTIVE ONBOARDING")
    print("=" * 65)
    print("Choose your hardware profile. We will automatically download the")
    print("optimal model, start the inference server, and begin the match.\n")

def print_table():
    print("  [1] CPU Only / MacBook (Ollama)")
    print("      Model: qwen2.5:1.5b (ultra-fast, lightweight)")
    print("      Requires: Ollama installed locally\n")
    
    print("  [2] 8GB+ VRAM GPU (vLLM)")
    print("      Model: Qwen/Qwen2.5-7B-Instruct-AWQ (fits in 8GB)")
    print("      Requires: vLLM installed, CUDA GPU\n")
    
    print("  [3] Cloud API (OpenAI)")
    print("      Model: gpt-4o-mini")
    print("      Requires: OPENAI_API_KEY\n")
    
    print("  [4] Mock / Offline Mode (Test Run)")
    print("      Model: mock-model")
    print("      Requires: Nothing. Zero downloads, instant test.\n")

def wait_for_server(url: str, timeout: int = 120):
    print(f"\nWaiting for server to be ready at {url}...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                print("[OK] Server is UP and READY!\n")
                return True
        except Exception:
            pass
        time.sleep(2)
        print(".", end="", flush=True)
    
    print("\n[ERROR] Timed out waiting for server.")
    return False

def run_wizard():
    hw = detect_hardware()
    
    print_header()
    
    print("[HARDWARE DETECTED]")
    print(f"OS : {hw['os']} ({hw['arch']})")
    if hw["has_nvidia"]:
        print(f"GPU: {hw['gpu_name']} ({hw['vram_mb']} MB VRAM)")
    else:
        print("GPU: No NVIDIA GPU detected (or nvidia-smi missing)")
        
    print(f"\n=> Recommended Profile: [{hw['recommended_profile']}]\n")
    
    print_table()
    
    choice = input(f"Enter profile [1-4] (default: {hw['recommended_profile']}): ").strip()
    if not choice:
        choice = hw["recommended_profile"]
        
    server_proc = None
    env = os.environ.copy()
    model_args = []
    
    try:
        if choice == "1":
            print("\n[Profile 1] Selected: Ollama (CPU)")
            try:
                print("Pulling qwen2.5:1.5b (this may take a minute)...")
                subprocess.run(["ollama", "pull", "qwen2.5:1.5b"], check=False)
                
                print("\nStarting Ollama server in background...")
                server_proc = subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except FileNotFoundError:
                print("\n[ERROR] 'ollama' command not found. Please install Ollama from https://ollama.com/")
                sys.exit(1)
            
            base_url = "http://localhost:11434/v1"
            if not wait_for_server(f"{base_url}/models"):
                print("Warning: Ollama might already be running or failed to start.")
                
            model_args = ["--model", "qwen2.5:1.5b", "--base-url", base_url]
            
        elif choice == "2":
            print("\n[Profile 2] Selected: vLLM (GPU)")
            model_name = "Qwen/Qwen2.5-7B-Instruct-AWQ"
            print(f"Starting vLLM server with {model_name}...")
            
            try:
                server_proc = subprocess.Popen([
                    sys.executable, "-m", "vllm.entrypoints.openai.api_server",
                    "--model", model_name,
                    "--port", "8000",
                    "--gpu-memory-utilization", "0.85",
                    "--max-model-len", "4096"
                ])
            except Exception as e:
                print(f"\n[ERROR] Failed to start vLLM: {e}")
                print("Make sure it is installed: pip install vllm")
                sys.exit(1)
            
            base_url = "http://localhost:8000/v1"
            if not wait_for_server(f"{base_url}/models", timeout=300):
                sys.exit(1)
                
            model_args = ["--model", model_name, "--base-url", base_url]
            
        elif choice == "3":
            print("\n[Profile 3] Selected: Cloud API (OpenAI)")
            api_key = input("Enter your OpenAI API Key: ").strip()
            if not api_key:
                print("API Key is required for Cloud API. Exiting.")
                sys.exit(1)
                
            env["OPENAI_API_KEY"] = api_key
            model_args = ["--model", "gpt-4o-mini"]
            
        elif choice == "4":
            print("\n[Profile 4] Selected: Mock / Offline Mode")
            print("Starting local mock server...")
            server_proc = subprocess.Popen([sys.executable, "-m", "src.mock_llm_server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            base_url = "http://localhost:8000/v1"
            time.sleep(2) # Give mock server a second to bind
            env["MOCK_DOCKER_NO_CONTAINERS"] = "1"
            model_args = ["--model", "mock-model", "--base-url", base_url]
            
        else:
            print("Invalid choice. Exiting.")
            sys.exit(1)
            
        # Launch match
        print("=" * 65)
        print(" [LAUNCH] HACKER SOCIETY MATCH")
        print("=" * 65)
        
        cmd = [sys.executable, "-m", "src.main"] + model_args
        subprocess.run(cmd, env=env)
        
    except KeyboardInterrupt:
        print("\nWizard aborted by user.")
    finally:
        if server_proc:
            print("\nCleaning up background server...")
            server_proc.terminate()
            try:
                server_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_proc.kill()

if __name__ == "__main__":
    run_wizard()
