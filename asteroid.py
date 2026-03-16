import random
import math
import pygame

ASTEROID_COUNT = 10
ASTEROID_MIN_SIZE = 14
ASTEROID_MAX_SIZE = 26

_FRAME_COUNT = 24  # fewer frames → chunkier rotation steps (15° each)
_GRID = 4  # snap vertices to this grid for blocky pixel-art look


class Asteroid(pygame.sprite.Sprite):
    def __init__(self, screen_w, screen_h):
        super().__init__()
        self._screen_w = screen_w
        self._screen_h = screen_h

        size = random.randint(ASTEROID_MIN_SIZE, ASTEROID_MAX_SIZE)
        self._size = size
        self.radius = int(size * 0.7)

        base = self._make_image(size)
        self._frames = [
            pygame.transform.rotate(base, i * (360 / _FRAME_COUNT))
            for i in range(_FRAME_COUNT)
        ]
        self._frame_step = 360 / _FRAME_COUNT

        self._x = float(random.randint(0, screen_w))
        self._y = float(random.randint(-screen_h, -size))
        self._speed = random.uniform(0.5, 1.5)
        self._drift_x = random.uniform(-0.2, 0.2)
        self._spin_speed = random.uniform(-0.5, 0.5)
        self._angle = random.uniform(0, 360)

        self.image = self._frames[0]
        self.rect = self.image.get_rect(center=(int(self._x), int(self._y)))

    @staticmethod
    def _make_image(size):
        canvas = size * 2 + 4
        surf = pygame.Surface((canvas, canvas), pygame.SRCALPHA)
        cx = cy = canvas // 2
        points = []
        for i in range(8):
            angle = math.tau * i / 8 + random.uniform(-0.25, 0.25)
            r = size * random.uniform(0.65, 1.0)
            # Snap to pixel grid for blocky look
            raw_x = cx + r * math.cos(angle)
            raw_y = cy + r * math.sin(angle)
            gx = round(raw_x / _GRID) * _GRID
            gy = round(raw_y / _GRID) * _GRID
            points.append((gx, gy))
        pygame.draw.polygon(surf, (110, 95, 80), points)
        pygame.draw.polygon(surf, (160, 145, 130), points, 2)
        # Pixel-art crater: small filled square
        cx4 = round((cx - size * 0.25) / _GRID) * _GRID
        cy4 = round((cy - size * 0.15) / _GRID) * _GRID
        pygame.draw.rect(surf, (80, 68, 58), (cx4 - 2, cy4 - 2, 4, 4))
        pygame.draw.rect(surf, (80, 68, 58), (cx4 + 4, cy4 + 4, 4, 4))
        return surf

    def update(self):
        self._x += self._drift_x
        self._y += self._speed
        self._angle = (self._angle + self._spin_speed) % 360

        frame_idx = int(self._angle / self._frame_step) % _FRAME_COUNT
        self.image = self._frames[frame_idx]
        self.rect = self.image.get_rect(center=(int(self._x), int(self._y)))

        if self.rect.top > self._screen_h:
            self._x = float(random.randint(0, self._screen_w))
            self._y = float(-self._size * 2)
            self._speed = random.uniform(0.5, 1.5)
            self._drift_x = random.uniform(-0.2, 0.2)
