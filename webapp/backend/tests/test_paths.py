from webapp.backend import paths


def test_repo_root_contains_pyproject():
    assert (paths.REPO_ROOT / "pyproject.toml").exists()


def test_data_dir_points_at_data():
    assert paths.DATA_DIR == paths.REPO_ROOT / "data"
    assert paths.IMAGES_DIR == paths.REPO_ROOT / "data" / "images"
    assert paths.PROMPTS_CSV == paths.REPO_ROOT / "data" / "prompts" / "prompts.csv"
    assert paths.ELO_STATE_FILE == paths.REPO_ROOT / "data" / "elo_state.json"
    assert paths.INSIGHTS_MD == paths.REPO_ROOT / "docs" / "INSIGHTS.md"
