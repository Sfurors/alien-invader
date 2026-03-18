"""Dungeon projectiles — bullets that travel through the map."""

import math
from .dungeon_settings import DungeonSettings
from . import dungeon_map


class DungeonProjectile:
    """A bullet moving through the dungeon in 3D (x, y, z)."""

    def __init__(self, x, y, angle, pitch_offset, speed, damage, color, owner):
        """
        Args:
            x, y: start position in tile coords
            angle: horizontal direction (radians)
            pitch_offset: vertical velocity per frame (world units)
            speed: tiles per frame
            damage: hit points to deal
            color: RGB tuple for rendering
            owner: "player" or "enemy"
        """
        self.x = x
        self.y = y
        self.z = 0.5  # eye height
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.vz = pitch_offset
        self.speed = speed
        self.damage = damage
        self.color = color
        self.owner = owner
        self.alive = True
        self.dist_travelled = 0.0

    def update(self, grid):
        """Move one frame. Returns False if the projectile hit a wall or went too far."""
        self.x += self.vx
        self.y += self.vy
        self.z += self.vz
        self.dist_travelled += self.speed

        # Kill if too far
        if self.dist_travelled > DungeonSettings.MAX_DEPTH:
            self.alive = False
            return

        # Kill if hit floor or ceiling
        if self.z < 0.0 or self.z > 1.0:
            self.alive = False
            return

        # Kill if hit a wall
        ix, iy = int(self.x), int(self.y)
        if 0 <= iy < len(grid) and 0 <= ix < len(grid[0]):
            if dungeon_map.is_wall(grid[iy][ix]):
                self.alive = False
        else:
            self.alive = False
