"""
src/export_dataset.py — Cyber Range Dataset Exporter

Exports match trajectories into:
1. ShareGPT format for SFT (Supervised Fine-Tuning)
2. Pairwise DPO format (`prompt`, `chosen`, `rejected`) for Direct Preference Optimization
"""

import json
import os
import glob
import argparse


def export_to_sharegpt(logs_dir="logs", output_file="dataset_sft.jsonl"):
    print(f"Exporting SFT logs from {logs_dir} to {output_file}...")
    dataset = []

    for log_file in glob.glob(os.path.join(logs_dir, "*.json")):
        try:
            with open(log_file, "r") as f:
                match_data = json.load(f)
        except Exception:
            continue

        rewards = match_data.get("rewards", {"attacker": 0.0, "defender": 0.0})
        turns = match_data.get("turns", [])

        # Attacker trace
        attacker_conversations = []
        for turn in turns:
            turn_num = turn.get("turn_number", 1)
            for event in turn.get("events", []):
                if event.get("role") == "attacker":
                    action = event.get("action", "")
                    if action:
                        attacker_conversations.append({
                            "from": "human",
                            "value": f"Turn {turn_num}: Execute next action to compromise target and exfiltrate flag."
                        })
                        attacker_conversations.append({
                            "from": "gpt",
                            "value": action
                        })

        if attacker_conversations:
            dataset.append({
                "match_id": match_data.get("match_id"),
                "agent_role": "attacker",
                "conversations": attacker_conversations,
                "reward": rewards.get("attacker", 0.0)
            })

    with open(output_file, "w") as out:
        for entry in dataset:
            out.write(json.dumps(entry) + "\n")

    print(f"Successfully exported {len(dataset)} SFT conversation traces to {output_file}.")


def export_to_dpo(logs_dir="logs", output_file="dataset_dpo.jsonl"):
    print(f"Exporting DPO preference dataset from {logs_dir} to {output_file}...")
    dpo_dataset = []

    for log_file in glob.glob(os.path.join(logs_dir, "*.json")):
        try:
            with open(log_file, "r") as f:
                match_data = json.load(f)
        except Exception:
            continue

        turns = match_data.get("turns", [])
        for turn in turns:
            turn_num = turn.get("turn_number", 1)
            events = turn.get("events", [])

            # Group events by role
            attacker_events = [e for e in events if e.get("role") == "attacker"]
            defender_events = [e for e in events if e.get("role") == "defender"]

            for role, evs in [("attacker", attacker_events), ("defender", defender_events)]:
                if not evs:
                    continue

                # Sort by shaped_reward
                sorted_evs = sorted(evs, key=lambda x: x.get("shaped_reward", 0.0), reverse=True)
                if len(sorted_evs) >= 2 and sorted_evs[0].get("shaped_reward", 0.0) > sorted_evs[-1].get("shaped_reward", 0.0):
                    prompt = f"Role: {role.upper()} | Turn: {turn_num}\nChoose the optimal bash command for this tactical scenario."
                    chosen = sorted_evs[0].get("action", "")
                    rejected = sorted_evs[-1].get("action", "")

                    if chosen and rejected and chosen != rejected:
                        dpo_dataset.append({
                            "prompt": prompt,
                            "chosen": chosen,
                            "rejected": rejected,
                            "match_id": match_data.get("match_id"),
                            "role": role
                        })

    with open(output_file, "w") as out:
        for entry in dpo_dataset:
            out.write(json.dumps(entry) + "\n")

    print(f"Successfully exported {len(dpo_dataset)} DPO preference pairs to {output_file}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export Hacker Society Match Telemetry")
    parser.add_argument("--logs-dir", type=str, default="logs", help="Directory containing match JSON logs")
    parser.add_argument("--format", type=str, choices=["sft", "dpo", "all"], default="all", help="Output format")
    args = parser.parse_args()

    if args.format in ["sft", "all"]:
        export_to_sharegpt(args.logs_dir, "dataset_sft.jsonl")
    if args.format in ["dpo", "all"]:
        export_to_dpo(args.logs_dir, "dataset_dpo.jsonl")
