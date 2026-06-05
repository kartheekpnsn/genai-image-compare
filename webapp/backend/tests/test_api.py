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
    assert body["target"] == 36
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
