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
