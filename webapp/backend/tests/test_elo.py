from webapp.backend import elo


def test_expected_score_equal_ratings_is_half():
    assert elo.expected_score(1000, 1000) == 0.5


def test_expected_score_higher_rating_favored():
    assert elo.expected_score(1200, 1000) > 0.5


def test_update_ratings_winner_gains_loser_loses():
    new_w, new_l = elo.update_ratings(1000, 1000)
    assert new_w == 1016.0   # 1000 + 32 * (1 - 0.5)
    assert new_l == 984.0    # 1000 + 32 * (0 - 0.5)


def test_update_ratings_zero_sum():
    new_w, new_l = elo.update_ratings(1050, 980)
    assert round((new_w - 1050) + (new_l - 980), 6) == 0.0


def test_load_state_initializes_when_missing(temp_state):
    state = elo.load_state()
    assert state["target"] == 36
    assert state["total_votes"] == 0
    assert set(state["models"]) == {
        "GPT-Image", "MAI-Image-2.5", "MAI-Image-2.5-Flash", "MAI-Image-2e",
    }
    assert state["models"]["GPT-Image"]["rating"] == 1000.0
    assert state["history"] == []


def test_record_vote_updates_ratings_and_counts(temp_state):
    elo.load_state()
    result = elo.record_vote("GPT-Image", "MAI-Image-2e", skipped=False)
    assert result["models"]["GPT-Image"]["rating"] == 1016.0
    assert result["models"]["GPT-Image"]["wins"] == 1
    assert result["models"]["MAI-Image-2e"]["losses"] == 1
    assert result["total_votes"] == 1
    assert result["history"][-1]["winner"] == "GPT-Image"


def test_record_skip_changes_no_rating(temp_state):
    elo.load_state()
    result = elo.record_vote("GPT-Image", "MAI-Image-2e", skipped=True)
    assert result["models"]["GPT-Image"]["rating"] == 1000.0
    assert result["models"]["GPT-Image"]["skips"] == 1
    assert result["models"]["MAI-Image-2e"]["skips"] == 1
    assert result["total_votes"] == 1


def test_reset_restores_base(temp_state):
    elo.load_state()
    elo.record_vote("GPT-Image", "MAI-Image-2e", skipped=False)
    state = elo.reset_state()
    assert state["total_votes"] == 0
    assert state["history"] == []
    assert all(m["rating"] == 1000.0 for m in state["models"].values())
    assert state["target"] == 36  # preserved


def test_state_persists_to_disk(temp_state):
    elo.load_state()
    elo.record_vote("GPT-Image", "MAI-Image-2e", skipped=False)
    reloaded = elo.load_state()
    assert reloaded["total_votes"] == 1
