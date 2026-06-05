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


def test_no_repeat_within_72_combos():
    # After 71 unique (prompt, pair) combos in history, the 72nd must be unseen.
    models = ["GPT-Image", "MAI-Image-2.5", "MAI-Image-2.5-Flash", "MAI-Image-2e"]
    prompts = [f"prompt-{i}" for i in range(1, 13)]
    import itertools
    all_combos = [
        (p, a, b)
        for p in prompts
        for a, b in itertools.combinations(models, 2)
    ]
    # fill history with the first 71 combos
    history = [
        {"prompt_id": p, "winner": a, "loser": b, "skipped": False}
        for p, a, b in all_combos[:71]
    ]
    store = matchups.MatchupStore()
    p, left, right = store._choose(models, prompts, history)
    missing_p, missing_a, missing_b = all_combos[71]
    assert p == missing_p
    assert {left, right} == {missing_a, missing_b}


def test_no_repeat_in_20_sequential_creates():
    store = matchups.MatchupStore()
    history: list[dict] = []
    seen: set[frozenset] = set()
    for _ in range(20):
        m = store.create(history)
        key = frozenset({m["prompt_id"], m["left_model"], m["right_model"]})
        assert key not in seen, f"Repeat: {m['prompt_id']} {m['left_model']} vs {m['right_model']}"
        seen.add(key)
        history.append({"prompt_id": m["prompt_id"], "winner": m["left_model"],
                        "loser": m["right_model"], "skipped": False})
