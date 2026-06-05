"""Filesystem locations used by the backend, resolved from the repo root."""

from __future__ import annotations

from pathlib import Path

# webapp/backend/paths.py -> parents[2] is the repository root.
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
IMAGES_DIR = DATA_DIR / "images"
PROMPTS_CSV = DATA_DIR / "prompts" / "prompts.csv"
ELO_STATE_FILE = DATA_DIR / "elo_state.json"
INSIGHTS_MD = REPO_ROOT / "docs" / "INSIGHTS.md"
