import math
import pygame
from pixel_art import draw_pixel_art

# 16 cols × 20 rows × pixel_size 4  →  64 × 80 px
_PIXEL_SIZE = 4

_PALETTE = {
    1: (155, 165, 195),  # fuselage silver-blue
    2: (200, 215, 245),  # fuselage highlight
    3: (30, 120, 220),  # cockpit glass
    4: (120, 200, 255),  # cockpit glint
    5: (60, 80, 120),  # wing dark
    6: (255, 140, 0),  # engine orange
    7: (255, 230, 80),  # engine yellow
    8: (90, 105, 135),  # engine housing
}

# Ship body without the flame rows (rows 0-12)
_SHIP_BODY = [
    # 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
    [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0],  #  0  nose tip
    [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],  #  1  nose
    [0, 0, 0, 0, 0, 0, 1, 3, 3, 1, 0, 0, 0, 0, 0, 0],  #  2  cockpit
    [0, 0, 0, 0, 0, 1, 1, 3, 3, 1, 1, 0, 0, 0, 0, 0],  #  3  cockpit
    [0, 0, 0, 0, 1, 1, 3, 3, 3, 3, 1, 1, 0, 0, 0, 0],  #  4  cockpit wide
    [0, 0, 0, 0, 1, 1, 3, 4, 4, 3, 1, 1, 0, 0, 0, 0],  #  5  cockpit glint
    [0, 0, 0, 1, 1, 1, 2, 4, 4, 2, 1, 1, 1, 0, 0, 0],  #  6  upper body
    [0, 0, 5, 5, 1, 1, 2, 2, 2, 2, 1, 1, 5, 5, 0, 0],  #  7  shoulders
    [0, 5, 5, 5, 1, 1, 1, 1, 1, 1, 1, 1, 5, 5, 5, 0],  #  8  wings start
    [5, 5, 5, 5, 1, 1, 1, 1, 1, 1, 1, 1, 5, 5, 5, 5],  #  9  wings full
    [5, 5, 5, 5, 1, 1, 1, 1, 1, 1, 1, 1, 5, 5, 5, 5],  # 10  wings full
    [0, 5, 5, 5, 1, 1, 8, 8, 8, 8, 1, 1, 5, 5, 5, 0],  # 11  engine housing
    [0, 0, 5, 0, 0, 1, 8, 8, 8, 8, 1, 0, 0, 5, 0, 0],  # 12  engine housing
]

# Idle flame (small, default)
_FLAME_IDLE = [
    [0, 0, 0, 0, 0, 1, 1, 6, 6, 1, 1, 0, 0, 0, 0, 0],  # 13  engine glow top
    [0, 0, 0, 0, 0, 6, 6, 6, 6, 6, 6, 0, 0, 0, 0, 0],  # 14  engine glow
    [0, 0, 0, 0, 0, 0, 6, 7, 7, 6, 0, 0, 0, 0, 0, 0],  # 15  flame core
    [0, 0, 0, 0, 0, 0, 7, 7, 7, 7, 0, 0, 0, 0, 0, 0],  # 16  flame
    [0, 0, 0, 0, 0, 0, 7, 7, 7, 7, 0, 0, 0, 0, 0, 0],  # 17  flame
    [0, 0, 0, 0, 0, 0, 0, 7, 7, 0, 0, 0, 0, 0, 0, 0],  # 18  flame narrow
    [0, 0, 0, 0, 0, 0, 0, 6, 6, 0, 0, 0, 0, 0, 0, 0],  # 19  flame tip
]

# Boost flame (bigger, more fire when moving up)
_FLAME_BOOST = [
    [0, 0, 0, 0, 0, 1, 1, 6, 6, 1, 1, 0, 0, 0, 0, 0],  # engine glow top
    [0, 0, 0, 0, 6, 6, 6, 6, 6, 6, 6, 6, 0, 0, 0, 0],  # engine glow wide
    [0, 0, 0, 0, 0, 6, 6, 7, 7, 6, 6, 0, 0, 0, 0, 0],  # flame outer
    [0, 0, 0, 0, 0, 6, 7, 7, 7, 7, 6, 0, 0, 0, 0, 0],  # flame core wide
    [0, 0, 0, 0, 0, 0, 7, 7, 7, 7, 0, 0, 0, 0, 0, 0],  # flame
    [0, 0, 0, 0, 0, 0, 7, 7, 7, 7, 0, 0, 0, 0, 0, 0],  # flame
    [0, 0, 0, 0, 0, 0, 6, 7, 7, 6, 0, 0, 0, 0, 0, 0],  # flame narrowing
    [0, 0, 0, 0, 0, 0, 0, 7, 7, 0, 0, 0, 0, 0, 0, 0],  # flame narrow
    [0, 0, 0, 0, 0, 0, 0, 7, 7, 0, 0, 0, 0, 0, 0, 0],  # flame narrow
    [0, 0, 0, 0, 0, 0, 0, 6, 6, 0, 0, 0, 0, 0, 0, 0],  # flame tip
    [0, 0, 0, 0, 0, 0, 0, 6, 6, 0, 0, 0, 0, 0, 0, 0],  # flame tip end
]

