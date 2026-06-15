import json
import os
import threading


class MemoryStore:
    def __init__(self, filepath="memory.json"):
        self.filepath = filepath
        self._lock = threading.Lock()   # FIX: guard concurrent file writes
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
        """Must be called while holding self._lock."""
        with open(self.filepath, "w") as f:
            json.dump(self._memory, f, indent=2)

    def add_memory(self, role: str, summary: str):
        with self._lock:
            if role not in self._memory:
                self._memory[role] = []
            self._memory[role].append(summary)
            self._save_memory()

    def get_memory(self, role: str) -> list:
        with self._lock:
            return list(self._memory.get(role, []))

    def search_memory(self, role: str, query: str) -> list:
        """
        Keyword-based search with TF-IDF-style term frequency scoring.
        Returns results sorted by relevance (most matching terms first).
        """
        memories = self.get_memory(role)
        query_terms = set(query.lower().split())
        scored = []
        for memory in memories:
            memory_lower = memory.lower()
            score = sum(1 for term in query_terms if term in memory_lower)
            if score > 0:
                scored.append((score, memory))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored]
