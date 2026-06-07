import json

import pytest
from fastapi.testclient import TestClient

from webapp.backend.main import app


@pytest.fixture()
def client(temp_state):
    return TestClient(app)


def test_state_endpoint(client):
    r = client.get("/api/state")
    assert r.status_code == 200
    body = r.json()
    assert body["target"] == 20
    assert body["total_votes"] == 0


def test_matchup_hides_models(client):
    r = client.get("/api/matchup")
    assert r.status_code == 200
    body = r.json()
    assert "left_model" not in body
    assert "right_model" not in body
    assert body["category"]
    assert body["prompt"]
    assert body["left_image"].startswith("/api/matchup-image/")


def test_matchup_image_served(client):
    m = client.get("/api/matchup").json()
    img = client.get(m["left_image"])
    assert img.status_code == 200
    assert img.headers["content-type"] == "image/png"


def test_vote_updates_state_and_reveals(client):
    m = client.get("/api/matchup").json()
    r = client.post("/api/vote", json={"matchup_id": m["matchup_id"], "choice": "left"})
    assert r.status_code == 200
    body = r.json()
    assert body["reveal"]["left_model"]
    assert body["reveal"]["winner"] == body["reveal"]["left_model"]
    assert body["state"]["total_votes"] == 1


def test_vote_unknown_matchup_404(client):
    r = client.post("/api/vote", json={"matchup_id": "nope", "choice": "left"})
    assert r.status_code == 404


def test_leaderboard_sorted_desc(client):
    rows = client.get("/api/leaderboard").json()["leaderboard"]
    ratings = [row["rating"] for row in rows]
    assert ratings == sorted(ratings, reverse=True)


def test_reset_clears_votes(client):
    m = client.get("/api/matchup").json()
    client.post("/api/vote", json={"matchup_id": m["matchup_id"], "choice": "left"})
    r = client.post("/api/reset")
    assert r.json()["total_votes"] == 0


def test_generate_streams_sse_events(client, monkeypatch):
    from webapp.backend import main

    fake_results = [
        {"model": "M1", "image_b64": "abc", "seconds": 1.0, "error": None},
        {"model": "M2", "image_b64": "xyz", "seconds": 2.0, "error": None},
    ]

    monkeypatch.setattr(main, "_get_clients", lambda: {"M1": object(), "M2": object()})
    monkeypatch.setattr(
        main.generation, "generate_stream", lambda p, c: iter(fake_results)
    )

    r = client.post("/api/generate", json={"prompt": "a fox"})
    assert r.status_code == 200
    assert "text/event-stream" in r.headers["content-type"]

    payloads = [
        line[6:]
        for line in r.text.splitlines()
        if line.startswith("data: ")
    ]
    assert payloads[-1] == "[DONE]"
    events = [json.loads(p) for p in payloads[:-1]]
    assert {e["model"] for e in events} == {"M1", "M2"}


def test_generate_requires_prompt(client):
    r = client.post("/api/generate", json={"prompt": "   "})
    assert r.status_code == 422


def test_insights_endpoint_returns_markdown(client):
    r = client.get("/api/insights")
    assert r.status_code == 200
    assert "# 🖼️ Image Model Comparison" in r.json()["markdown"]
