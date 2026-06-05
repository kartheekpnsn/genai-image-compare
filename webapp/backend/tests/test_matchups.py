from webapp.backend import matchups


def test_new_matchup_has_two_distinct_models():
    store = matchups.MatchupStore()
    m = store.create(history=[])
    assert m["left_model"] != m["right_model"]
    assert m["prompt_id"].startswith("prompt-")
    assert m["matchup_id"]


def test_matchup_is_retrievable_then_resolved():
    store = matchups.MatchupStore()
    m = store.create(history=[])
    fetched = store.get(m["matchup_id"])
    assert fetched["left_model"] == m["left_model"]
    resolved = store.resolve(m["matchup_id"], "left")
    assert resolved["winner"] == m["left_model"]
    assert resolved["loser"] == m["right_model"]


def test_resolve_skip_returns_both_models_no_winner():
    store = matchups.MatchupStore()
    m = store.create(history=[])
    resolved = store.resolve(m["matchup_id"], "skip")
    assert resolved["skipped"] is True
    assert {resolved["left_model"], resolved["right_model"]} == {
        m["left_model"], m["right_model"]
    }


def test_prefers_least_seen_pair():
    # Saturate every pair except (GPT-Image, MAI-Image-2e) in history.
    models = ["GPT-Image", "MAI-Image-2.5", "MAI-Image-2.5-Flash", "MAI-Image-2e"]
    seen_pairs = [
        ("GPT-Image", "MAI-Image-2.5"),
        ("GPT-Image", "MAI-Image-2.5-Flash"),
        ("MAI-Image-2.5", "MAI-Image-2.5-Flash"),
        ("MAI-Image-2.5", "MAI-Image-2e"),
        ("MAI-Image-2.5-Flash", "MAI-Image-2e"),
    ]
    history = [{"winner": a, "loser": b, "skipped": False} for a, b in seen_pairs] * 5
    store = matchups.MatchupStore()
    chosen = store.choose_pair(models, history)
    assert set(chosen) == {"GPT-Image", "MAI-Image-2e"}
