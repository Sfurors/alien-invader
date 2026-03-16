"""Minimap renderer showing terrain, fog, units, and camera rect."""

import pygame
from .rts_settings import RTSSettings as S


class Minimap:
    def __init__(self, size=S.MINIMAP_SIZE):
        self.size = size
        self.surface = pygame.Surface((size, size))
        self.scale_x = size / S.MAP_PIXEL_W
        self.scale_y = size / S.MAP_PIXEL_H

    def draw(self, screen, x, y, tile_map, fog, camera, rts_ctx):
        self.surface.fill((0, 0, 0))

        # Draw terrain
        tile_w = max(1, self.size / tile_map.width)
        tile_h = max(1, self.size / tile_map.height)
        for ty in range(tile_map.height):
            for tx in range(tile_map.width):
                if not fog.is_explored(tx, ty):
                    continue
                color = S.TERRAIN_COLORS.get(tile_map.tiles[ty][tx], (60, 120, 40))
                if not fog.is_visible(tx, ty):
                    color = tuple(c // 2 for c in color)
                mx = int(tx * tile_w)
                my = int(ty * tile_h)
                pygame.draw.rect(
                    self.surface,
                    color,
                    (mx, my, max(1, int(tile_w)), max(1, int(tile_h))),
                )

        # Draw units as dots
        for unit in rts_ctx.player_units:
            mx = int(unit.px * self.scale_x)
            my = int(unit.py * self.scale_y)
            pygame.draw.rect(self.surface, (0, 200, 255), (mx, my, 2, 2))

        for unit in rts_ctx.enemy_units:
            tx, ty = unit.tile_x, unit.tile_y
            if fog.is_visible(tx, ty):
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

        # Camera rectangle
        cam_x = int(camera.x * self.scale_x)
        cam_y = int(camera.y * self.scale_y)
        cam_w = int(camera.screen_w * self.scale_x)
        cam_h = int(camera.viewport_h * self.scale_y)
        pygame.draw.rect(self.surface, (255, 255, 255), (cam_x, cam_y, cam_w, cam_h), 1)

        # Blit to screen
        screen.blit(self.surface, (x, y))
        pygame.draw.rect(screen, (100, 100, 100), (x, y, self.size, self.size), 1)
