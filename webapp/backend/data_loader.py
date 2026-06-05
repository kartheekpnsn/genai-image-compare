"""Load prompts and discover model image folders from the data directory."""

from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path

from webapp.backend import paths


@lru_cache(maxsize=1)
def load_prompts() -> dict[str, dict[str, str]]:
    """Return {prompt_id: {"category": ..., "prompt": ...}} from prompts.csv."""
    prompts: dict[str, dict[str, str]] = {}
    with paths.PROMPTS_CSV.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            prompts[row["ID"]] = {
                "category": row["Category"],
                "prompt": row["Prompt"],
            }
    return prompts


@lru_cache(maxsize=1)
def discover_models() -> list[str]:
    """Return sorted model names from the image subfolders."""
    return sorted(p.name for p in paths.IMAGES_DIR.iterdir() if p.is_dir())


def image_path(model: str, prompt_id: str) -> Path:
    """Return the PNG path for a model/prompt pair."""
    return paths.IMAGES_DIR / model / f"{prompt_id}.png"
