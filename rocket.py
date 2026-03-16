import math
import pygame
from pixel_art import draw_pixel_art

# 4 cols × 11 rows × pixel_size 3  →  12 × 33 px
_PIXEL_SIZE = 3

_PALETTE = {
    1: (220, 220, 230),  # body gray-white
    2: (160, 160, 180),  # body shadow
    3: (255, 100, 30),  # flame / nose cone
    4: (255, 220, 60),  # flame core
}

_ROCKET_MAP = [
    # 0  1  2  3
    [0, 1, 1, 0],  #  0  nose tip
    [0, 3, 3, 0],  #  1  nose cone
    [3, 3, 3, 3],  #  2  nose base
    [1, 1, 1, 1],  #  3  body top
    [1, 2, 2, 1],  #  4  body
    [1, 2, 2, 1],  #  5  body
    [1, 2, 2, 1],  #  6  body
    [1, 1, 1, 1],  #  7  body bottom
    [3, 3, 3, 3],  #  8  flame base
    [0, 4, 4, 0],  #  9  flame core
    [0, 3, 3, 0],  # 10  flame tip
]

_W = len(_ROCKET_MAP[0]) * _PIXEL_SIZE  # 12
_H = len(_ROCKET_MAP) * _PIXEL_SIZE  # 33

_GLOW_MARGIN = 14  # extra pixels around the rocket for glow
_FULL_W = _W + _GLOW_MARGIN * 2
_FULL_H = _H + _GLOW_MARGIN * 2


class Rocket(pygame.sprite.Sprite):
    def __init__(self, ai_settings, screen, ship):
        super().__init__()
        self.screen = screen

        self._rocket_img = pygame.Surface((_W, _H), pygame.SRCALPHA)
        draw_pixel_art(self._rocket_img, _ROCKET_MAP, _PIXEL_SIZE, _PALETTE)

        self.image = pygame.Surface((_FULL_W, _FULL_H), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.centerx = ship.rect.centerx
        self.rect.top = ship.rect.top - _GLOW_MARGIN

        screen_rect = screen.get_rect()
        self.detonate_y = screen_rect.height * ai_settings.rocket_detonate_fraction
        self._y = float(self.rect.y)
        self.speed = ai_settings.rocket_speed
        self._phase = 0.0

    def update(self):
        self._y -= self.speed
        self.rect.y = int(self._y)
        if self.rect.bottom <= 0:
            self.kill()
            return

        self._phase += 0.15
        self.image.fill((0, 0, 0, 0))

        # Pulsating glow layers
        cx, cy = _FULL_W // 2, _FULL_H // 2 + 4
        pulse = 0.7 + 0.3 * math.sin(self._phase)
        for radius, alpha_base in [(14, 30), (10, 50), (6, 80)]:
            r = int(radius * pulse)
            alpha = int(alpha_base * pulse)
            glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 140, 30, alpha), (r, r), r)
            self.image.blit(glow, (cx - r, cy - r))

        # Rocket sprite on top
        self.image.blit(self._rocket_img, (_GLOW_MARGIN, _GLOW_MARGIN))
