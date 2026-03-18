"""Dungeon mode input handling."""

import sys
import math
import random
import pygame
from .dungeon_settings import DungeonSettings
from .dungeon_projectile import DungeonProjectile


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
    """Mouse look — horizontal rotation and vertical pitch."""
    if not ctx.mouse_captured:
        return
    rel_x, rel_y = pygame.mouse.get_rel()
    ctx.player.angle += rel_x * DungeonSettings.MOUSE_SENSITIVITY
    # Scale mouse Y from screen pixels to render pixels so pitch
    # behaves the same regardless of window size.
    render_h = DungeonSettings.RENDER_HEIGHT - DungeonSettings.HUD_HEIGHT
    scale_y = render_h / ctx.screen_h
    ctx.player.pitch -= rel_y * scale_y * DungeonSettings.MOUSE_SENSITIVITY_Y
    ctx.player.pitch = max(
        -DungeonSettings.MAX_PITCH,
        min(DungeonSettings.MAX_PITCH, ctx.player.pitch),
    )


def _handle_fire(ctx):
    """Fire weapon on mouse click or held button."""
    if not ctx.player.alive:
        return
    mouse_buttons = pygame.mouse.get_pressed()
    if mouse_buttons[0] and ctx.player.can_fire():
        _fire_weapon(ctx)


def _fire_weapon(ctx):
    """Fire current weapon — spawn projectile(s)."""
    player = ctx.player
    player.fire()
    ctx.fire_flash = 3

    if "shoot" in ctx.sounds:
        ctx.sounds["shoot"].play()

    w_info = player.get_weapon_info()
    # Bullets travel flat — the pitch rendering already makes them
    # appear to originate from the crosshair direction.
    speed = w_info.get("speed", DungeonSettings.PROJECTILE_SPEED)
    vz = 0.0

    for _ in range(w_info["projectiles"]):
        spread = w_info["spread"]
        angle = player.angle + random.uniform(-spread, spread)
        bullet = DungeonProjectile(
            x=player.x,
            y=player.y,
            angle=angle,
            pitch_offset=vz,
            speed=speed,
            damage=w_info["damage"],
            color=w_info["color"],
            owner="player",
        )
        ctx.projectiles.append(bullet)
