import pytest

from exercises import EXERCISES
from tests.harness import TestHarness


@pytest.mark.parametrize("ex", EXERCISES, ids=lambda ex: ex["id"])
def test_exercise(nvim, ex):
    """Verify that the answer keystrokes solve the exercise."""
    h = TestHarness(nvim)
    h.load_exercise(ex)
    h.play_and_verify(ex)
