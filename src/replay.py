import argparse
import json
import os
import sys

def replay_match(log_path: str):
    if not os.path.exists(log_path):
        print(f"Error: Log file '{log_path}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(log_path, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        sys.exit(1)

    match_id = data.get("match_id", "Unknown")
    timestamp = data.get("timestamp", "Unknown")
    outcome = data.get("outcome", "Unknown")
    rewards = data.get("rewards", {})
    shaped = data.get("shaped_rewards", {})

    print("=" * 60)
    print(f" MATCH REPLAY: {match_id}")
    print(f" Timestamp: {timestamp}")
    print(f" Outcome:   {outcome.upper()}")
    print("=" * 60)

    turns = data.get("turns", [])
    for turn in turns:
        turn_num = turn.get("turn_number", "?")
        print(f"\n--- TURN {turn_num} ---")
        for event in turn.get("events", []):
            role = event.get("role", "unknown")
            agent_id = event.get("agent_id", "unknown")
            action = event.get("action", "")
            reward = event.get("shaped_reward", 0.0)

            color = "\033[91m" if role == "attacker" else "\033[94m"
            reset = "\033[0m"

            print(f"{color}[{role.upper()} | {agent_id}] (Reward: {reward:.2f}){reset}")

            if not action.strip():
                print("  <no action recorded>")
            else:
                for line in action.splitlines():
                    print(f"  {line}")

    print("\n" + "=" * 60)
    print(" MATCH SUMMARY")
    print("=" * 60)
    print(f"Outcome: {outcome.upper()}")
    print("Binary Rewards:")
    print(f"  Attacker: {rewards.get('attacker', 0.0)}")
    print(f"  Defender: {rewards.get('defender', 0.0)}")
    print("Shaped Rewards:")
    print(f"  Attacker: {shaped.get('attacker', 0.0):.2f}")
    print(f"  Defender: {shaped.get('defender', 0.0):.2f}")
    print("=" * 60 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Replay a Hacker Society match log.")
    parser.add_argument("log_file", type=str, help="Path to the match log JSON file (e.g., logs/match_123_log.json)")
    args = parser.parse_args()

    replay_match(args.log_file)

if __name__ == "__main__":
    main()
