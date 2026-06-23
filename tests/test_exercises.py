import pytest

from exercises import EXERCISES
from tests.harness import ExerciseHarness, validate_answer_tokens
from trainer import VimTrainer, SessionStats


@pytest.mark.parametrize("ex", EXERCISES, ids=lambda ex: ex["id"])
def test_allowed_keys(ex):
    """Verify that every keystroke in the answer is covered by allowed_keys."""
    ok, msg = validate_answer_tokens(ex)
    assert ok, f"{ex['id']}: {msg}"


@pytest.mark.parametrize("ex", EXERCISES, ids=lambda ex: ex["id"])
def test_exercise(nvim, ex):
    """Verify that the answer keystrokes solve the exercise."""
    h = ExerciseHarness(nvim)
    h.load_exercise(ex)
    h.play_and_verify(ex)


@pytest.mark.parametrize("ex", EXERCISES, ids=lambda ex: ex["id"])
def test_statusline_no_crash(nvim, ex):
    """_update_status must not crash when allowed_keys contains < >."""
    h = ExerciseHarness(nvim)
    h.load_exercise(ex)
    trainer = VimTrainer(nvim=nvim)
    if "targets" in ex:
        stats = SessionStats(targets_total=len(ex["targets"]))
        trainer._update_status(ex, stats, 0)
