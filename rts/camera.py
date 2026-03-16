"""Viewport camera for RTS map scrolling."""

from .rts_settings import RTSSettings as S


class Camera:
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.viewport_h = screen_h - S.HUD_HEIGHT
        self.x = 0.0
        self.y = 0.0
        self.max_x = S.MAP_PIXEL_W - screen_w
        self.max_y = S.MAP_PIXEL_H - self.viewport_h
        # Scrolling direction state
        self.scrolling_left = False
        self.scrolling_right = False
        self.scrolling_up = False
        self.scrolling_down = False

    def update(self):
        speed = S.CAMERA_SPEED
        if self.scrolling_left:
            self.x -= speed
        if self.scrolling_right:
            self.x += speed
        if self.scrolling_up:
            self.y -= speed
        if self.scrolling_down:
            self.y += speed
        self._clamp()

    def _clamp(self):
        self.x = max(0, min(self.x, self.max_x))
        self.y = max(0, min(self.y, self.max_y))

    def center_on(self, px, py):
        """Center camera on pixel position."""
        self.x = px - self.screen_w // 2
        self.y = py - self.viewport_h // 2
        self._clamp()

    def world_to_screen(self, wx, wy):
        return int(wx - self.x), int(wy - self.y)

    def screen_to_world(self, sx, sy):
        return sx + self.x, sy + self.y

    def screen_to_tile(self, sx, sy):
        wx, wy = self.screen_to_world(sx, sy)
        return int(wx // S.TILE_SIZE), int(wy // S.TILE_SIZE)

    def is_visible(self, wx, wy, w=S.TILE_SIZE, h=S.TILE_SIZE):
        return (
            wx + w > self.x
            and wx < self.x + self.screen_w
            and wy + h > self.y
            and wy < self.y + self.viewport_h
        )
