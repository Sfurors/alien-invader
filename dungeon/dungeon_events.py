"""Dungeon mode input handling."""

import sys
import math
import random
import pygame
from .dungeon_settings import DungeonSettings
from . import dungeon_map


def handle_events(ctx):
    """Process input events. Returns 'quit' to exit game, None otherwise."""
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                sys.exit()
            elif event.key == pygame.K_ESCAPE:
                return "quit"
            elif event.key == pygame.K_TAB:
                ctx.player.next_weapon()
            elif event.key == pygame.K_RETURN:
                if not ctx.player.alive:
                    return "dead"
                if ctx.floor_complete:
                    return "next_floor"

    # Continuous input
    _handle_movement(ctx)
    _handle_mouse(ctx)
    _handle_fire(ctx)
    return None


def _handle_movement(ctx):
    """WASD movement."""
    keys = pygame.key.get_pressed()
    player = ctx.player
    if not player.alive:
        return

    speed = DungeonSettings.PLAYER_SPEED
    dx, dy = 0.0, 0.0

    if keys[pygame.K_w]:
        dx += math.cos(player.angle) * speed
        dy += math.sin(player.angle) * speed
    if keys[pygame.K_s]:
        dx -= math.cos(player.angle) * speed
        dy -= math.sin(player.angle) * speed
    if keys[pygame.K_a]:
        dx += math.cos(player.angle - math.pi / 2) * speed
        dy += math.sin(player.angle - math.pi / 2) * speed
    if keys[pygame.K_d]:
        dx += math.cos(player.angle + math.pi / 2) * speed
        dy += math.sin(player.angle + math.pi / 2) * speed

    # Keyboard rotation fallback (arrow keys)
    if keys[pygame.K_LEFT]:
        player.angle -= DungeonSettings.PLAYER_ROT_SPEED
    if keys[pygame.K_RIGHT]:
        player.angle += DungeonSettings.PLAYER_ROT_SPEED

    if dx != 0 or dy != 0:
        player.move(dx, dy, ctx.grid)


def _handle_mouse(ctx):
    """Mouse look."""
    if not ctx.mouse_captured:
        return
    rel_x, _ = pygame.mouse.get_rel()
    ctx.player.angle += rel_x * DungeonSettings.MOUSE_SENSITIVITY


def _handle_fire(ctx):
    """Fire weapon on mouse click or held button."""
    if not ctx.player.alive:
        return
    mouse_buttons = pygame.mouse.get_pressed()
    if mouse_buttons[0] and ctx.player.can_fire():
        _fire_weapon(ctx)


def _fire_weapon(ctx):
    """Fire current weapon — hitscan ray check against enemies."""
    player = ctx.player
    player.fire()
    ctx.fire_flash = 3

    if "shoot" in ctx.sounds:
        ctx.sounds["shoot"].play()

    w_info = player.get_weapon_info()

    for _ in range(w_info["projectiles"]):
        spread = w_info["spread"]
        angle = player.angle + random.uniform(-spread, spread)
        _hitscan(ctx, angle, w_info["damage"])


def _hitscan(ctx, angle, damage):
    """Cast a ray and damage the first enemy hit."""
    player = ctx.player
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    max_dist = DungeonSettings.MAX_DEPTH

    # Step along ray
    step = 0.05
    dist = 0.0
    while dist < max_dist:
        dist += step
        rx = player.x + cos_a * dist
        ry = player.y + sin_a * dist

        # Check wall hit first
        ix, iy = int(rx), int(ry)
        if 0 <= iy < len(ctx.grid) and 0 <= ix < len(ctx.grid[0]):
            if dungeon_map.is_wall(ctx.grid[iy][ix]):
                return  # hit a wall
        else:
            return

        # Check enemy hit
        for enemy in ctx.enemies:
            if not enemy.alive:
                continue
            edx = rx - enemy.x
            edy = ry - enemy.y
            if edx * edx + edy * edy < enemy.size * enemy.size:
                enemy.take_damage(damage)
                if not enemy.alive:
                    player.score += enemy.points
                    player.kills += 1
                    # Drop loot
                    if enemy.should_drop_loot():
                        loot_type = enemy.get_loot()
                        pickup_cfg = DungeonSettings.PICKUP_TYPES.get(loot_type, {})
                        ctx.pickups.append(
                            {
                                "type": loot_type,
                                "x": enemy.x,
                                "y": enemy.y,
                                "color": pickup_cfg.get("color", (200, 200, 200)),
                            }
                        )
                return
