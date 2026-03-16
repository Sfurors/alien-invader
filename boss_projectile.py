import pygame


class BossProjectile(pygame.sprite.Sprite):
    def __init__(self, screen, x, y, dx, dy, speed):
        super().__init__()
        screen_rect = screen.get_rect()
        self._screen_w = screen_rect.width
        self._screen_h = screen_rect.height

        self.image = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 80, 20), (4, 4), 4)
        pygame.draw.circle(self.image, (255, 200, 60), (4, 4), 2)

        self.rect = self.image.get_rect(center=(x, y))
        self._fx = float(self.rect.x)
        self._fy = float(self.rect.y)
        self._dx = dx * speed
        self._dy = dy * speed

    def update(self):
        self._fx += self._dx
        self._fy += self._dy
        self.rect.x = int(self._fx)
        self.rect.y = int(self._fy)
        if (
            self.rect.top > self._screen_h
            or self.rect.bottom < 0
            or self.rect.right < 0
            or self.rect.left > self._screen_w
        ):
            self.kill()
