"""In-memory matchup store: pairing selection and side resolution.

Models are kept server-side keyed by matchup_id so the client never learns
which model produced which image until after voting.
"""

from __future__ import annotations

import itertools
import random
import uuid

from webapp.backend import data_loader


class MatchupStore:
    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    def choose_pair(self, models: list[str], history: list[dict]) -> tuple[str, str]:
        """Pick the model pair that has appeared least often in history."""
        counts: dict[frozenset[str], int] = {
            frozenset(pair): 0 for pair in itertools.combinations(models, 2)
        }
        for entry in history:
            key = frozenset({entry["winner"], entry["loser"]})
            if key in counts:
                counts[key] += 1
        fewest = min(counts.values())
        candidates = [pair for pair, c in counts.items() if c == fewest]
        chosen = list(random.choice(candidates))
        random.shuffle(chosen)
        return chosen[0], chosen[1]

    def create(self, history: list[dict]) -> dict:
        """Create a new matchup and store the hidden model mapping."""
        models = data_loader.discover_models()
        prompt_id = random.choice(list(data_loader.load_prompts().keys()))
        left, right = self.choose_pair(models, history)
        matchup_id = uuid.uuid4().hex
        record = {
            "matchup_id": matchup_id,
            "prompt_id": prompt_id,
            "left_model": left,
            "right_model": right,
        }
        self._store[matchup_id] = record
        return record

    def get(self, matchup_id: str) -> dict | None:
        return self._store.get(matchup_id)

    def resolve(self, matchup_id: str, choice: str) -> dict | None:
        """Translate a left/right/skip choice into winner/loser models."""
        record = self._store.get(matchup_id)
        if record is None:
            return None
        left, right = record["left_model"], record["right_model"]
        if choice == "skip":
            result = {"skipped": True, "winner": None, "loser": None}
        elif choice == "left":
            result = {"skipped": False, "winner": left, "loser": right}
        elif choice == "right":
            result = {"skipped": False, "winner": right, "loser": left}
        else:
            return None
        result.update(
            {"left_model": left, "right_model": right,
             "prompt_id": record["prompt_id"]}
        )
        return result
