import json
import sys
import os
import argparse
from typing import Dict, Any

def display_replay(filepath: str) -> None:
    if not os.path.exists(filepath):
        print(f"Error: Log file '{filepath}' not found.")
        sys.exit(1)

    try:
        with open(filepath, 'r') as f:
            data: Dict[str, Any] = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Log file '{filepath}' is not valid JSON.")
        sys.exit(1)

    print(f"--- REPLAY FOR MATCH {data.get('match_id', 'UNKNOWN')} ---")
    print(f"Outcome: {data.get('outcome', 'Unknown').upper()}")

    turns = data.get('turns', [])
    if not turns:
        print("No turns found in this match.")
        return

    for turn in turns:
        print(f"\n=== TURN {turn.get('turn_number', '?')} ===")
        events = turn.get('events', [])
        for event in events:
            role = event.get('role', 'Unknown').upper()
            agent_id = event.get('agent_id', 'Unknown')
            action = event.get('action', '')
            reward = event.get('shaped_reward', 0.0)
            print(f"[{agent_id} ({role}) | Reward: {reward:.2f}]:\n{action}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Replay a Hacker Society match from a JSON log file.")
    parser.add_argument("log_file", help="Path to the JSON log file to replay.")
    args = parser.parse_args()

    display_replay(args.log_file)
