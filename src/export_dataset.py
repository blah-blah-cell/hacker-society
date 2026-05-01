import json
import os
import glob

def export_to_sharegpt(logs_dir="logs", output_file="dataset.jsonl"):
    print(f"Exporting logs from {logs_dir} to {output_file}...")
    dataset = []

    for log_file in glob.glob(os.path.join(logs_dir, "*.json")):
        try:
            with open(log_file, "r") as f:
                match_data = json.load(f)
        except json.JSONDecodeError:
            print(f"Skipping invalid JSON file: {log_file}")
            continue

        rewards = match_data.get("rewards", {"attacker": 0.0, "defender": 0.0})
        turns = match_data.get("turns", [])

        # We can extract conversation for the attacker and defender separately
        # Attacker trace
        attacker_conversations = []
        for turn in turns:
            for event in turn.get("events", []):
                if event.get("role") == "attacker":
                    # Map 'attacker' to 'assistant' (since the model plays this role)
                    attacker_conversations.append({
                        "from": "gpt",
                        "value": event.get("action", "")
                    })
                elif event.get("role") == "defender":
                    # Actions from the other side or environment might be "user" or environment feedback
                    # For a simple format, we just keep the assistant's actions and assume prompts are tracked elsewhere or implicitly
                    pass

        if attacker_conversations:
            dataset.append({
                "match_id": match_data.get("match_id"),
                "agent_role": "attacker",
                "conversations": attacker_conversations,
                "reward": rewards.get("attacker", 0.0)
            })

        # Defender trace
        defender_conversations = []
        for turn in turns:
            for event in turn.get("events", []):
                if event.get("role") == "defender":
                    defender_conversations.append({
                        "from": "gpt",
                        "value": event.get("action", "")
                    })

        if defender_conversations:
            dataset.append({
                "match_id": match_data.get("match_id"),
                "agent_role": "defender",
                "conversations": defender_conversations,
                "reward": rewards.get("defender", 0.0)
            })

    with open(output_file, "w") as out:
        for entry in dataset:
            out.write(json.dumps(entry) + "\n")

    print(f"Successfully exported {len(dataset)} conversation traces to {output_file}.")

if __name__ == "__main__":
    export_to_sharegpt()
