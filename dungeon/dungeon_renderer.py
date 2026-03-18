"""Dungeon mode rendering — scales raycaster output and draws HUD."""

import pygame
from .dungeon_settings import DungeonSettings
from . import raycaster
from . import dungeon_map


def draw_frame(screen, ctx):
    """Render one complete dungeon frame: 3D view + HUD, scaled to screen."""
    player = ctx.player
    grid = ctx.grid

    # Render 3D view at low resolution
    raycaster.render_frame(ctx.render_surface, player, grid, ctx.enemies, ctx.pickups,
                           ctx.projectiles)

    # Draw HUD bar at the bottom of the render surface
    _draw_hud(ctx.render_surface, ctx)

    # Scale up to screen
    scaled = pygame.transform.scale(ctx.render_surface, (ctx.screen_w, ctx.screen_h))
    screen.blit(scaled, (0, 0))

    # Draw weapon flash overlay
    if ctx.fire_flash > 0:
        flash_alpha = min(100, ctx.fire_flash * 20)
        flash_surf = pygame.Surface((ctx.screen_w, ctx.screen_h), pygame.SRCALPHA)
        w_info = player.get_weapon_info()
        color = w_info["color"]
        flash_surf.fill((*color, flash_alpha))
        screen.blit(flash_surf, (0, 0))

    # Draw damage flash overlay
    if player.damage_flash > 0:
        dmg_alpha = min(120, player.damage_flash * 15)
        dmg_surf = pygame.Surface((ctx.screen_w, ctx.screen_h), pygame.SRCALPHA)
        dmg_surf.fill((255, 0, 0, dmg_alpha))
        screen.blit(dmg_surf, (0, 0))

    # Draw crosshair
    cx, cy = ctx.screen_w // 2, ctx.screen_h // 2
    size = max(3, ctx.screen_w // 100)
    pygame.draw.line(screen, (255, 255, 255), (cx - size, cy), (cx + size, cy))
    pygame.draw.line(screen, (255, 255, 255), (cx, cy - size), (cx, cy + size))

    pygame.display.flip()


def _draw_hud(surface, ctx):
    """Draw HUD onto the bottom of the render surface."""
    rw = DungeonSettings.RENDER_WIDTH
    rh = DungeonSettings.RENDER_HEIGHT
    hud_h = DungeonSettings.HUD_HEIGHT
    hud_y = rh - hud_h
    player = ctx.player

    # Background
    pygame.draw.rect(surface, (20, 20, 30), (0, hud_y, rw, hud_h))
    pygame.draw.line(surface, (80, 80, 100), (0, hud_y), (rw, hud_y))

    # Health bar
    bar_w = 60
    bar_h = 8
    bar_x = 4
    bar_y = hud_y + 6
    hp_frac = player.hp / DungeonSettings.PLAYER_MAX_HP
    pygame.draw.rect(surface, (60, 0, 0), (bar_x, bar_y, bar_w, bar_h))
    pygame.draw.rect(surface, (0, 200, 0), (bar_x, bar_y, int(bar_w * hp_frac), bar_h))
    # HP text
    if ctx.hud_font:
        hp_text = ctx.hud_font.render(f"HP:{player.hp}", True, (255, 255, 255))
        surface.blit(hp_text, (bar_x, bar_y + bar_h + 2))

    # Weapon & ammo
    w_info = player.get_weapon_info()
    ammo = player.weapons[player.current_weapon]
    ammo_str = "INF" if ammo == -1 else str(ammo)
    if ctx.hud_font:
        w_text = ctx.hud_font.render(
            f"{w_info['name']}:{ammo_str}", True, w_info["color"]
        )
        surface.blit(w_text, (rw // 2 - 30, hud_y + 6))

    # Floor number
    if ctx.hud_font:
        f_text = ctx.hud_font.render(f"F{ctx.floor_num}", True, (180, 180, 200))
        surface.blit(f_text, (rw - 30, hud_y + 6))

    # Score
    if ctx.hud_font:
        s_text = ctx.hud_font.render(f"{player.score}", True, (255, 220, 50))
        surface.blit(s_text, (rw - 30, hud_y + 20))

    # Minimap
    _draw_minimap(surface, ctx, rw - 56, hud_y - 56)


def _draw_minimap(surface, ctx, x, y):
    """Draw a small minimap in the corner."""
    size = 52
    scale = 3  # pixels per tile
    player = ctx.player
    grid = ctx.grid

    # Semi-transparent background
    mm_surf = pygame.Surface((size, size), pygame.SRCALPHA)
    mm_surf.fill((0, 0, 0, 140))

    # Center on player
    pcx = int(player.x)
    pcy = int(player.y)
    half = size // (2 * scale)

    for dy in range(-half, half + 1):
        for dx in range(-half, half + 1):
            tx = pcx + dx
            ty = pcy + dy
            sx = (dx + half) * scale
            sy = (dy + half) * scale
            if 0 <= ty < len(grid) and 0 <= tx < len(grid[0]):
                tile = grid[ty][tx]
                if dungeon_map.is_wall(tile):
                    pygame.draw.rect(mm_surf, (80, 80, 100), (sx, sy, scale, scale))
                elif tile == dungeon_map.EXIT_TILE:
                    pygame.draw.rect(mm_surf, (0, 255, 0), (sx, sy, scale, scale))

    # Player dot
    px = half * scale + int((player.x - pcx) * scale)
    py_m = half * scale + int((player.y - pcy) * scale)
    pygame.draw.circle(mm_surf, (255, 255, 0), (px, py_m), 2)

    # Enemy dots
    for e in ctx.enemies:
        if e.alive:
            edx = e.x - pcx
            edy = e.y - pcy
            if abs(edx) <= half and abs(edy) <= half:
                ex = (edx + half) * scale + scale // 2
                ey = (edy + half) * scale + scale // 2
                pygame.draw.circle(mm_surf, (255, 0, 0), (int(ex), int(ey)), 1)

    surface.blit(mm_surf, (x, y))
