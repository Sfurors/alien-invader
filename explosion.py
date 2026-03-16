import pygame

TOTAL_FRAMES = 15
MAX_RADIUS = 28


class Explosion(pygame.sprite.Sprite):
    def __init__(
        self, screen, center, total_frames=TOTAL_FRAMES, max_radius=MAX_RADIUS
    ):
        super().__init__()
        self.frame = 0
        self.total_frames = total_frames
        self.max_radius = max_radius
        r = max_radius
        self.image = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=center)

    def update(self):
        self.frame += 1
        if self.frame >= self.total_frames:
            self.kill()
            return

        r = self.max_radius
        progress = self.frame / self.total_frames
        size = int(r * progress)
        alpha = int(255 * (1 - progress))

        self.image.fill((0, 0, 0, 0))

        # Pixel-art style: concentric squares stepping outward
        step = max(2, size // 4)
        for i in range(3, 0, -1):
            ring = size - (3 - i) * step
            if ring <= 0:
                continue
            color = [
                (255, 255, 120, alpha),  # inner bright yellow
                (255, 160, 30, alpha),  # mid orange
                (200, 60, 10, alpha),  # outer dark red-orange
            ][i - 1]
            pygame.draw.rect(
                self.image,
                color,
                (r - ring, r - ring, ring * 2, ring * 2),
            )


def RocketExplosion(screen, center):
    return Explosion(screen, center, total_frames=25, max_radius=80)
