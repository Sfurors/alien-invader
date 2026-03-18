"""Dungeon enemies — LizardCyborg types with simple AI."""

import math
import random
from .dungeon_settings import DungeonSettings
from .dungeon_projectile import DungeonProjectile
from . import dungeon_map


class DungeonEnemy:
    """A single enemy in the dungeon."""

    def __init__(self, enemy_type, x, y):
        self.type = enemy_type
        cfg = DungeonSettings.ENEMY_TYPES[enemy_type]
        self.hp = cfg["hp"]
        self.max_hp = cfg["hp"]
        self.speed = cfg["speed"]
        self.damage = cfg["damage"]
        self.attack_range = cfg["attack_range"]
        self.attack_cooldown_max = cfg["attack_cooldown"]
        self.detect_range = cfg["detect_range"]
        self.color = cfg["color"]
        self.size = cfg["size"]
        self.points = cfg["points"]
        self.drop_chance = cfg["drop_chance"]

        # Position in tile coordinates
        self.x = x + 0.5
        self.y = y + 0.5
        self.alive = True
        self.death_timer = 0  # frames since death for animation

        # AI state
        self.state = "idle"  # idle, chase, attack
        self.attack_cooldown = 0
        self.pain_timer = 0

    def take_damage(self, amount):
        self.hp -= amount
        self.pain_timer = 8
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            self.death_timer = 20

    def update(self, ctx):
        player = ctx.player
        grid = ctx.grid
        if not self.alive:
            if self.death_timer > 0:
                self.death_timer -= 1
            return

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.pain_timer > 0:
            self.pain_timer -= 1
            return  # stagger — can't move while in pain

        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.sqrt(dx * dx + dy * dy)

        has_los = _has_line_of_sight(self.x, self.y, player.x, player.y, grid)

        if dist < self.attack_range and self.attack_cooldown <= 0 and has_los:
            self.state = "attack"
            self._attack(ctx, dx, dy, dist)
        elif dist < self.detect_range and has_los:
            self.state = "chase"
            self._chase(dx, dy, dist, grid)
        else:
            self.state = "idle"

    def _attack(self, ctx, dx, dy, dist):
        """Fire a projectile toward the player."""
        self.attack_cooldown = self.attack_cooldown_max
        if dist < 0.1:
            return
        angle = math.atan2(dy, dx)
        # Slight inaccuracy so enemies aren't perfect shots
        angle += random.uniform(-0.1, 0.1)
        speed = DungeonSettings.ENEMY_PROJECTILE_SPEED
        bullet = DungeonProjectile(
            x=self.x,
            y=self.y,
            angle=angle,
            pitch_offset=0.0,  # enemies shoot flat
            speed=speed,
            damage=self.damage,
            color=self.color,
            owner="enemy",
        )
        ctx.projectiles.append(bullet)

    def _chase(self, dx, dy, dist, grid):
        if dist < 0.1:
            return
        nx = dx / dist * self.speed
        ny = dy / dist * self.speed
        # Simple collision: try to move, skip if blocked
        new_x = self.x + nx
        new_y = self.y + ny
        ix, iy = int(new_x), int(new_y)
        if 0 <= ix < len(grid[0]) and 0 <= iy < len(grid):
            if not dungeon_map.is_wall(grid[iy][ix]):
                self.x = new_x
                self.y = new_y

    def should_drop_loot(self):
        return random.random() < self.drop_chance

    def get_loot(self):
        """Return a pickup type to drop."""
        options = ["ammo", "health"]
        if self.type == "lizard_soldier":
            options.append("plasma")
        elif self.type == "lizard_brute":
            options.extend(["plasma", "rocket_launcher"])
        return random.choice(options)


def _has_line_of_sight(x1, y1, x2, y2, grid):
    """Simple raycast to check if two points can see each other."""
    dx = x2 - x1
    dy = y2 - y1
    dist = math.sqrt(dx * dx + dy * dy)
    if dist < 0.01:
        return True
    steps = int(dist * 4)
    for i in range(1, steps):
        t = i / steps
        cx = x1 + dx * t
        cy = y1 + dy * t
        if dungeon_map.is_wall(grid[int(cy)][int(cx)]):
            return False
    return True
