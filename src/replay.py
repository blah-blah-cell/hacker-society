import argparse
import json
import os
import sys
import time

def load_log(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Log file '{filepath}' not found.")
    with open(filepath, "r") as f:
        return json.load(f)

def print_turn(turn_data):
    turn_num = turn_data.get("turn_number", "?")
    print(f"\n{'='*20} TURN {turn_num} {'='*20}")

    events = turn_data.get("events", [])
    if not events:
        print("No events in this turn.")
        return

    for event in events:
        role = event.get("role", "unknown")
        agent_id = event.get("agent_id", "unknown")
        action = event.get("action", "")
        reward = event.get("shaped_reward", 0.0)

        print(f"\n[{agent_id.upper()} ({role})] (Reward: {reward:.2f})")
        print(f"Action: {action}")

def replay_match(filepath, delay=0):
    match_data = load_log(filepath)

    match_id = match_data.get("match_id", "Unknown")
    outcome = match_data.get("outcome", "Unknown")

    print(f"\nStarting Replay for Match: {match_id}")
    print(f"Outcome: {outcome}")

    turns = match_data.get("turns", [])
    for turn in turns:
        print_turn(turn)
        if delay > 0:
            time.sleep(delay)
        else:
            input("\nPress Enter to continue to next turn...")

    print("\nReplay finished.")

def main():
    parser = argparse.ArgumentParser(description="Replay a Hacker Society match from a JSON log file.")
    parser.add_argument("log_file", type=str, help="Path to the JSON log file.")
    parser.add_argument("--delay", type=float, default=0, help="Delay between turns in seconds (0 for manual progression).")

    args = parser.parse_args()

    try:
        replay_match(args.log_file, args.delay)
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{args.log_file}'.")
        sys.exit(1)

if __name__ == "__main__":
    main()
