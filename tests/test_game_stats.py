"""GameStats tests — no pygame needed."""

from game_stats import GameStats


def test_initial_score_is_zero():
    assert GameStats().score == 0


def test_initial_rockets_is_zero():
    assert GameStats().rockets == 0


def test_initial_game_active_is_false():
    assert not GameStats().game_active


def test_initial_game_started_is_false():
    assert not GameStats().game_started


def test_initial_game_over_sound_played_is_false():
    assert not GameStats().game_over_sound_played


def test_reset_clears_score():
    stats = GameStats()
    stats.score = 9999
    stats.reset_stats()
    assert stats.score == 0


def test_reset_clears_rockets():
    stats = GameStats()
    stats.rockets = 5
    stats.reset_stats()
    assert stats.rockets == 0


def test_reset_clears_game_over_sound_played():
    stats = GameStats()
    stats.game_over_sound_played = True
    stats.reset_stats()
    assert not stats.game_over_sound_played


def test_reset_does_not_change_game_active():
    stats = GameStats()
    stats.game_active = True
    stats.reset_stats()
    assert stats.game_active


def test_reset_does_not_change_game_started():
    stats = GameStats()
    stats.game_started = True
    stats.reset_stats()
    assert stats.game_started
