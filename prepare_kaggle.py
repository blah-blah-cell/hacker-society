import json

notebook_path = './kaggle_run/notebook627229440d.ipynb'
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

code_lines = [
    "import os, sys, subprocess, time, requests\n",
    "os.chdir('/kaggle/working')\n",
    "if not os.path.exists('/kaggle/working/hacker-society'):\n",
    "    subprocess.run(['git', 'clone', 'https://github.com/blah-blah-cell/hacker-society.git', '/kaggle/working/hacker-society'], check=True)\n",
    "else:\n",
    "    subprocess.run(['git', '-C', '/kaggle/working/hacker-society', 'pull', 'origin', 'main'], check=True)\n",
    "os.chdir('/kaggle/working/hacker-society')\n",
    "subprocess.run(['apt-get', 'update', '-q'], check=True)\n",
    "subprocess.run(['apt-get', 'install', '-y', 'nmap', 'mysql-client', 'nano', 'vsftpd', 'net-tools', 'ufw', 'curl', 'netcat'], check=True)\n",
    "subprocess.run(['service', 'vsftpd', 'start'], capture_output=True)\n",
    "with open('/tmp/flag.txt', 'w') as f:\n",
    "    f.write('HACKSOC_REAL_FLAG_7B_2026')\n",
    "subprocess.run(['pkill', '-9', '-f', 'vllm'], capture_output=True)\n",
    "time.sleep(3)\n",
    "print('=== Starting Qwen/Qwen2.5-7B-Instruct-AWQ ===')\n",
    "vllm_log = open('/tmp/vllm7b.log', 'w')\n",
    "vllm_proc = subprocess.Popen(\n",
    "    [sys.executable, '-m', 'vllm.entrypoints.openai.api_server',\n",
    "     '--model', 'Qwen/Qwen2.5-7B-Instruct-AWQ',\n",
    "     '--port', '8000',\n",
    "     '--gpu-memory-utilization', '0.85',\n",
    "     '--max-model-len', '4096',\n",
    "     '--enable-auto-tool-choice',\n",
    "     '--tool-call-parser', 'hermes'],\n",
    "    stdout=vllm_log, stderr=subprocess.STDOUT\n",
    ")\n",
    "print('Waiting for vLLM server...')\n",
    "ready = False\n",
    "for i in range(90):\n",
    "    try:\n",
    "        r = requests.get('http://localhost:8000/v1/models', timeout=2)\n",
    "        if r.status_code == 200:\n",
    "            print(f'=== vLLM SERVER UP (after {i*2}s) ===')\n",
    "            ready = True\n",
    "            break\n",
    "    except Exception:\n",
    "        pass\n",
    "    time.sleep(2)\n",
    "if not ready:\n",
    "    print('Server failed. Log:')\n",
    "    with open('/tmp/vllm7b.log') as f:\n",
    "        print(f.read()[-2000:])\n",
    "else:\n",
    "    subprocess.run(['nvidia-smi', '--query-gpu=name,memory.used,memory.free', '--format=csv'])\n",
    "    print('=== Running 3-Turn Match (REAL_LOCAL_SHELL) ===')\n",
    "    res = subprocess.run(\n",
    "        \"echo '1' | MOCK_DOCKER_NO_CONTAINERS=1 REAL_LOCAL_SHELL=1 python -m src.main --model Qwen/Qwen2.5-7B-Instruct-AWQ --base-url http://localhost:8000/v1 --attackers 1 --defenders 1 --turns 3\",\n",
    "        shell=True, capture_output=True, text=True, cwd='/kaggle/working/hacker-society'\n",
    "    )\n",
    "    print('=== STDOUT ===')\n",
    "    print(res.stdout)\n",
    "    if res.stderr:\n",
    "        print('=== STDERR (tail) ===')\n",
    "        print(res.stderr[-800:])\n"
]

nb['cells'].append({
    'cell_type': 'code',
    'execution_count': None,
    'metadata': {},
    'outputs': [],
    'source': code_lines
})

with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

meta = {
  'id': 'ojmehta/notebook627229440d',
  'title': 'notebook627229440d',
  'code_file': 'notebook627229440d.ipynb',
  'language': 'python',
  'kernel_type': 'notebook',
  'is_private': 'true',
  'enable_gpu': 'true',
  'enable_tpu': 'false',
  'enable_internet': 'true',
  'dataset_sources': [],
  'kernel_sources': [],
  'competition_sources': []
}

with open('./kaggle_run/kernel-metadata.json', 'w', encoding='utf-8') as f:
    json.dump(meta, f, indent=2)

print('Notebook updated and metadata generated successfully.')
