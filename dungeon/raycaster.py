"""Core raycasting engine — renders the 3D view onto a pygame Surface."""

import math
import pygame
from .dungeon_settings import DungeonSettings
from . import dungeon_map

# Precompute
_DEG_TO_RAD = math.pi / 180
_HALF_FOV = DungeonSettings.FOV / 2 * _DEG_TO_RAD
_NUM_RAYS = DungeonSettings.RENDER_WIDTH
_DELTA_ANGLE = 2 * _HALF_FOV / _NUM_RAYS
_RENDER_H = DungeonSettings.RENDER_HEIGHT - DungeonSettings.HUD_HEIGHT
_HALF_RENDER_H = _RENDER_H / 2
_PROJ_DIST = _NUM_RAYS / (2 * math.tan(_HALF_FOV))


def cast_rays(player, grid):
    """Cast all rays and return list of (distance, wall_type, is_vertical_hit)."""
    results = []
    ray_angle = player.angle - _HALF_FOV
    height = len(grid)
    width = len(grid[0])

    for _ in range(_NUM_RAYS):
        sin_a = math.sin(ray_angle)
        cos_a = math.cos(ray_angle)

        # DDA raycasting
        dist, wall_type, vert = _dda(
            player.x, player.y, sin_a, cos_a, grid, width, height
        )
        # Fix fisheye
        dist *= math.cos(ray_angle - player.angle)
        results.append((dist, wall_type, vert))
        ray_angle += _DELTA_ANGLE

    return results


def _dda(px, py, sin_a, cos_a, grid, width, height):
    """Digital Differential Analyzer for a single ray."""
    max_depth = DungeonSettings.MAX_DEPTH

    # Avoid division by zero
    if abs(cos_a) < 1e-8:
        cos_a = 1e-8
    if abs(sin_a) < 1e-8:
        sin_a = 1e-8

    # Horizontal intersections (checking rows)
    y_step = 1 if sin_a > 0 else -1
    y_boundary = int(py) + (1 if sin_a > 0 else 0)
    depth_h = (y_boundary - py) / sin_a
    x_h = px + depth_h * cos_a
    delta_depth_h = y_step / sin_a
    dx_h = delta_depth_h * cos_a

    h_dist = max_depth
    h_wall = 1
    for _ in range(max_depth):
        tile_x = int(x_h)
        tile_y = int(y_boundary) if sin_a > 0 else int(y_boundary) - 1
        if 0 <= tile_x < width and 0 <= tile_y < height:
            if dungeon_map.is_wall(grid[tile_y][tile_x]):
                h_dist = depth_h
                h_wall = grid[tile_y][tile_x]
                break
        x_h += dx_h
        y_boundary += y_step
        depth_h += abs(delta_depth_h)

    # Vertical intersections (checking columns)
    x_step = 1 if cos_a > 0 else -1
    x_boundary = int(px) + (1 if cos_a > 0 else 0)
    depth_v = (x_boundary - px) / cos_a
    y_v = py + depth_v * sin_a
    delta_depth_v = x_step / cos_a
    dy_v = delta_depth_v * sin_a

    v_dist = max_depth
    v_wall = 1
    for _ in range(max_depth):
        tile_x = int(x_boundary) if cos_a > 0 else int(x_boundary) - 1
        tile_y = int(y_v)
        if 0 <= tile_x < width and 0 <= tile_y < height:
            if dungeon_map.is_wall(grid[tile_y][tile_x]):
                v_dist = depth_v
                v_wall = grid[tile_y][tile_x]
                break
        y_v += dy_v
        x_boundary += x_step
        depth_v += abs(delta_depth_v)

    if h_dist < v_dist:
        return h_dist, h_wall, False
    return v_dist, v_wall, True


def render_frame(surface, player, grid, enemies, pickups):
    """Render one frame of the raycasted view onto surface."""
    rw = DungeonSettings.RENDER_WIDTH
    rh = _RENDER_H

    # Clear: ceiling and floor
    surface.fill(DungeonSettings.CEILING_COLOR, (0, 0, rw, rh // 2))
    surface.fill(DungeonSettings.FLOOR_COLOR, (0, rh // 2, rw, rh // 2))

    # Cast walls
    ray_data = cast_rays(player, grid)
    z_buffer = []

    for col, (dist, wall_type, is_vert) in enumerate(ray_data):
        if dist <= 0:
            dist = 0.001
        wall_h = min(rh, int(_PROJ_DIST / dist))
        y_offset = (rh - wall_h) // 2

        color = DungeonSettings.WALL_COLORS.get(wall_type, (100, 100, 100))
        # Darken vertical hits for depth shading
        if is_vert:
            color = (color[0] * 3 // 4, color[1] * 3 // 4, color[2] * 3 // 4)
        # Distance fog
        fog = max(0.2, 1.0 - dist / DungeonSettings.MAX_DEPTH)
        color = (int(color[0] * fog), int(color[1] * fog), int(color[2] * fog))

        pygame.draw.line(surface, color, (col, y_offset), (col, y_offset + wall_h))
        z_buffer.append(dist)

    # Render sprites (enemies + pickups) as billboards
    _render_sprites(surface, player, enemies, pickups, z_buffer)


def _render_sprites(surface, player, enemies, pickups, z_buffer):
    """Render enemies and pickups as billboard sprites sorted by distance."""
    rw = DungeonSettings.RENDER_WIDTH
    rh = _RENDER_H

    sprite_list = []

    for e in enemies:
        if not e.alive and e.death_timer <= 0:
            continue
        dx = e.x - player.x
        dy = e.y - player.y
        dist = math.sqrt(dx * dx + dy * dy)
        angle = math.atan2(dy, dx) - player.angle
        # Normalize angle
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        if abs(angle) < _HALF_FOV + 0.2:
            color = e.color if e.alive else (80, 80, 80)
            if e.pain_timer > 0:
                color = (255, 255, 255)
            sprite_list.append((dist, angle, e.size, color, "enemy", e))

    for p in pickups:
        dx = p["x"] - player.x
        dy = p["y"] - player.y
        dist = math.sqrt(dx * dx + dy * dy)
        angle = math.atan2(dy, dx) - player.angle
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        if abs(angle) < _HALF_FOV + 0.2:
            sprite_list.append((dist, angle, 0.25, p["color"], "pickup", p))

    # Sort back to front
    sprite_list.sort(key=lambda s: -s[0])

    for dist, angle, size, color, kind, obj in sprite_list:
        if dist < 0.1:
            continue
        sprite_h = min(rh, int(_PROJ_DIST * size / dist))
        sprite_w = sprite_h
        screen_x = int(rw / 2 + angle * rw / (2 * _HALF_FOV)) - sprite_w // 2
        screen_y = (rh - sprite_h) // 2

        # Draw column by column, checking z-buffer
        for sx in range(max(0, screen_x), min(rw, screen_x + sprite_w)):
            if z_buffer[sx] > dist:
                fog = max(0.2, 1.0 - dist / DungeonSettings.MAX_DEPTH)
                c = (int(color[0] * fog), int(color[1] * fog), int(color[2] * fog))
                pygame.draw.line(surface, c, (sx, screen_y), (sx, screen_y + sprite_h))
