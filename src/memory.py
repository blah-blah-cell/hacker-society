import json
import os

class MemoryStore:
    def __init__(self, filepath="memory.json"):
        self.filepath = filepath
        self._memory = self._load_memory()

    def _load_memory(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {"attacker": [], "defender": []}
        return {"attacker": [], "defender": []}

    def _save_memory(self):
        with open(self.filepath, "w") as f:
            json.dump(self._memory, f, indent=2)

    def add_memory(self, role: str, summary: str):
        if role not in self._memory:
            self._memory[role] = []
        self._memory[role].append(summary)
        self._save_memory()

    def get_memory(self, role: str) -> list:
        return self._memory.get(role, [])

    def search_memory(self, role: str, query: str) -> list:
        """
        A simple keyword-based search for the optional memory tool.
        """
        memories = self.get_memory(role)
        query_terms = query.lower().split()
        results = []
        for memory in memories:
            if any(term in memory.lower() for term in query_terms):
                results.append(memory)
        return results
