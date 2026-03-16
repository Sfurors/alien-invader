"""Collision detection tests — require SDL dummy display."""

import pytest
import pygame
from unittest.mock import patch
from fleet import create_fleet
from bullet import Bullet
from alien import Alien
from rocket import Rocket
from weapon_drop import WeaponDrop
import collision


def _add_alien_at(ctx, x, y):
    a = Alien(ctx.settings, ctx.screen, x, y)
    ctx.aliens.add(a)
    return a


def _add_bullet_at(ctx, x, y):
    b = Bullet(ctx.settings, ctx.screen, ctx.ship)
    b.rect.centerx = x
    b.rect.centery = y
    ctx.bullets.add(b)
    return b


# ── Bullet ↔ Alien ──────────────────────────────────────────────────────────


def test_bullet_kills_alien_and_awards_score(ctx):
    alien = _add_alien_at(ctx, 100, 100)
    _add_bullet_at(ctx, alien.rect.centerx, alien.rect.centery)
    initial_score = ctx.stats.score

    collision.check_bullet_alien_collisions(ctx)

    assert ctx.stats.score > initial_score
    assert alien not in ctx.aliens.sprites()
    assert len(ctx.bullets) == 0


def test_bullet_hit_plays_explosion_sound(ctx):
    alien = _add_alien_at(ctx, 200, 200)
    _add_bullet_at(ctx, alien.rect.centerx, alien.rect.centery)

    collision.check_bullet_alien_collisions(ctx)

    ctx.sounds["explosion"].play.assert_called()


def test_bullet_miss_preserves_alien(ctx):
    _add_alien_at(ctx, 400, 400)
    _add_bullet_at(ctx, 0, 0)  # far away
    initial_score = ctx.stats.score

    collision.check_bullet_alien_collisions(ctx)

    assert ctx.stats.score == initial_score
    assert len(ctx.aliens) == 1


# ── Drop ↔ Ship ─────────────────────────────────────────────────────────────


def test_drop_pickup_increments_rockets(ctx):
    drop = WeaponDrop(ctx.settings, ctx.screen, ctx.ship.rect.center)
    ctx.drops.add(drop)
    initial = ctx.stats.rockets

    collision.check_drop_ship_collisions(ctx)

    assert ctx.stats.rockets == initial + 1
    assert drop not in ctx.drops.sprites()


def test_drop_pickup_plays_sound(ctx):
    drop = WeaponDrop(ctx.settings, ctx.screen, ctx.ship.rect.center)
    ctx.drops.add(drop)

    collision.check_drop_ship_collisions(ctx)

    ctx.sounds["pickup"].play.assert_called_once()


def test_drop_out_of_reach_is_ignored(ctx):
    # Place drop far from ship
    drop = WeaponDrop(ctx.settings, ctx.screen, (0, 0))
    ctx.ship.rect.center = (700, 1100)
    ctx.drops.add(drop)
    initial = ctx.stats.rockets

    collision.check_drop_ship_collisions(ctx)

    assert ctx.stats.rockets == initial


# ── Game-over triggers ───────────────────────────────────────────────────────


def test_alien_collides_with_ship_ends_game(ctx):
    ctx.stats.game_active = True
    alien = _add_alien_at(ctx, ctx.ship.rect.centerx - 5, ctx.ship.rect.centery - 5)

    collision.check_aliens_ship_collision(ctx)

    assert not ctx.stats.game_active


def test_alien_reaches_bottom_ends_game(ctx):
    ctx.stats.game_active = True
    screen_rect = ctx.screen.get_rect()
    alien = _add_alien_at(ctx, 100, screen_rect.bottom)

    collision.check_aliens_ship_collision(ctx)

    assert not ctx.stats.game_active


def test_game_over_sound_plays_once(ctx):
    ctx.stats.game_active = True
    alien = _add_alien_at(ctx, ctx.ship.rect.centerx - 5, ctx.ship.rect.centery - 5)

    collision.check_aliens_ship_collision(ctx)
    collision.check_aliens_ship_collision(ctx)  # second call — game already over

    ctx.sounds["game_over"].play.assert_called_once()


# ── Rocket detonation ────────────────────────────────────────────────────────


def test_rocket_detonation_kills_aliens_in_radius(ctx):
    create_fleet(ctx)
    ctx.stats.rockets = 1
    rocket = Rocket(ctx.settings, ctx.screen, ctx.ship)
    # Force rocket to detonate position
    rocket.rect.top = int(rocket.detonate_y) - 1
    ctx.rockets.add(rocket)

    initial_count = len(ctx.aliens)
    collision.check_rocket_detonations(ctx)

    assert len(ctx.aliens) < initial_count


def test_rocket_detonation_plays_sound(ctx):
    ctx.stats.rockets = 1
    rocket = Rocket(ctx.settings, ctx.screen, ctx.ship)
    rocket.rect.top = int(rocket.detonate_y) - 1
    ctx.rockets.add(rocket)

    collision.check_rocket_detonations(ctx)

    ctx.sounds["rocket_explosion"].play.assert_called_once()


def test_detonate_all_rockets_removes_all(ctx):
    ctx.stats.rockets = 2
    for _ in range(2):
        ctx.rockets.add(Rocket(ctx.settings, ctx.screen, ctx.ship))

    collision.detonate_all_rockets(ctx)

    assert len(ctx.rockets) == 0
