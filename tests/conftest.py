import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pytest
import pygame
from unittest.mock import MagicMock

from settings1 import Settings
from game_stats import GameStats
from ship import Ship
from game_context import GameContext


@pytest.fixture(scope="session", autouse=True)
def pygame_init():
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    yield
    pygame.quit()


@pytest.fixture
def screen(pygame_init):
    return pygame.display.set_mode((768, 1200))


@pytest.fixture
def ai_settings():
    return Settings()


@pytest.fixture
def stats():
    return GameStats()


@pytest.fixture
def ship(screen, ai_settings):
    return Ship(screen, ai_settings)


@pytest.fixture
def sounds():
    return {
        k: MagicMock()
        for k in (
            "shoot",
            "explosion",
            "game_over",
            "pickup",
            "rocket_fire",
            "rocket_explosion",
            "boss_hit",
            "boss_shoot",
            "boss_death",
            "level_up",
            "victory",
            "menu_melody",
            "level_music",
            "boss_music",
        )
    }


@pytest.fixture
def ctx(screen, ai_settings, stats, ship, sounds):
    return GameContext(
        settings=ai_settings,
        stats=stats,
        screen=screen,
        sounds=sounds,
        ship=ship,
        bullets=pygame.sprite.Group(),
        aliens=pygame.sprite.Group(),
        explosions=pygame.sprite.Group(),
        asteroids=pygame.sprite.Group(),
        rockets=pygame.sprite.Group(),
        drops=pygame.sprite.Group(),
        boss_group=pygame.sprite.Group(),
        boss_projectiles=pygame.sprite.Group(),
        background=MagicMock(),
    )


@pytest.fixture
def renderer_fonts(pygame_init):
    """Returns (title_font, menu_font) for renderer smoke tests."""
    title_font = pygame.font.SysFont("consolas", 72, bold=True)
    menu_font = pygame.font.SysFont("consolas", 32)
    return title_font, menu_font
