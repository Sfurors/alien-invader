import math
import pygame


class Bullet(pygame.sprite.Sprite):
    def __init__(self, ai_settings, screen, ship):
        super().__init__()
        self.screen = screen
        self.speed = ai_settings.bullet_speed
        self.color = ai_settings.bullet_color

        angle_rad = math.radians(ship.angle)
        self._dx = -math.sin(angle_rad) * self.speed
        self._dy = -math.cos(angle_rad) * self.speed

        w = ai_settings.bullet_width
        h = ai_settings.bullet_height
        self._angle = ship.angle

        self._base_image = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(self._base_image, self.color, (0, 0, w, h))
        pygame.draw.rect(self._base_image, (255, 255, 220), (0, 0, w, 3))

        if self._angle != 0.0:
            self.image = pygame.transform.rotate(self._base_image, self._angle)
        else:
            self.image = self._base_image
        self.rect = self.image.get_rect()
        self.rect.centerx = ship.rect.centerx
        self.rect.bottom = ship.rect.top

        self._fx = float(self.rect.x)
        self._fy = float(self.rect.y)
        self._screen_h = screen.get_rect().height

    def update(self):
        self._fx += self._dx
        self._fy += self._dy
        self.rect.x = int(self._fx)
        self.rect.y = int(self._fy)
        if (
            self.rect.bottom <= 0
            or self.rect.right < 0
            or self.rect.left > self.screen.get_rect().width
        ):
            self.kill()

    def draw(self):
        self.screen.blit(self.image, self.rect)
