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
