"""ELO rating math and persistent state for the model ranking page."""

from __future__ import annotations

BASE_RATING = 1000.0
K_FACTOR = 32.0


def expected_score(rating_a: float, rating_b: float) -> float:
    """Expected score for A against B (0..1)."""
    return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))


def update_ratings(winner: float, loser: float) -> tuple[float, float]:
    """Return (new_winner, new_loser) after a decisive result."""
    exp_w = expected_score(winner, loser)
    exp_l = expected_score(loser, winner)
    new_w = winner + K_FACTOR * (1.0 - exp_w)
    new_l = loser + K_FACTOR * (0.0 - exp_l)
    return new_w, new_l


import json

from webapp.backend import data_loader, paths

DEFAULT_TARGET = 36


def _initial_state() -> dict:
    return {
        "target": DEFAULT_TARGET,
        "total_votes": 0,
        "models": {
            model: {"rating": BASE_RATING, "games": 0, "wins": 0,
                    "losses": 0, "skips": 0}
            for model in data_loader.discover_models()
        },
        "history": [],
    }


def _write(state: dict) -> dict:
    paths.ELO_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    paths.ELO_STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state


def load_state() -> dict:
    """Load ELO state from disk, initializing the file if it is missing."""
    if not paths.ELO_STATE_FILE.exists():
        return _write(_initial_state())
    return json.loads(paths.ELO_STATE_FILE.read_text(encoding="utf-8"))


def reset_state() -> dict:
    """Reset ratings/counters to base, preserving the configured target."""
    state = load_state()
    fresh = _initial_state()
    fresh["target"] = state.get("target", DEFAULT_TARGET)
    return _write(fresh)


def record_vote(winner: str, loser: str, *, skipped: bool) -> dict:
    """Apply a vote (or skip) to disk-backed state and return the new state."""
    state = load_state()
    models = state["models"]
    if skipped:
        models[winner]["skips"] += 1
        models[loser]["skips"] += 1
    else:
        new_w, new_l = update_ratings(models[winner]["rating"],
                                      models[loser]["rating"])
        models[winner]["rating"] = round(new_w, 2)
        models[loser]["rating"] = round(new_l, 2)
        models[winner]["wins"] += 1
        models[loser]["losses"] += 1
        models[winner]["games"] += 1
        models[loser]["games"] += 1
    state["total_votes"] += 1
    state["history"].append(
        {"winner": winner, "loser": loser, "skipped": skipped}
    )
    return _write(state)
