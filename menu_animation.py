import math
import random
import pygame
from pixel_art import draw_pixel_art
from alien import _ALIEN_MAP, _PALETTE as _ALIEN_PALETTE, _PIXEL_SIZE as _ALIEN_PX


class MenuAlien:
    """Shaking, bobbing alien above the title."""

    def __init__(self, base_x, base_y):
        self._base_x = base_x
        self._base_y = base_y
        self._phase = 0.0

        ps = 6
        w = len(_ALIEN_MAP[0]) * ps
        h = len(_ALIEN_MAP) * ps
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        draw_pixel_art(self.image, _ALIEN_MAP, ps, _ALIEN_PALETTE)
        self.rect = self.image.get_rect(center=(base_x, base_y))

    def update(self):
        self._phase += 0.06
        shake_x = math.sin(self._phase * 3.7) * 5
        bob_y = math.sin(self._phase) * 10
        angle = math.sin(self._phase * 2.3) * 8
        self._rotated = pygame.transform.rotate(self.image, angle)
        self.rect = self._rotated.get_rect(
            center=(int(self._base_x + shake_x), int(self._base_y + bob_y))
        )

    def draw(self, screen):
        screen.blit(self._rotated, self.rect)


_ASTRO_PX = 4

_ASTRO_PALETTE = {
    1: (255, 255, 255),  # suit white
    2: (200, 210, 230),  # suit shadow
    3: (180, 140, 60),  # visor gold
    4: (220, 180, 80),  # visor highlight
    5: (160, 170, 190),  # backpack
    6: (120, 130, 150),  # backpack dark
}

_ASTRO_MAP = [
    [0, 0, 0, 1, 1, 1, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 0, 0],
    [0, 0, 1, 3, 3, 3, 1, 0, 0],
    [0, 0, 1, 3, 4, 3, 1, 0, 0],
    [0, 0, 1, 3, 3, 3, 1, 0, 0],
    [0, 0, 0, 1, 1, 1, 0, 0, 0],
    [0, 5, 1, 1, 1, 1, 1, 5, 0],
    [0, 6, 1, 2, 1, 2, 1, 6, 0],
    [1, 6, 1, 2, 1, 2, 1, 6, 1],
    [1, 5, 1, 1, 1, 1, 1, 5, 1],
    [0, 0, 1, 1, 0, 1, 1, 0, 0],
    [0, 0, 1, 1, 0, 1, 1, 0, 0],
    [0, 0, 2, 2, 0, 2, 2, 0, 0],
]


class MenuAstronaut:
    """Small astronaut floating across the screen."""

    def __init__(self, screen_w, screen_h):
        self._screen_w = screen_w
        self._screen_h = screen_h

        w = len(_ASTRO_MAP[0]) * _ASTRO_PX
        h = len(_ASTRO_MAP) * _ASTRO_PX
        self._base_image = pygame.Surface((w, h), pygame.SRCALPHA)
        draw_pixel_art(self._base_image, _ASTRO_MAP, _ASTRO_PX, _ASTRO_PALETTE)

        self._reset()

    def _reset(self):
        self._x = float(random.choice([-60, self._screen_w + 60]))
        self._y = float(random.randint(100, self._screen_h - 200))
        self._vx = random.uniform(0.4, 1.0) * (1 if self._x < 0 else -1)
        self._vy = random.uniform(-0.2, 0.2)
        self._angle = 0.0
        self._spin = random.uniform(-0.8, 0.8)

    def update(self):
        self._x += self._vx
        self._y += self._vy
        self._angle = (self._angle + self._spin) % 360

        if self._x < -100 or self._x > self._screen_w + 100:
            self._reset()

    def draw(self, screen):
        rotated = pygame.transform.rotate(self._base_image, self._angle)
        rect = rotated.get_rect(center=(int(self._x), int(self._y)))
        screen.blit(rotated, rect)


class MenuMeteor:
    """Fast-moving meteor streak across the screen."""

    def __init__(self, screen_w, screen_h):
        self._screen_w = screen_w
        self._screen_h = screen_h
        self._active = False
        self._timer = random.randint(60, 180)
        self._x = 0.0
        self._y = 0.0
        self._vx = 0.0
        self._vy = 0.0
        self._trail: list[tuple[float, float]] = []
        self._size = 3
        self._color = (200, 180, 140)

    def _spawn(self):
        self._active = True
        side = random.choice(["top", "left", "right"])
        if side == "top":
            self._x = float(random.randint(0, self._screen_w))
            self._y = -10.0
            self._vx = random.uniform(-3, 3)
            self._vy = random.uniform(4, 8)
        elif side == "left":
            self._x = -10.0
            self._y = float(random.randint(0, self._screen_h // 2))
            self._vx = random.uniform(4, 8)
            self._vy = random.uniform(1, 4)
        else:
            self._x = float(self._screen_w + 10)
            self._y = float(random.randint(0, self._screen_h // 2))
            self._vx = random.uniform(-8, -4)
            self._vy = random.uniform(1, 4)

        self._size = random.randint(2, 4)
        brightness = random.randint(160, 255)
        self._color = (brightness, brightness - 30, brightness - 60)
        self._trail = []

    def update(self):
        if not self._active:
            self._timer -= 1
            if self._timer <= 0:
                self._spawn()
            return

        self._trail.append((self._x, self._y))
        if len(self._trail) > 12:
            self._trail.pop(0)

        self._x += self._vx
        self._y += self._vy

        if (
            self._x < -50
            or self._x > self._screen_w + 50
            or self._y > self._screen_h + 50
        ):
            self._active = False
            self._timer = random.randint(60, 240)

    def draw(self, screen):
        if not self._active:
            return
        for i, (tx, ty) in enumerate(self._trail):
            alpha = int(255 * (i + 1) / len(self._trail))
            r, g, b = self._color
            size = max(1, self._size * (i + 1) // len(self._trail))
            trail_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, (r, g, b, alpha), (size, size), size)
            screen.blit(trail_surf, (int(tx) - size, int(ty) - size))
        pygame.draw.circle(
            screen, self._color, (int(self._x), int(self._y)), self._size
        )


class MenuAnimation:
    """Manages all animated menu elements. Created once, updated per frame."""

    def __init__(self, screen_w, screen_h, alien_center):
        self.alien = MenuAlien(*alien_center)
        self.astronaut = MenuAstronaut(screen_w, screen_h)
        self.meteors = [MenuMeteor(screen_w, screen_h) for _ in range(3)]

    def update(self):
        self.alien.update()
        self.astronaut.update()
        for m in self.meteors:
            m.update()

    def draw(self, screen):
        for m in self.meteors:
            m.draw(screen)
        self.astronaut.draw(screen)
        self.alien.draw(screen)
