import json
import os
import sys
import glob

def find_latest_log(logs_dir: str = "logs") -> str | None:
    """Find the most recently modified match log file."""
    if not os.path.exists(logs_dir):
        return None
    files = glob.glob(os.path.join(logs_dir, "*.json"))
    if not files:
        return None
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

def replay_match(filepath: str):
    if not os.path.exists(filepath):
        print(f"Error: Log file {filepath} not found.")
        sys.exit(1)
        return

    with open(filepath, 'r', encoding='utf-8') as f:
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
    shaped_rewards = log_data.get("shaped_rewards", {})

    print(f"=== REPLAY: Match {match_id} ===")
    print(f"Timestamp: {timestamp}")
    print(f"Outcome: {outcome.upper()}")
    if shaped_rewards:
        print(f"Rewards: Attacker: {shaped_rewards.get('attacker', 0.0):+.2f} | Defender: {shaped_rewards.get('defender', 0.0):+.2f}")
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

    print("============================================================")
    print(f"   REPLAY COMPLETE: Total Turns Replayed: {len(turns)}")
    print("============================================================")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        latest = find_latest_log()
        if latest:
            print(f"No log specified. Automatically replaying most recent match: {latest}\n")
            replay_match(latest)
        else:
            print("No match logs found in 'logs/'.")
            print("Usage: python -m src.replay logs/match_<id>_log.json")
            sys.exit(1)
    else:
        replay_match(sys.argv[1])
