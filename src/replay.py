import json
import sys
import argparse

def replay_match(log_file):
    try:
        with open(log_file, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading {log_file}: {e}")
        return

    print("=" * 60)
    print("HACKER SOCIETY - MATCH REPLAY VIEWER")
    print("=" * 60)
    print(f"Match ID: {data.get('match_id', 'Unknown')}")
    print(f"Timestamp: {data.get('timestamp', 'Unknown')}")
    print(f"Outcome: {str(data.get('outcome', 'Unknown')).upper()}")

    rewards = data.get("rewards", {})
    shaped_rewards = data.get("shaped_rewards", {})

    print(f"Outcome Rewards: Attacker: {rewards.get('attacker', 0)}, Defender: {rewards.get('defender', 0)}")
    print(f"Shaped Rewards: Attacker: {shaped_rewards.get('attacker', 0):.2f}, Defender: {shaped_rewards.get('defender', 0):.2f}")

    print("-" * 60)

    turns = data.get("turns", [])

    if not turns:
        print("No turns recorded.")
        return

    for turn in turns:
        turn_num = turn.get("turn_number", "Unknown")
        print(f"\n--- TURN {turn_num} ---")

        events = turn.get("events", [])
        if not events:
            print("  No events.")
            continue

        for event in events:
            role = str(event.get("role", "unknown")).upper()
            agent_id = event.get("agent_id", "unknown")
            action = str(event.get("action", ""))
            reward = event.get("shaped_reward", 0.0)

            # Truncate action for better viewing if it's too long
            if len(action) > 150:
                action = action[:147] + "..."

            # Replace newlines with spaces for compact output
            action = action.replace("\n", " ")

            print(f"[{role} - {agent_id}] (Reward: {reward:+.2f}) -> {action}")

    print("\n" + "=" * 60)
    print("REPLAY COMPLETE")
    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="CLI Match Replay Viewer")
    parser.add_argument("log_file", type=str, help="Path to the match log JSON file")

    args = parser.parse_args()
    replay_match(args.log_file)

if __name__ == "__main__":
    main()
