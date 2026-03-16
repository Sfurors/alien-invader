import random
import math
import pygame


class SpaceBackground:
    def __init__(self, screen, num_stars=120):
        self._screen = screen
        self._w = screen.get_width()
        self._h = screen.get_height()
        self._frame = 0

        self._stars = [
            {
                "x": random.randint(0, self._w),
                "y": random.randint(0, self._h),
                "size": random.choice([1, 1, 1, 2, 2, 3]),
                "base_alpha": random.randint(100, 180),
                "phase": random.uniform(0, math.tau),
                "speed": random.uniform(0.02, 0.06),
                "tint": random.choice(
                    [
                        (255, 255, 255),
                        (200, 210, 255),
                        (255, 240, 200),
                        (200, 255, 220),
                    ]
                ),
            }
            for _ in range(num_stars)
        ]

        self._planet_surf = pygame.Surface((self._w, self._h), pygame.SRCALPHA)
        self._star_surf = pygame.Surface((self._w, self._h), pygame.SRCALPHA)

        self._build_planet_surf()

    def _draw_craters(self, surface, cx, cy):
        for offset in [(-10, -8), (8, 5)]:
            csx, csy = cx + offset[0], cy + offset[1]
            pygame.draw.circle(surface, (90, 75, 68), (csx, csy), 7)
            pygame.draw.circle(surface, (140, 120, 110), (csx, csy), 7, 2)

    def _build_planet_surf(self):
        s = self._planet_surf
        w, h = self._w, self._h

        # --- Planet A: gas giant, right edge ---
        A_CX, A_CY, A_R = w - 30, h // 3, 70

        clip_surf_a = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(clip_surf_a, (255, 255, 255, 255), (A_CX, A_CY), A_R)

        body_a = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(body_a, (40, 60, 150), (A_CX, A_CY), A_R)

        band_colors = [
            (70, 90, 180),
            (55, 75, 165),
            (80, 100, 190),
            (45, 65, 155),
            (65, 85, 175),
        ]
        band_heights = [18, 14, 20, 12, 16]
        y_offset = A_CY - A_R + 8
        for bcolor, bh in zip(band_colors, band_heights):
            rect = pygame.Rect(A_CX - A_R, y_offset, A_R * 2, bh)
            band_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.ellipse(band_surf, (*bcolor, 180), rect)
            band_surf.blit(clip_surf_a, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            body_a.blit(band_surf, (0, 0))
            y_offset += bh + 4

        pygame.draw.circle(body_a, (100, 130, 220), (A_CX, A_CY), A_R, 3)
        s.blit(body_a, (0, 0))

        # --- Planet B: rocky + ring, left edge ---
        B_CX, B_CY, B_R = 20, h * 2 // 3, 35

        pygame.draw.circle(s, (120, 100, 90), (B_CX, B_CY), B_R)
        self._draw_craters(s, B_CX, B_CY)

        ring_rx = B_R + 22
        ring_ry = 10
        ring_rect = pygame.Rect(
            B_CX - ring_rx, B_CY - ring_ry, ring_rx * 2, ring_ry * 2
        )

        ring_back = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(ring_back, (160, 140, 120, 180), ring_rect, 5)
        clip_top = pygame.Surface((w, h), pygame.SRCALPHA)
        clip_top.fill((255, 255, 255, 255), pygame.Rect(0, 0, w, B_CY))
        ring_back.blit(clip_top, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        s.blit(ring_back, (0, 0))

        pygame.draw.circle(s, (120, 100, 90), (B_CX, B_CY), B_R)
        self._draw_craters(s, B_CX, B_CY)

        ring_front = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(ring_front, (160, 140, 120, 200), ring_rect, 5)
        clip_bot = pygame.Surface((w, h), pygame.SRCALPHA)
        clip_bot.fill((255, 255, 255, 255), pygame.Rect(0, B_CY, w, h - B_CY))
        ring_front.blit(clip_bot, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        s.blit(ring_front, (0, 0))

    def update(self):
        self._frame += 1
        self._star_surf.fill((0, 0, 0, 0))
        for star in self._stars:
            alpha = star["base_alpha"] + int(
                60 * math.sin(star["phase"] + self._frame * star["speed"])
            )
            alpha = max(30, min(220, alpha))
            r, g, b = star["tint"]
            color = (r, g, b, alpha)
            size = star["size"]
            if size == 1:
                self._star_surf.set_at((star["x"], star["y"]), color)
            else:
                pygame.draw.circle(self._star_surf, color, (star["x"], star["y"]), size)

    def draw(self, screen):
        screen.blit(self._planet_surf, (0, 0))
        screen.blit(self._star_surf, (0, 0))
