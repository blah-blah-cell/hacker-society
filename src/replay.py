import sys
import json
import argparse


def main():
    parser = argparse.ArgumentParser(description="Hacker Society CLI Match Replay Viewer")
    parser.add_argument("log_file", type=str, help="Path to the JSON match log file")
    args = parser.parse_args()

    try:
        with open(args.log_file, 'r') as f:
            logs = json.load(f)
    except FileNotFoundError:
        print(f"Error: Log file not found: {args.log_file}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in log file: {args.log_file}")
        sys.exit(1)

    print(f"=== Match Replay Viewer ===")
    print(f"Match ID: {logs.get('match_id', 'Unknown')}")
    print(f"Outcome: {logs.get('outcome', 'Unknown')}")
    print(f"Rewards: {logs.get('rewards', {})}")
    print("=" * 27)

    turns = logs.get("turns", [])
    if not turns:
        print("No turns recorded in the log.")
        return

    for turn in turns:
        turn_number = turn.get("turn_number", "?")
        print(f"\n--- Turn {turn_number} ---")
        events = turn.get("events", [])
        if not events:
            print("  No events in this turn.")
            continue

        for event in events:
            agent_id = event.get("agent_id", "Unknown")
            role = event.get("role", "Unknown").upper()
            action = event.get("action", "")
            print(f"[{agent_id} ({role})]:\n{action}\n")

if __name__ == "__main__":
    main()
