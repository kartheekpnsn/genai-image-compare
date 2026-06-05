import pytest

from webapp.backend import paths


@pytest.fixture()
def temp_state(tmp_path, monkeypatch):
    """Point ELO state at a temp file for the duration of a test."""
    state_file = tmp_path / "elo_state.json"
    monkeypatch.setattr(paths, "ELO_STATE_FILE", state_file)
    return state_file
