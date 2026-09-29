from rezept_stempel.grams import MAX_GRAMS, MIN_GRAMS, clamp_grams, step_grams


def test_clamp_snaps_and_limits() -> None:
    assert clamp_grams(7) == 5
    assert clamp_grams(8) == 10
    assert clamp_grams(0) == MIN_GRAMS
    assert clamp_grams(250) == MAX_GRAMS


def test_wheel_steps_by_five() -> None:
    assert step_grams(25, 1) == 30
    assert step_grams(25, -1) == 20
    assert step_grams(5, -1) == MIN_GRAMS
    assert step_grams(100, 1) == MAX_GRAMS
    assert step_grams(25, 0) == 25
