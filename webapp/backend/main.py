"""FastAPI application: model ranking, generation, and insights endpoints."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from webapp.backend import data_loader, elo, matchups

app = FastAPI(title="GenAI Image Compare")
_store = matchups.MatchupStore()


class VoteRequest(BaseModel):
    matchup_id: str
    choice: str  # "left" | "right" | "skip"


def _leaderboard(state: dict) -> list[dict]:
    rows = [
        {"model": name, **stats} for name, stats in state["models"].items()
    ]
    rows.sort(key=lambda r: r["rating"], reverse=True)
    for i, row in enumerate(rows, start=1):
        row["rank"] = i
    return rows


@app.get("/api/state")
def get_state() -> dict:
    return elo.load_state()


@app.get("/api/leaderboard")
def get_leaderboard() -> dict:
    state = elo.load_state()
    return {"leaderboard": _leaderboard(state), "total_votes": state["total_votes"],
            "target": state["target"]}


@app.get("/api/matchup")
def get_matchup() -> dict:
    state = elo.load_state()
    record = _store.create(state["history"])
    prompt = data_loader.load_prompts()[record["prompt_id"]]
    mid = record["matchup_id"]
    return {
        "matchup_id": mid,
        "prompt_id": record["prompt_id"],
        "category": prompt["category"],
        "prompt": prompt["prompt"],
        "left_image": f"/api/matchup-image/{mid}/left",
        "right_image": f"/api/matchup-image/{mid}/right",
    }


@app.get("/api/matchup-image/{matchup_id}/{side}")
def get_matchup_image(matchup_id: str, side: str) -> FileResponse:
    record = _store.get(matchup_id)
    if record is None or side not in ("left", "right"):
        raise HTTPException(status_code=404, detail="Unknown matchup or side")
    model = record["left_model"] if side == "left" else record["right_model"]
    path = data_loader.image_path(model, record["prompt_id"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path, media_type="image/png")


@app.post("/api/vote")
def post_vote(req: VoteRequest) -> dict:
    resolved = _store.resolve(req.matchup_id, req.choice)
    if resolved is None:
        raise HTTPException(status_code=404, detail="Unknown matchup or choice")
    if resolved["skipped"]:
        state = elo.record_vote(resolved["left_model"], resolved["right_model"],
                                skipped=True)
    else:
        state = elo.record_vote(resolved["winner"], resolved["loser"],
                                skipped=False)
    return {"state": state, "leaderboard": _leaderboard(state), "reveal": resolved}


@app.post("/api/reset")
def post_reset() -> dict:
    return elo.reset_state()
