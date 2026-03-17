"""Minimap renderer showing terrain, fog, units, and camera rect."""

import math
import pygame
from .rts_settings import RTSSettings as S


class Minimap:
    def __init__(self, size=S.MINIMAP_SIZE):
        self.size = size
        self.surface = pygame.Surface((size, size))
        self.scale_x = size / S.MAP_PIXEL_W
        self.scale_y = size / S.MAP_PIXEL_H
        # Cache terrain surface to avoid redrawing 36k+ tiles every frame
        self._terrain_cache = pygame.Surface((size, size))
        self._terrain_dirty = True
        self._draw_count = 0
        # Screen rect (set during draw, used for click detection)
        self.last_screen_rect = None

    def mark_dirty(self):
        """Call when fog or terrain changes to refresh the cached terrain."""
        self._terrain_dirty = True

    def _rebuild_terrain(self, tile_map, fog):
        """Redraw terrain+fog onto the cached surface."""
        self._terrain_cache.fill((0, 0, 0))
        tile_w = self.size / tile_map.width
        tile_h = self.size / tile_map.height
        pw = max(1, round(tile_w))
        ph = max(1, round(tile_h))

        for ty in range(tile_map.height):
            for tx in range(tile_map.width):
                if not fog.is_explored(tx, ty):
                    continue
                color = S.TERRAIN_COLORS.get(tile_map.tiles[ty][tx], (60, 120, 40))
                if not fog.is_visible(tx, ty):
                    color = tuple(c // 2 for c in color)
                mx = round(tx * tile_w)
                my = round(ty * tile_h)
                pygame.draw.rect(self._terrain_cache, color, (mx, my, pw, ph))
        self._terrain_dirty = False

    def draw(self, screen, x, y, tile_map, fog, camera, rts_ctx, state=None):
        # Rebuild terrain cache every 10 frames (fog changes each frame)
        self._draw_count += 1
        if self._terrain_dirty or self._draw_count % 10 == 0:
            self._rebuild_terrain(tile_map, fog)

        self.surface.blit(self._terrain_cache, (0, 0))

        # Draw units as dots
        for unit in rts_ctx.player_units:
            mx = int(unit.px * self.scale_x)
            my = int(unit.py * self.scale_y)
            pygame.draw.rect(self.surface, (0, 200, 255), (mx, my, 2, 2))

        for unit in rts_ctx.enemy_units:
            etx, ety = unit.tile_x, unit.tile_y
            if fog.is_visible(etx, ety):
                mx = int(unit.px * self.scale_x)
                my = int(unit.py * self.scale_y)
                pygame.draw.rect(self.surface, (255, 60, 60), (mx, my, 2, 2))

        # Draw buildings
        for b in rts_ctx.player_buildings:
            mx = int(b.px * self.scale_x)
            my = int(b.py * self.scale_y)
            bw = max(2, int(b.size[0] * S.TILE_SIZE * self.scale_x))
            bh = max(2, int(b.size[1] * S.TILE_SIZE * self.scale_y))
            pygame.draw.rect(self.surface, (0, 150, 255), (mx, my, bw, bh))

        for b in rts_ctx.enemy_buildings:
            ctx, cty = b.center_tile()
            if fog.is_visible(ctx, cty):
                mx = int(b.px * self.scale_x)
                my = int(b.py * self.scale_y)
                bw = max(2, int(b.size[0] * S.TILE_SIZE * self.scale_x))
                bh = max(2, int(b.size[1] * S.TILE_SIZE * self.scale_y))
                pygame.draw.rect(self.surface, (255, 80, 30), (mx, my, bw, bh))

        # Draw minimap alerts (scout seppuku pulsing red circles)
        if state and state.minimap_alerts:
            alert_duration = 180  # 3 seconds at 60fps
            alive_alerts = []
            for alert in state.minimap_alerts:
                atx, aty, start_frame = alert
                age = state.frame - start_frame
                if age > alert_duration:
                    continue
                alive_alerts.append(alert)
                # Pulsing radius via sin
                base_radius = 4
                pulse = math.sin(age * 0.15) * 2 + base_radius
                radius = max(2, int(pulse))
                # Fade alpha based on age
                alpha = max(0, 255 - int(255 * age / alert_duration))
                amx = int(atx * S.TILE_SIZE * self.scale_x)
                amy = int(aty * S.TILE_SIZE * self.scale_y)
                alert_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(
                    alert_surf, (255, 40, 40, alpha), (radius, radius), radius
                )
                self.surface.blit(alert_surf, (amx - radius, amy - radius))
            state.minimap_alerts = alive_alerts

        # Camera viewport rectangle
        cam_x = int(camera.x * self.scale_x)
        cam_y = int(camera.y * self.scale_y)
        cam_w = max(4, int(camera.screen_w * self.scale_x))
        cam_h = max(4, int(camera.viewport_h * self.scale_y))
        pygame.draw.rect(self.surface, (255, 255, 255), (cam_x, cam_y, cam_w, cam_h), 1)

        # Blit to screen
        screen.blit(self.surface, (x, y))
        pygame.draw.rect(screen, (100, 100, 100), (x, y, self.size, self.size), 1)
        self.last_screen_rect = pygame.Rect(x, y, self.size, self.size)

    def minimap_to_world(self, click_x, click_y):
        """Convert screen click position to (world_px, world_py, tile_x, tile_y)."""
        r = self.last_screen_rect
        local_x = click_x - r.x
        local_y = click_y - r.y
        world_px = local_x / self.scale_x
        world_py = local_y / self.scale_y
        tile_x = int(world_px // S.TILE_SIZE)
        tile_y = int(world_py // S.TILE_SIZE)
        return world_px, world_py, tile_x, tile_y
