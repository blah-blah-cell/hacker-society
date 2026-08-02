import json
import sys
import os

def replay_match(log_path: str):
    if not os.path.exists(log_path):
        print(f"Error: Log file {log_path} not found.")
        sys.exit(1)

    with open(log_path, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print(f"Error: Could not parse JSON from {log_path}")
            sys.exit(1)

    print(f"--- MATCH REPLAY: {data.get('match_id', 'unknown')} ---")
    print(f"Outcome: {data.get('outcome', 'unknown')}")
    print(f"Timestamp: {data.get('timestamp', 'unknown')}\n")

    turns = data.get("turns", [])
    if not turns:
        print("No turns found in this match.")
        return

    for turn in turns:
        print(f"=== TURN {turn.get('turn_number')} ===")
        events = turn.get("events", [])
        for event in events:
            agent = event.get("agent_id", "unknown")
            role = event.get("role", "unknown")
            action = event.get("action", "")
            print(f"[{agent.upper()}] ({role}):\n{action}\n")

    print(f"--- REPLAY COMPLETE ---")
    print(f"Final Rewards: {json.dumps(data.get('rewards', {}))}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python src/replay.py <path_to_log_json>")
        sys.exit(1)

    replay_match(sys.argv[1])
