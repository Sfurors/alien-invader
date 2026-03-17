"""RTS context dataclass — passed to all RTS functions."""

from dataclasses import dataclass, field
import pygame
from .rts_settings import RTSSettings
from .tile_map import TileMap
from .camera import Camera


@dataclass
class RTSContext:
    settings: RTSSettings
    screen: pygame.Surface
    sounds: dict
    tile_map: TileMap
    camera: Camera
    screen_w: int
    screen_h: int
    font_scale: float

    # Sprite groups
    player_units: pygame.sprite.Group = field(default_factory=pygame.sprite.Group)
    player_buildings: pygame.sprite.Group = field(default_factory=pygame.sprite.Group)
    enemy_units: pygame.sprite.Group = field(default_factory=pygame.sprite.Group)
    enemy_buildings: pygame.sprite.Group = field(default_factory=pygame.sprite.Group)
    all_entities: pygame.sprite.Group = field(default_factory=pygame.sprite.Group)
    projectiles: pygame.sprite.Group = field(default_factory=pygame.sprite.Group)

    # Fog of war reference (set after init)
    fog: object = None

    # AI reference (set after init)
    ai: object = None

    # Minimap reference (set after init)
    minimap: object = None

    # HUD manager (set after init)
    hud_manager: object = None
