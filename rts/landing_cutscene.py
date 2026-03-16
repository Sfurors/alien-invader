"""Brief ship-landing transition before RTS mode begins."""

import math
import pygame


class LandingCutscene:
    """Shows the player's ship descending onto the planet surface."""

    DURATION = 180  # 3 seconds at 60fps

    def __init__(self, screen_w, screen_h, font_scale=1.0):
        self._sw = screen_w
        self._sh = screen_h
        self._fs = font_scale
        self._frame = 0
        self._finished = False

        self._font = pygame.font.SysFont(
            "consolas", max(14, int(24 * font_scale)), bold=True
        )
        self._small_font = pygame.font.SysFont(
            "consolas", max(10, int(16 * font_scale))
        )

        # Planet surface color gradient
        self._sky_top = (10, 15, 40)
        self._sky_bottom = (40, 80, 60)
        self._ground = (60, 120, 40)

    @property
    def finished(self):
        return self._finished

    def update(self):
        self._frame += 1
        if self._frame >= self.DURATION:
            self._finished = True

    def draw(self, screen):
        progress = min(1.0, self._frame / self.DURATION)

        # Draw sky gradient
        for y in range(self._sh):
            t = y / self._sh
            r = int(self._sky_top[0] * (1 - t) + self._sky_bottom[0] * t)
            g = int(self._sky_top[1] * (1 - t) + self._sky_bottom[1] * t)
            b = int(self._sky_top[2] * (1 - t) + self._sky_bottom[2] * t)
            pygame.draw.line(screen, (r, g, b), (0, y), (self._sw, y))

        # Ground
        ground_y = int(self._sh * 0.7)
        pygame.draw.rect(
            screen, self._ground, (0, ground_y, self._sw, self._sh - ground_y)
        )
        # Ground detail
        for x in range(0, self._sw, 20):
            shade = 50 + (x * 3 % 20)
            pygame.draw.rect(
                screen,
                (shade, shade + 60, shade - 10),
                (x, ground_y, 20, 3),
            )

        # Ship descending
        ship_y = int(-50 + (ground_y - 60) * progress)
        ship_x = self._sw // 2
        # Ship body
        pygame.draw.polygon(
            screen,
            (180, 180, 200),
            [
                (ship_x - 20, ship_y + 30),
                (ship_x, ship_y - 20),
                (ship_x + 20, ship_y + 30),
            ],
        )
        # Engine glow
        if progress < 0.9:
            glow_size = int(10 + 8 * math.sin(self._frame * 0.3))
            pygame.draw.circle(screen, (255, 150, 30), (ship_x, ship_y + 35), glow_size)
            pygame.draw.circle(
                screen, (255, 220, 100), (ship_x, ship_y + 35), glow_size // 2
            )

        # Text
        if progress < 0.3:
            text = self._font.render("APPROACHING NOVA KEPLER-7", True, (200, 220, 200))
        elif progress < 0.7:
            text = self._font.render(
                "INITIATING LANDING SEQUENCE", True, (200, 220, 200)
            )
        else:
            text = self._font.render("TOUCHDOWN", True, (0, 255, 100))

        tr = text.get_rect(centerx=self._sw // 2, top=int(30 * self._fs))
        screen.blit(text, tr)

        # Skip hint
        if self._frame > 30:
            hint = self._small_font.render("Press ENTER to skip", True, (150, 150, 150))
            hr = hint.get_rect(
                centerx=self._sw // 2, bottom=self._sh - int(20 * self._fs)
            )
            screen.blit(hint, hr)

        pygame.display.flip()
