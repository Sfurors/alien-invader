"""Renderer smoke tests — verify no crash, no pixel inspection."""

import pytest
import pygame
from fleet import create_fleet
from game_stats import GameStats
import renderer


@pytest.fixture(autouse=True)
def reset_icon():
    """Ensure the cached rocket icon is cleared before each test."""
    renderer._reset_rocket_icon()
    yield
    renderer._reset_rocket_icon()


# ── Menu & game-over screens ─────────────────────────────────────────────────


def test_draw_menu_no_crash(screen, ai_settings, renderer_fonts):
    title_font, menu_font = renderer_fonts
    renderer.draw_menu(screen, ai_settings, title_font, menu_font)


def test_draw_menu_with_bg_no_crash(screen, ai_settings, renderer_fonts):
    from unittest.mock import MagicMock

    title_font, menu_font = renderer_fonts
    renderer.draw_menu(screen, ai_settings, title_font, menu_font, bg=MagicMock())


def test_draw_game_over_no_crash(screen, ai_settings, renderer_fonts):
    title_font, menu_font = renderer_fonts
    renderer.draw_game_over(screen, ai_settings, title_font, menu_font)


def test_draw_game_over_with_bg_no_crash(screen, ai_settings, renderer_fonts):
    from unittest.mock import MagicMock

    title_font, menu_font = renderer_fonts
    renderer.draw_game_over(screen, ai_settings, title_font, menu_font, bg=MagicMock())


# ── In-game HUD ──────────────────────────────────────────────────────────────


def test_draw_score_no_crash(screen, renderer_fonts):
    stats = GameStats()
    stats.score = 1250
    _, font = renderer_fonts
    renderer.draw_score(screen, stats, font)


def test_draw_rocket_hud_no_crash(screen, renderer_fonts):
    stats = GameStats()
    stats.rockets = 3
    _, font = renderer_fonts
    renderer.draw_rocket_hud(screen, stats, font)


# ── Full screen update ───────────────────────────────────────────────────────


def test_update_screen_empty_groups_no_crash(ctx, renderer_fonts):
    _, font = renderer_fonts
    hint_font = pygame.font.SysFont("consolas", 32)
    renderer.update_screen(ctx, font, hint_font)


def test_update_screen_with_fleet_no_crash(ctx, renderer_fonts):
    create_fleet(ctx)
    _, font = renderer_fonts
    hint_font = pygame.font.SysFont("consolas", 32)
    renderer.update_screen(ctx, font, hint_font)


def test_update_screen_with_active_rocket_shows_hint(ctx, renderer_fonts):
    from rocket import Rocket

    ctx.rockets.add(Rocket(ctx.settings, ctx.screen, ctx.ship))
    _, font = renderer_fonts
    hint_font = pygame.font.SysFont("consolas", 32)
    renderer.update_screen(ctx, font, hint_font)  # must not crash with rocket hint


# ── Icon caching ─────────────────────────────────────────────────────────────


def test_rocket_icon_is_cached(pygame_init):
    renderer._reset_rocket_icon()
    icon1 = renderer._get_rocket_icon()
    icon2 = renderer._get_rocket_icon()
    assert icon1 is icon2


def test_reset_icon_clears_cache(pygame_init):
    renderer._get_rocket_icon()  # populate cache
    renderer._reset_rocket_icon()
    assert renderer._ROCKET_ICON is None
