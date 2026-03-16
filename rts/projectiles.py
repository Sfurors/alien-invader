"""Projectile sprites for ranged combat."""

import pygame
from .rts_settings import RTSSettings as S


class Projectile(pygame.sprite.Sprite):
    """A projectile that travels from attacker to target."""

    def __init__(
        self,
        start_px,
        start_py,
        target,
        damage,
        speed=6.0,
        color=(255, 255, 100),
        size=2,
        faction="human",
    ):
        super().__init__()
        self.px = float(start_px)
        self.py = float(start_py)
        self.target = target
        self.damage = damage
        self.speed = speed
        self.color = color
        self.size = size
        self.faction = faction
        self.alive_flag = True
        # Small surface for the projectile
        self.image = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (size, size), size)
        self.rect = self.image.get_rect(center=(int(self.px), int(self.py)))

    def update(self):
        if not self.alive_flag:
            self.kill()
            return
        # Check if target is still alive
        if self.target is None or not self.target.alive():
            self.kill()
            return
        # Move toward target
        if hasattr(self.target, "px"):
            tx, ty = self.target.px, self.target.py
        else:
            # Building target
            tx = self.target.px + self.target.size[0] * S.TILE_SIZE // 2
            ty = self.target.py + self.target.size[1] * S.TILE_SIZE // 2
        dx = tx - self.px
        dy = ty - self.py
        dist = (dx * dx + dy * dy) ** 0.5
        if dist < self.speed + 2:
            # Hit!
            self.target.take_damage(self.damage)
            self.kill()
            return
        self.px += dx / dist * self.speed
        self.py += dy / dist * self.speed
        self.rect.center = (int(self.px), int(self.py))