_COLS = len(_SHIP_BODY[0])
_BODY_ROWS = len(_SHIP_BODY)

_W = _COLS * _PIXEL_SIZE  # 64


def _build_ship_surface(flame_rows, scale):
    """Build a ship surface with the given flame, then scale it."""
    total_rows = _BODY_ROWS + len(flame_rows)
    full_map = _SHIP_BODY + flame_rows
    w = _COLS * _PIXEL_SIZE
    h = total_rows * _PIXEL_SIZE
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    draw_pixel_art(surf, full_map, _PIXEL_SIZE, _PALETTE)
    if scale != 1.0:
        sw = max(16, int(w * scale))
        sh = max(20, int(h * scale))
        return pygame.transform.smoothscale(surf, (sw, sh))
    return surf


_MAX_TILT = 12  # degrees
_TILT_SPEED = 2.0  # degrees per frame toward target
_THRUST_BLEND_SPEED = 0.15  # how fast thrust visual transitions


class Ship:
    def __init__(self, screen, ai_settings):
        self.screen = screen
        self.ai_settings = ai_settings
        self.screen_rect = screen.get_rect()

        scale = getattr(ai_settings, "resolution_scale", 1.0)
        self._scale = scale

        self._img_idle = _build_ship_surface(_FLAME_IDLE, scale)
        self._img_boost = _build_ship_surface(_FLAME_BOOST, scale)

        self.base_image = self._img_idle
        self.image = self.base_image
        self.rect = self.image.get_rect()
        self.rect.centerx = self.screen_rect.centerx
        self.rect.bottom = self.screen_rect.bottom
        self.x = float(self.rect.centerx)
        self.y = float(self.rect.bottom)
        self.radius = int(20 * scale)

        # Vertical movement boundary: bottom 1/4 of screen
        self._y_min = self.screen_rect.bottom - self.screen_rect.height // 4

        self.moving_right = False
        self.moving_left = False
        self.moving_up = False
        self.moving_down = False
        self.angle = 0.0
        self._thrust = 0.0  # 0.0 = idle, 1.0 = full boost
        self._flame_phase = 0.0  # for flame flicker

    def update(self):
        if self.moving_right and self.rect.right < self.screen_rect.right:
            self.x += self.ai_settings.ship_speed
        if self.moving_left and self.rect.left > 0:
            self.x -= self.ai_settings.ship_speed
        if self.moving_up and self.rect.top > self._y_min:
            self.y -= self.ai_settings.ship_speed
        if self.moving_down and self.rect.bottom < self.screen_rect.bottom:
            self.y += self.ai_settings.ship_speed
        self.rect.centerx = int(self.x)
        self.rect.bottom = int(self.y)

        # Thrust animation blend
        target_thrust = 1.0 if self.moving_up else 0.0
        if self._thrust < target_thrust:
            self._thrust = min(self._thrust + _THRUST_BLEND_SPEED, target_thrust)
        elif self._thrust > target_thrust:
            self._thrust = max(self._thrust - _THRUST_BLEND_SPEED, target_thrust)

        # Pick base image: boost when thrust is active
        if self._thrust > 0.5:
            self.base_image = self._img_boost
        else:
            self.base_image = self._img_idle

        # Tilt animation
        target = 0.0
        if self.moving_right and not self.moving_left:
            target = -_MAX_TILT
        elif self.moving_left and not self.moving_right:
            target = _MAX_TILT

        if self.angle < target:
            self.angle = min(self.angle + _TILT_SPEED, target)
        elif self.angle > target:
            self.angle = max(self.angle - _TILT_SPEED, target)

        if self.angle != 0.0:
            self.image = pygame.transform.rotate(self.base_image, self.angle)
        else:
            self.image = self.base_image

        old_centerx = self.rect.centerx
        old_bottom = self.rect.bottom
        self.rect = self.image.get_rect()
        self.rect.centerx = old_centerx
        self.rect.bottom = old_bottom

    def blitme(self):
        self.screen.blit(self.image, self.rect)
        # Draw flame flicker glow when thrusting
        if self._thrust > 0.3:
            self._flame_phase += 0.2
            flicker = 0.6 + 0.4 * math.sin(self._flame_phase)
            alpha = int(60 * self._thrust * flicker)
            r = int((12 + 8 * self._thrust) * self._scale)
            glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 160, 30, alpha), (r, r), r)
            glow_x = self.rect.centerx - r
            glow_y = self.rect.bottom - int(r * 0.5)
            self.screen.blit(glow, (glow_x, glow_y))

    def center(self):
        self.x = float(self.screen_rect.centerx)
        self.y = float(self.screen_rect.bottom)
        self.rect.centerx = self.screen_rect.centerx
        self.rect.bottom = self.screen_rect.bottom
        self.angle = 0.0
        self._thrust = 0.0
        self.base_image = self._img_idle
        self.image = self.base_image
        self.moving_up = False
        self.moving_down = False
