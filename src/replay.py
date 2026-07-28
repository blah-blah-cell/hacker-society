import json
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="Match Replay Viewer")
    parser.add_argument("log_file", help="Path to the match JSON log file")
    args = parser.parse_args()

    try:
        with open(args.log_file, "r") as f:
            log_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Log file not found: {args.log_file}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Could not parse JSON from {args.log_file}")
        sys.exit(1)

    print(f"--- MATCH REPLAY STARTING: {log_data.get('match_id', 'Unknown')} ---")
    print(f"Outcome: {log_data.get('outcome', 'Unknown')}")
    print(f"Flag Hash: {log_data.get('secret_flag_sha256', 'Unknown')}\n")

    turns = log_data.get("turns", [])
    if not turns:
        print("No turns found in the log.")
        return

    for turn in turns:
        turn_number = turn.get("turn_number", "?")
        print(f"=== TURN {turn_number} ===")
        events = turn.get("events", [])

        # Display defender events first, then attacker, as they are usually ordered
        for event in events:
            role = event.get("role", "Unknown").upper()
            agent_id = event.get("agent_id", "Unknown")
            action = event.get("action", "")
            reward = event.get("shaped_reward", 0.0)

            print(f"[{agent_id.upper()} ({role})] Reward: {reward:+.2f}")
            print(f"Action: {action}")
            print("-" * 40)

        print("\nPress Enter to continue to next turn...", end="", flush=True)
        try:
            input()
        except EOFError:
            print("\nReplay interrupted.")
            break

    print("\n--- MATCH REPLAY FINISHED ---")

if __name__ == "__main__":
    main()
