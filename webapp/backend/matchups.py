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

    def _choose(self, models: list[str], prompts: list[str], history: list[dict]) -> tuple[str, str, str]:
        """Pick an unseen (prompt, pair) combination; fall back to least-seen if all 72 done."""
        seen: set[frozenset] = set()
        counts: dict[frozenset, int] = {}
        for entry in history:
            key = frozenset({entry["prompt_id"], entry["winner"], entry["loser"]})
            seen.add(key)
            counts[key] = counts.get(key, 0) + 1

        all_combos = [
            frozenset({p, a, b})
            for p in prompts
            for a, b in itertools.combinations(models, 2)
        ]
        unseen = [c for c in all_combos if c not in seen]
        pool = unseen if unseen else [min(all_combos, key=lambda c: counts.get(c, 0))]
        chosen = random.choice(pool)
        prompt_id = next(v for v in chosen if v in set(prompts))
        pair = [v for v in chosen if v != prompt_id]
        random.shuffle(pair)
        return prompt_id, pair[0], pair[1]

    def create(self, history: list[dict]) -> dict:
        """Create a new matchup and store the hidden model mapping."""
        models = data_loader.discover_models()
        prompts = list(data_loader.load_prompts().keys())
        prompt_id, left, right = self._choose(models, prompts, history)
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
