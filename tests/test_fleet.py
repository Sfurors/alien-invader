"""Fleet creation and direction tests — require SDL dummy display."""

import pytest
import pygame
from fleet import create_fleet, change_fleet_direction
from game_logic import FLEET_TOP_MARGIN


def test_create_fleet_populates_aliens(ctx):
    assert len(ctx.aliens) == 0
    create_fleet(ctx)
    assert len(ctx.aliens) > 0


def test_create_fleet_all_aliens_within_screen(ctx):
    create_fleet(ctx)
    screen_rect = ctx.screen.get_rect()
    for alien in ctx.aliens.sprites():
        assert alien.rect.left >= 0
        assert alien.rect.right <= screen_rect.right


def test_create_fleet_aliens_in_upper_half(ctx):
    create_fleet(ctx)
    screen_rect = ctx.screen.get_rect()
    for alien in ctx.aliens.sprites():
        assert alien.rect.bottom <= screen_rect.height // 2 + 100  # generous margin


def test_create_fleet_first_row_at_top_margin(ctx):
    create_fleet(ctx)
    y_values = {alien.rect.y for alien in ctx.aliens.sprites()}
    assert FLEET_TOP_MARGIN in y_values


def test_change_fleet_direction_reverses(ctx):
    create_fleet(ctx)
    initial = ctx.settings.fleet_direction
    change_fleet_direction(ctx)
    assert ctx.settings.fleet_direction == -initial


def test_change_fleet_direction_drops_aliens(ctx):
    create_fleet(ctx)
    y_before = {id(a): a.rect.y for a in ctx.aliens.sprites()}
    change_fleet_direction(ctx)
    for alien in ctx.aliens.sprites():
        assert alien.rect.y > y_before[id(alien)]


def test_fleet_refilled_after_empty(ctx):
    create_fleet(ctx)
    count_first = len(ctx.aliens)
    ctx.aliens.empty()
    create_fleet(ctx)
    assert len(ctx.aliens) == count_first
