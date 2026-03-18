"""Front-facing lizard-cyborg pixel art for FPS dungeon enemies.

One base sprite is defined in a neutral palette and tinted per enemy type
at startup.  The result is cached so each type builds its Surface only once.
"""

import pygame
from .dungeon_settings import DungeonSettings

# Pixel size for the source art (each art-pixel becomes PS x PS real pixels).
_PS = 2

# Neutral grayscale palette — tinted at runtime by enemy color.
# 1 = highlight (metal shine)
# 2 = mid body
# 3 = dark armor / shadow
# 4 = accent (circuits / glow) — receives strongest tint
# 5 = eye — bright, receives strongest tint
# 6 = claw / weapon — slight tint
_BASE_PALETTE = {
    1: (210, 220, 215),  # highlight
    2: (150, 160, 155),  # mid
    3: (80, 90, 85),     # dark
    4: (200, 220, 180),  # circuit accent
    5: (255, 255, 240),  # eye
    6: (170, 170, 175),  # claw
}

# Front-facing lizard-cyborg drone (11 wide x 16 tall)
_BASE_MAP = [
    #0  1  2  3  4  5  6  7  8  9 10
    [0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0],  # 0  cranium top
    [0, 0, 1, 2, 2, 1, 2, 2, 1, 0, 0],  # 1  cranium
    [0, 0, 1, 5, 2, 4, 2, 5, 1, 0, 0],  # 2  eyes + circuit
    [0, 0, 0, 2, 3, 3, 3, 2, 0, 0, 0],  # 3  jaw
    [0, 0, 0, 0, 3, 4, 3, 0, 0, 0, 0],  # 4  neck circuit
    [0, 0, 1, 2, 2, 2, 2, 2, 1, 0, 0],  # 5  shoulder plate
    [0, 6, 1, 2, 4, 2, 4, 2, 1, 6, 0],  # 6  arms + torso circuits
    [0, 6, 0, 2, 2, 1, 2, 2, 0, 6, 0],  # 7  arms + torso
    [6, 6, 0, 3, 2, 2, 2, 3, 0, 6, 6],  # 8  claws + torso
    [0, 0, 0, 3, 4, 3, 4, 3, 0, 0, 0],  # 9  belt circuits
    [0, 0, 0, 2, 3, 0, 3, 2, 0, 0, 0],  # 10 hip
    [0, 0, 0, 2, 3, 0, 3, 2, 0, 0, 0],  # 11 upper legs
    [0, 0, 0, 3, 3, 0, 3, 3, 0, 0, 0],  # 12 lower legs
    [0, 0, 3, 3, 0, 0, 0, 3, 3, 0, 0],  # 13 feet
]

_ART_W = len(_BASE_MAP[0])
_ART_H = len(_BASE_MAP)
_SURF_W = _ART_W * _PS
_SURF_H = _ART_H * _PS

# How strongly each palette index is tinted by the enemy color.
# 0.0 = keep neutral, 1.0 = fully replace with tint.
_TINT_STRENGTH = {
    1: 0.15,
    2: 0.35,
    3: 0.25,
    4: 0.80,
    5: 0.90,
    6: 0.20,
}

# Cache: enemy_type string -> pygame.Surface (SRCALPHA)
_cache: dict[str, pygame.Surface] = {}


def _lerp_color(base, tint, t):
    """Linearly interpolate between base and tint by t (0..1)."""
    return (
        int(base[0] + (tint[0] - base[0]) * t),
        int(base[1] + (tint[1] - base[1]) * t),
        int(base[2] + (tint[2] - base[2]) * t),
    )


def _build_sprite(tint_color):
    """Render the base pixel map with the given tint into a Surface."""
    surf = pygame.Surface((_SURF_W, _SURF_H), pygame.SRCALPHA)
    for row_idx, row in enumerate(_BASE_MAP):
        for col_idx, idx in enumerate(row):
            if idx == 0:
                continue
            base = _BASE_PALETTE[idx]
            strength = _TINT_STRENGTH[idx]
            color = _lerp_color(base, tint_color, strength)
            pygame.draw.rect(
                surf, (*color, 255),
                (col_idx * _PS, row_idx * _PS, _PS, _PS),
            )
    return surf


def get_enemy_sprite(enemy_type):
    """Return the cached tinted Surface for this enemy type."""
    if enemy_type not in _cache:
        cfg = DungeonSettings.ENEMY_TYPES[enemy_type]
        _cache[enemy_type] = _build_sprite(cfg["color"])
    return _cache[enemy_type]


def get_pain_sprite():
    """Return a white-flash version of the sprite (shared by all types)."""
    key = "__pain__"
    if key not in _cache:
        _cache[key] = _build_sprite((255, 255, 255))
    return _cache[key]


def get_death_sprite():
    """Return a dark gray version for dying enemies."""
    key = "__death__"
    if key not in _cache:
        _cache[key] = _build_sprite((80, 80, 80))
    return _cache[key]
