import json

notebook_path = './kaggle_run/notebook627229440d.ipynb'

code_lines = [
    "import os, sys, subprocess, time, requests\n",
    "os.chdir('/kaggle/working')\n",
    "if not os.path.exists('/kaggle/working/hacker-society'):\n",
    "    subprocess.run(['git', 'clone', 'https://github.com/blah-blah-cell/hacker-society.git', '/kaggle/working/hacker-society'], check=True)\n",
    "else:\n",
    "    subprocess.run(['git', '-C', '/kaggle/working/hacker-society', 'fetch', 'origin'], check=True)\n",
    "    subprocess.run(['git', '-C', '/kaggle/working/hacker-society', 'reset', '--hard', 'origin/main'], check=True)\n",
    "os.chdir('/kaggle/working/hacker-society')\n",
    "subprocess.run(['pip', 'install', '-q', 'fastapi', 'uvicorn', 'transformers', 'accelerate', 'torch'], check=True)\n",
    "subprocess.run(['apt-get', 'update', '-q'], check=True)\n",
    "subprocess.run(['apt-get', 'install', '-y', 'nmap', 'mysql-client', 'nano', 'vsftpd', 'net-tools', 'ufw', 'curl', 'netcat', 'psmisc'], check=True)\n",
    "subprocess.run(['service', 'vsftpd', 'start'], capture_output=True)\n",
    "subprocess.run('pkill -9 -f vllm ; pkill -9 -f python ; fuser -v /dev/nvidia* -k -9', shell=True, capture_output=True)\n",
    "time.sleep(4)\n",
    "print('=== Starting Qwen 2.5 3B Server (Qwen/Qwen2.5-3B-Instruct) ===')\n",
    "server_log = open('/tmp/server.log', 'w')\n",
    "server_proc = subprocess.Popen([sys.executable, 'fast_server.py'], stdout=server_log, stderr=subprocess.STDOUT)\n",
    "print('Waiting up to 180s for Qwen 2.5 3B server startup...')\n",
    "ready = False\n",
    "for i in range(180):\n",
    "    try:\n",
    "        r = requests.get('http://localhost:8000/v1/models', timeout=2)\n",
    "        if r.status_code == 200:\n",
    "            print(f'=== QWEN 2.5 3B SERVER IS UP AND READY (after {i*2}s) ===')\n",
    "            print(r.json())\n",
    "            ready = True\n",
    "            break\n",
    "    except Exception:\n",
    "        pass\n",
    "    time.sleep(2)\n",
    "if not ready:\n",
    "    print('Server failed to start within 180s. Log:')\n",
    "    with open('/tmp/server.log') as f:\n",
    "        server_err = f.read()\n",
    "        print(server_err)\n",
    "        with open('/kaggle/working/match_output.txt', 'w') as out_f:\n",
    "            out_f.write('SERVER_STARTUP_FAILED:\\n' + server_err)\n",
    "else:\n",
    "    subprocess.run(['nvidia-smi', '--query-gpu=name,memory.used,memory.free', '--format=csv'])\n",
    "    print('=== Running Qwen 2.5 3B Autonomous Cyber Match ===')\n",
    "    res = subprocess.run(\n",
    "        \"echo '1' | MOCK_DOCKER_NO_CONTAINERS=1 REAL_LOCAL_SHELL=1 python -m src.main --model Qwen/Qwen2.5-3B-Instruct --base-url http://localhost:8000/v1 --attackers 1 --defenders 1 --turns 3\",\n",
    "        shell=True, capture_output=True, text=True, cwd='/kaggle/working/hacker-society'\n",
    "    )\n",
    "    match_out = res.stdout + ('\\n=== STDERR ===\\n' + res.stderr if res.stderr else '')\n",
    "    with open('/kaggle/working/match_output.txt', 'w', encoding='utf-8') as f:\n",
    "        f.write(match_out)\n",
    "    print(match_out)\n"
]

clean_nb = {
    'cells': [{
        'cell_type': 'code',
        'execution_count': None,
        'metadata': {},
        'outputs': [],
        'source': code_lines
    }],
    'metadata': {
        'kernelspec': {
            'display_name': 'Python 3',
            'language': 'python',
            'name': 'python3'
        },
        'language_info': {
            'name': 'python',
            'version': '3.10.12'
        }
    },
    'nbformat': 4,
    'nbformat_minor': 4
}

with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(clean_nb, f, indent=1)

print('Updated clean_nb.py with git reset --hard origin/main.')
