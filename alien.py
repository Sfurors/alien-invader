import math
import random
import pygame
from pixel_art import draw_pixel_art

# 12 cols × 9 rows × pixel_size 4  →  48 × 36 px
ALIEN_WIDTH = 48
ALIEN_HEIGHT = 36

_PIXEL_SIZE = 4

_PALETTE = {
    1: (0, 200, 50),  # alien green
    2: (0, 0, 0),  # eyes
    3: (0, 140, 30),  # dark green detail
}

_ALIEN_MAP = [
    # 0  1  2  3  4  5  6  7  8  9 10 11
    [0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0],  # 0  antennae
    [0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0],  # 1  antennae inner
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],  # 2  head dome
    [1, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 1],  # 3  eyes
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],  # 4  body
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],  # 5  body lower
    [0, 0, 1, 1, 0, 3, 3, 0, 1, 1, 0, 0],  # 6  belly detail
    [0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0],  # 7  legs
    [0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0],  # 8  feet
]


class Alien(pygame.sprite.Sprite):
    def __init__(self, ai_settings, screen, x, y, drift_y=0.0):
        super().__init__()
        self.screen = screen
        self.ai_settings = ai_settings

        base = pygame.Surface((ALIEN_WIDTH, ALIEN_HEIGHT), pygame.SRCALPHA)
        draw_pixel_art(base, _ALIEN_MAP, _PIXEL_SIZE, _PALETTE)

        scale = getattr(ai_settings, "resolution_scale", 1.0)
        self.scaled_w = max(12, int(ALIEN_WIDTH * scale))
        self.scaled_h = max(9, int(ALIEN_HEIGHT * scale))
        if scale != 1.0:
            self.image = pygame.transform.smoothscale(
                base, (self.scaled_w, self.scaled_h)
            )
        else:
            self.image = base

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.x = float(self.rect.x)
        self.y = float(self.rect.y)
        self.drift_y = drift_y
        self._dodge_phase = random.uniform(0, 2 * math.pi)
        self.dodge_offset = 0.0

    def check_edges(self, screen_width: int):
        base_right = self.x + self.scaled_w
        return base_right >= screen_width or self.x <= 0

    def update(self):
        self.x += self.ai_settings.alien_speed * self.ai_settings.fleet_direction
        if self.ai_settings.alien_dodge:
            self._dodge_phase += self.ai_settings.alien_dodge_frequency
            self.dodge_offset = (
                math.sin(self._dodge_phase) * self.ai_settings.alien_dodge_amplitude
            )
        self.rect.x = int(self.x + self.dodge_offset)
        if self.drift_y:
            self.y += self.drift_y
            self.rect.y = int(self.y)
            if self.rect.top > self.ai_settings.screen_height:
                self.kill()
