"""Dungeon player state: position, angle, health, weapons."""

from .dungeon_settings import DungeonSettings
from . import dungeon_map


class DungeonPlayer:
    def __init__(self, x, y):
        # Position in tile coordinates (float)
        self.x = x + 0.5
        self.y = y + 0.5
        self.angle = 0.0  # radians, 0 = east

        self.hp = DungeonSettings.PLAYER_MAX_HP
        self.alive = True

        # Weapons: dict of weapon_name -> ammo (-1 = infinite)
        self.weapons = {"blaster": -1}
        self.current_weapon = "blaster"
        self.fire_cooldown = 0

        # Damage flash
        self.damage_flash = 0

        self.score = 0
        self.kills = 0

    def get_weapon_info(self):
        return DungeonSettings.WEAPONS[self.current_weapon]

    def has_weapon(self, name):
        return name in self.weapons

    def give_weapon(self, name):
        w = DungeonSettings.WEAPONS[name]
        if name not in self.weapons:
            self.weapons[name] = w["ammo"]
            self.current_weapon = name
        else:
            # Give ammo instead
            if self.weapons[name] != -1:
                self.weapons[name] += w["ammo"]

    def give_ammo(self, amount):
        """Add ammo to current limited weapon, or to first limited weapon."""
        for wname in [self.current_weapon] + list(self.weapons.keys()):
            if self.weapons.get(wname, -1) != -1:
                self.weapons[wname] += amount
                return

    def next_weapon(self):
        names = list(self.weapons.keys())
        if len(names) <= 1:
            return
        idx = names.index(self.current_weapon)
        self.current_weapon = names[(idx + 1) % len(names)]

    def can_fire(self):
        if self.fire_cooldown > 0:
            return False
        ammo = self.weapons[self.current_weapon]
        return ammo == -1 or ammo > 0

    def fire(self):
        w = self.get_weapon_info()
        self.fire_cooldown = w["fire_rate"]
        ammo = self.weapons[self.current_weapon]
        if ammo > 0:
            self.weapons[self.current_weapon] -= 1

    def take_damage(self, amount):
        self.hp -= amount
        self.damage_flash = 10
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    def heal(self, amount):
        self.hp = min(self.hp + amount, DungeonSettings.PLAYER_MAX_HP)

    def move(self, dx, dy, grid):
        """Move with wall collision."""
        r = DungeonSettings.PLAYER_SIZE
        new_x = self.x + dx
        new_y = self.y + dy

        # Check X movement
        if not _collides(new_x, self.y, r, grid):
            self.x = new_x
        # Check Y movement
        if not _collides(self.x, new_y, r, grid):
            self.y = new_y

    def update(self):
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1
        if self.damage_flash > 0:
            self.damage_flash -= 1


def _collides(x, y, radius, grid):
    """Check if a circle at (x,y) with given radius overlaps any wall."""
    height = len(grid)
    width = len(grid[0])
    # Check corners of bounding box
    for cx in [x - radius, x + radius]:
        for cy in [y - radius, y + radius]:
            ix, iy = int(cx), int(cy)
            if ix < 0 or iy < 0 or ix >= width or iy >= height:
                return True
            if dungeon_map.is_wall(grid[iy][ix]):
                return True
    return False
