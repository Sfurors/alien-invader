from dataclasses import dataclass
import pygame
from settings1 import Settings
from game_stats import GameStats
from ship import Ship
from background import SpaceBackground


@dataclass
class GameContext:
    settings: Settings
    stats: GameStats
    screen: pygame.Surface
    sounds: dict
    ship: Ship
    bullets: pygame.sprite.Group
    aliens: pygame.sprite.Group
    explosions: pygame.sprite.Group
    asteroids: pygame.sprite.Group
    rockets: pygame.sprite.Group
    drops: pygame.sprite.Group
    boss_group: pygame.sprite.Group
    boss_projectiles: pygame.sprite.Group
    background: SpaceBackground
