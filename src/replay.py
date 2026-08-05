import json
import os
import sys

def replay_match(filepath: str):
    if not os.path.exists(filepath):
        print(f"Error: Log file {filepath} not found.")
        sys.exit(1)
        return

    with open(filepath, 'r') as f:
        try:
            log_data = json.load(f)
        except json.JSONDecodeError:
            print(f"Error: {filepath} is not a valid JSON file.")
            sys.exit(1)
            return

    match_id = log_data.get("match_id", "Unknown")
    timestamp = log_data.get("timestamp", "Unknown")
    outcome = log_data.get("outcome", "Unknown")
    turns = log_data.get("turns", [])

    print(f"=== REPLAY: Match {match_id} ===")
    print(f"Timestamp: {timestamp}")
    print(f"Outcome: {outcome.upper()}")
    print("-" * 40)

    for turn in turns:
        turn_number = turn.get("turn_number", "?")
        print(f"\n[Turn {turn_number}]")
        events = turn.get("events", [])

        for event in events:
            role = event.get("role", "unknown").upper()
            agent_id = event.get("agent_id", "unknown")
            action = event.get("action", "")
            reward = event.get("shaped_reward", 0.0)

            print(f"  [{role} | {agent_id} | Reward: {reward:+.2f}]")
            print(f"  Action: {action.strip()}")
            print()

    print("=== REPLAY COMPLETE ===")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 src/replay.py logs/match_<id>_log.json")
        sys.exit(1)

    replay_match(sys.argv[1])
