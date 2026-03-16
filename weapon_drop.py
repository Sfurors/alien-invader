import pygame
from pixel_art import draw_pixel_art

# 5 cols × 8 rows × pixel_size 4  →  20 × 32 px
_PIXEL_SIZE = 4

_PALETTE = {
    1: (0, 200, 180),  # teal body
    2: (0, 255, 220),  # teal highlight
    3: (0, 140, 120),  # teal shadow
}

_DROP_MAP = [
    # 0  1  2  3  4
    [0, 1, 1, 1, 0],  # 0  top cap
    [1, 2, 2, 2, 1],  # 1  body top highlight
    [1, 1, 2, 1, 1],  # 2  body
    [1, 1, 1, 1, 1],  # 3  body
    [1, 3, 1, 3, 1],  # 4  body detail
    [1, 1, 1, 1, 1],  # 5  body
    [1, 1, 2, 1, 1],  # 6  body bottom
    [0, 1, 1, 1, 0],  # 7  bottom cap
]

_W = len(_DROP_MAP[0]) * _PIXEL_SIZE  # 20
_H = len(_DROP_MAP) * _PIXEL_SIZE  # 32


class WeaponDrop(pygame.sprite.Sprite):
    def __init__(self, ai_settings, screen, center):
        super().__init__()
        base = pygame.Surface((_W, _H), pygame.SRCALPHA)
        draw_pixel_art(base, _DROP_MAP, _PIXEL_SIZE, _PALETTE)
        scale = getattr(ai_settings, "resolution_scale", 1.0)
        if scale != 1.0:
            sw = max(5, int(_W * scale))
            sh = max(8, int(_H * scale))
            self.image = pygame.transform.smoothscale(base, (sw, sh))
        else:
            self.image = base
        self.rect = self.image.get_rect(center=center)
        self._y = float(self.rect.y)
        self._drop_speed = ai_settings.drop_speed
        self._screen_bottom = screen.get_rect().bottom

    def update(self):
        self._y += self._drop_speed
        self.rect.y = int(self._y)
        if self.rect.top >= self._screen_bottom:
            self.kill()
