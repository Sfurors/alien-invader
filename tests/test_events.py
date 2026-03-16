"""Event handler tests — events injected via pygame.event.post."""

import pygame
import events


def _post(key):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))


def _post_up(key):
    pygame.event.post(pygame.event.Event(pygame.KEYUP, key=key))


# ── Movement flags ───────────────────────────────────────────────────────────


def test_keydown_right_sets_moving_right(ctx):
    ctx.stats.game_active = True
    _post(pygame.K_RIGHT)
    events.check_events(ctx)
    assert ctx.ship.moving_right


def test_keydown_left_sets_moving_left(ctx):
    ctx.stats.game_active = True
    _post(pygame.K_LEFT)
    events.check_events(ctx)
    assert ctx.ship.moving_left


def test_keyup_right_clears_moving_right(ctx):
    ctx.ship.moving_right = True
    ctx.stats.game_active = True
    _post_up(pygame.K_RIGHT)
    events.check_events(ctx)
    assert not ctx.ship.moving_right


def test_keyup_left_clears_moving_left(ctx):
    ctx.ship.moving_left = True
    ctx.stats.game_active = True
    _post_up(pygame.K_LEFT)
    events.check_events(ctx)
    assert not ctx.ship.moving_left


# ── Firing ───────────────────────────────────────────────────────────────────


def test_space_fires_bullet_when_active(ctx):
    ctx.stats.game_active = True
    _post(pygame.K_SPACE)
    events.check_events(ctx)
    assert len(ctx.bullets) == 1


def test_space_respects_bullets_allowed_limit(ctx):
    ctx.stats.game_active = True
    # Fill up to the limit first
    from bullet import Bullet

    for _ in range(ctx.settings.bullets_allowed):
        ctx.bullets.add(Bullet(ctx.settings, ctx.screen, ctx.ship))
    _post(pygame.K_SPACE)
    events.check_events(ctx)
    assert len(ctx.bullets) == ctx.settings.bullets_allowed  # not exceeded


def test_space_plays_shoot_sound(ctx):
    ctx.stats.game_active = True
    _post(pygame.K_SPACE)
    events.check_events(ctx)
    ctx.sounds["shoot"].play.assert_called_once()


# ── Start / Restart ──────────────────────────────────────────────────────────


def test_enter_starts_game_when_inactive(ctx):
    ctx.stats.game_active = False
    _post(pygame.K_RETURN)
    events.check_events(ctx)
    assert ctx.stats.game_active


def test_enter_sets_game_started(ctx):
    ctx.stats.game_active = False
    ctx.stats.game_started = False
    _post(pygame.K_RETURN)
    events.check_events(ctx)
    assert ctx.stats.game_started


def test_enter_resets_score(ctx):
    ctx.stats.game_active = False
    ctx.stats.score = 9999
    _post(pygame.K_RETURN)
    events.check_events(ctx)
    assert ctx.stats.score == 0


def test_enter_creates_fleet(ctx):
    ctx.stats.game_active = False
    _post(pygame.K_RETURN)
    events.check_events(ctx)
    assert len(ctx.aliens) > 0


def test_enter_clears_bullets(ctx):
    ctx.stats.game_active = False
    from bullet import Bullet

    ctx.bullets.add(Bullet(ctx.settings, ctx.screen, ctx.ship))
    _post(pygame.K_RETURN)
    events.check_events(ctx)
    assert len(ctx.bullets) == 0


def test_enter_ignored_when_game_active(ctx):
    ctx.stats.game_active = True
    # With game active, ENTER is not handled (no restart branch)
    initial_score = ctx.stats.score = 500
    _post(pygame.K_RETURN)
    events.check_events(ctx)
    assert ctx.stats.score == initial_score  # unchanged


# ── Rocket key ───────────────────────────────────────────────────────────────


def test_b_fires_rocket_when_none_active(ctx):
    ctx.stats.game_active = True
    ctx.stats.rockets = 2
    _post(pygame.K_b)
    events.check_events(ctx)
    assert len(ctx.rockets) == 1
    assert ctx.stats.rockets == 1


def test_b_detonates_existing_rocket(ctx):
    ctx.stats.game_active = True
    from rocket import Rocket

    rocket = Rocket(ctx.settings, ctx.screen, ctx.ship)
    ctx.rockets.add(rocket)
    _post(pygame.K_b)
    events.check_events(ctx)
    assert len(ctx.rockets) == 0
    ctx.sounds["rocket_explosion"].play.assert_called_once()
