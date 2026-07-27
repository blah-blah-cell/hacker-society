import json
import os
import sys


def replay_match(log_file: str):
    if not os.path.exists(log_file):
        print(f"Error: Log file '{log_file}' not found.")
        sys.exit(1)

    with open(log_file, 'r') as f:
        try:
            match_data = json.load(f)
        except json.JSONDecodeError:
            print(f"Error: Failed to parse JSON from '{log_file}'.")
            sys.exit(1)

    print("=" * 60)
    print(f"Match ID: {match_data.get('match_id', 'UNKNOWN')}")
    print(f"Outcome: {match_data.get('outcome', 'UNKNOWN').upper()}")

    rewards = match_data.get('rewards', {})
    print(f"Final Rewards - Attacker: {rewards.get('attacker', 0.0)} | Defender: {rewards.get('defender', 0.0)}")

    shaped_rewards = match_data.get('shaped_rewards', {})
    if shaped_rewards:
        print(f"Shaped Rewards - Attacker: {shaped_rewards.get('attacker', 0.0):.2f} | Defender: {shaped_rewards.get('defender', 0.0):.2f}")

    print("=" * 60)

    turns = match_data.get('turns', [])
    if not turns:
        print("No turns recorded in this match.")
        return

    for turn in turns:
        turn_num = turn.get('turn_number', '?')
        print(f"\n--- Turn {turn_num} ---")

        events = turn.get('events', [])
        for event in events:
            role = event.get('role', 'unknown').upper()
            agent_id = event.get('agent_id', 'unknown')
            action = event.get('action', '')
            reward = event.get('shaped_reward', 0.0)

            print(f"[{role} - {agent_id}] (Reward: {reward:.2f})")
            if action:
                print(f"Action: {action.strip()}")
            else:
                print("Action: <None>")
            print("-" * 30)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 -m src.replay <path_to_match_log.json>")
        sys.exit(1)

    log_path = sys.argv[1]
    replay_match(log_path)
