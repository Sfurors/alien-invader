"""Fog of war: 3-state per tile (unexplored / explored / visible)."""

import pygame
from .rts_settings import RTSSettings as S


class FogOfWar:
    def __init__(self, width=S.MAP_WIDTH, height=S.MAP_HEIGHT):
        self.width = width
        self.height = height
        # 0=unexplored, 1=explored, 2=visible
        self.state = [[S.FOG_UNEXPLORED] * width for _ in range(height)]

    def reset_visible(self):
        """Each frame, demote VISIBLE -> EXPLORED."""
        for y in range(self.height):
            for x in range(self.width):
                if self.state[y][x] == S.FOG_VISIBLE:
                    self.state[y][x] = S.FOG_EXPLORED

    def reveal(self, cx, cy, radius):
        """Mark tiles around (cx,cy) as visible."""
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx * dx + dy * dy <= radius * radius:
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        self.state[ny][nx] = S.FOG_VISIBLE

    def is_visible(self, tx, ty):
        if 0 <= tx < self.width and 0 <= ty < self.height:
            return self.state[ty][tx] == S.FOG_VISIBLE
        return False

    def is_explored(self, tx, ty):
        if 0 <= tx < self.width and 0 <= ty < self.height:
            return self.state[ty][tx] >= S.FOG_EXPLORED
        return False

    def draw_overlay(self, surface, camera):
        """Draw fog overlay on the viewport."""
        ts = S.TILE_SIZE
        start_tx = max(0, int(camera.x // ts))
        start_ty = max(0, int(camera.y // ts))
        end_tx = min(self.width, int((camera.x + camera.screen_w) // ts) + 1)
        end_ty = min(self.height, int((camera.y + camera.viewport_h) // ts) + 1)

        for ty in range(start_ty, end_ty):
            for tx in range(start_tx, end_tx):
                state = self.state[ty][tx]
                if state == S.FOG_VISIBLE:
                    continue
                sx, sy = camera.world_to_screen(tx * ts, ty * ts)
                if state == S.FOG_UNEXPLORED:
                    pygame.draw.rect(surface, (0, 0, 0), (sx, sy, ts, ts))
                else:  # explored but not visible
                    fog_surf = pygame.Surface((ts, ts), pygame.SRCALPHA)
                    fog_surf.fill((0, 0, 0, 150))
                    surface.blit(fog_surf, (sx, sy))
