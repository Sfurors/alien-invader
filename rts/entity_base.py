"""Base entity classes: BaseUnit and BaseBuilding (Sprite subclasses)."""

import pygame
from pixel_art import draw_pixel_art
from .rts_settings import RTSSettings as S
from .rts_sprites import get_sprite_data
from .entity_registry import UNIT_DEFS, BUILDING_DEFS


class BaseUnit(pygame.sprite.Sprite):
    """Generic unit driven by stats from entity_registry."""

    def __init__(self, unit_type, tile_x, tile_y, faction="human"):
        super().__init__()
        self.unit_type = unit_type
        self.faction = faction
        stats = UNIT_DEFS[unit_type]

        self.max_hp = stats["hp"]
        self.hp = self.max_hp
        self.speed = stats["speed"]
        self.attack_power = stats["attack"]
        self.attack_range = stats["attack_range"]
        self.can_build = stats.get("can_build", False)
        self.can_harvest = stats.get("can_harvest", False)
        self.harvest_rate = stats.get("harvest_rate", 0)
        self.carry_capacity = stats.get("carry_capacity", 0)
        self.isotope_harvest_rate = stats.get("isotope_harvest_rate", 0)
        self.isotope_carry_capacity = stats.get("isotope_carry_capacity", 0)
        self.vision = stats.get("vision", S.UNIT_VISION_RANGE)

        # Position (pixel coords)
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.px = float(tile_x * S.TILE_SIZE + S.TILE_SIZE // 2)
        self.py = float(tile_y * S.TILE_SIZE + S.TILE_SIZE // 2)

        # Movement
        self.path = []  # list of (tx, ty)
        self.moving = False

        # Combat
        self.attack_target = None
        self.attack_cooldown = 0

        # Harvesting
        self.carrying = 0
        self.carrying_isotope = 0
        self.harvest_target = None  # (tx, ty)
        self.return_target = None  # building to return to
        self.harvesting = False
        self.returning = False
        self.harvest_timer = 0
        self.harvest_cooldown_max = S.HARVEST_COOLDOWN
        self.harvest_resource_type = None  # "crystal" or "isotope"

        # Building
        self.build_target = None  # reference to building under construction
        self.building = False

        # Mining camp assignment
        self.assigned_camp = None  # reference to mining_camp building
        self.assigned_isotope_camp = None  # reference to isotope extractor/siphon
        self.caravan_mode = False
        self._normal_speed = self.speed
        self._normal_image = None  # set after _build_image

        # Scout mode (human scout auto-explore)
        self.scout_mode = False
        self.scout_timer = 0

        # Damage tracking (frames since last hit, None = never hit)
        self.last_hit_frame = None

        # Selection
        self.selected = False

        # Build sprite
        self._build_image()
        self._normal_image = self.image

    def _build_image(self):
        sprite_data = get_sprite_data(self.unit_type)
        if sprite_data:
            pmap, palette, ps = sprite_data
            w = len(pmap[0]) * ps
            h = len(pmap) * ps
            self.image = pygame.Surface((w, h), pygame.SRCALPHA)
            draw_pixel_art(self.image, pmap, ps, palette)
        else:
            self.image = pygame.Surface((S.TILE_SIZE, S.TILE_SIZE), pygame.SRCALPHA)
            color = (0, 150, 255) if self.faction == "human" else (255, 80, 30)
            pygame.draw.circle(
                self.image,
                color,
                (S.TILE_SIZE // 2, S.TILE_SIZE // 2),
                S.TILE_SIZE // 3,
            )
        self.rect = self.image.get_rect(center=(int(self.px), int(self.py)))

    def update(self):
        self._move_along_path()
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        self.rect.center = (int(self.px), int(self.py))
        self.tile_x = int(self.px) // S.TILE_SIZE
        self.tile_y = int(self.py) // S.TILE_SIZE

    def _move_along_path(self):
        if not self.path:
            self.moving = False
            return
        self.moving = True
        tx, ty = self.path[0]
        target_px = tx * S.TILE_SIZE + S.TILE_SIZE // 2
        target_py = ty * S.TILE_SIZE + S.TILE_SIZE // 2
        dx = target_px - self.px
        dy = target_py - self.py
        dist = (dx * dx + dy * dy) ** 0.5
        if dist < self.speed:
            self.px = float(target_px)
            self.py = float(target_py)
            self.path.pop(0)
        else:
            self.px += dx / dist * self.speed
            self.py += dy / dist * self.speed

    def set_move_target(self, path):
        """Set a path for this unit to follow."""
        self.path = list(path)
        self.moving = True
        self.attack_target = None
        self.harvest_target = None
        self.harvesting = False
        self.returning = False
        self.harvest_timer = 0
        self.build_target = None
        self.building = False
        self.scout_mode = False

    def distance_to_tile(self, tx, ty):
        dx = self.tile_x - tx
        dy = self.tile_y - ty
        return (dx * dx + dy * dy) ** 0.5

    def take_damage(self, amount):
        self.hp -= amount
        self.last_hit_frame = 0  # reset to 0 = "just hit"; incremented externally
        if self.hp <= 0:
            self.kill()


class BaseBuilding(pygame.sprite.Sprite):
    """Generic building driven by stats from entity_registry."""

    def __init__(self, building_type, tile_x, tile_y, faction="human"):
        super().__init__()
        self.building_type = building_type
        self.faction = faction
        stats = BUILDING_DEFS[building_type]

        self.max_hp = stats["hp"]
        self.hp = self.max_hp
        self.cost = stats["cost"]
        self.size = stats["size"]  # (w, h) in tiles
        self.produces = list(stats.get("produces", []))
        self.attack_power = stats.get("attack", 0)
        self.attack_range = stats.get("attack_range", 0)
        self.vision = stats.get("vision", S.BUILDING_VISION_RANGE)
        self.crystal_capacity = stats.get("crystal_capacity", 0)
        self.stored_crystals = 0
        self.is_mining_camp = stats.get("is_mining_camp", False)
        self.isotope_capacity = stats.get("isotope_capacity", 0)
        self.stored_isotope = 0
        self.is_isotope_camp = stats.get("is_isotope_camp", False)

        # Position (top-left tile)
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.px = tile_x * S.TILE_SIZE
        self.py = tile_y * S.TILE_SIZE

        # Construction
        self.under_construction = False
        self.build_progress = 0
        self.build_time = stats.get("build_time", 180)  # default 3s at 60fps

        # Production queue
        self.production_queue = []
        self.production_timer = 0

        # Combat (for turrets/spines)
        self.attack_target = None
        self.attack_cooldown = 0

        # Selection
        self.selected = False

        # Damage tracking
        self.last_hit_frame = None

        # Tile map reference (set after creation for ruins on destroy)
        self.tile_map = None

        # Rally point
        self.rally_x = tile_x + self.size[0]
        self.rally_y = tile_y + self.size[1]

        # Destruction stage tracking
        self.destroyed = False

        self._build_image()
        self._build_damaged_images()

    def _build_damaged_images(self):
        """Pre-build damaged stage images."""
        pw = self.size[0] * S.TILE_SIZE
        ph = self.size[1] * S.TILE_SIZE
        # Stage 1: light damage (< 66% hp) — cracks
        self.image_damaged1 = self.image.copy()
        for i in range(3):
            x1 = 4 + i * (pw // 4)
            y1 = 2 + i * (ph // 3)
            x2 = x1 + pw // 5
            y2 = y1 + ph // 4
            pygame.draw.line(self.image_damaged1, (40, 40, 40), (x1, y1), (x2, y2), 1)
        # Stage 2: heavy damage (< 33% hp) — cracks + dark overlay
        self.image_damaged2 = self.image.copy()
        dark = pygame.Surface((pw, ph), pygame.SRCALPHA)
        dark.fill((0, 0, 0, 60))
        self.image_damaged2.blit(dark, (0, 0))
        for i in range(5):
            x1 = 2 + i * (pw // 5)
            y1 = 1 + i * (ph // 4)
            x2 = x1 + pw // 4
            y2 = y1 + ph // 3
            pygame.draw.line(self.image_damaged2, (30, 30, 30), (x1, y1), (x2, y2), 2)
        # Ruins image — very dark, rubble
        self.image_ruins = pygame.Surface((pw, ph), pygame.SRCALPHA)
        self.image_ruins.fill((50, 45, 40, 200))
        for i in range(6):
            rx = (i * 7 + 3) % pw
            ry = (i * 11 + 5) % ph
            pygame.draw.rect(self.image_ruins, (70, 65, 55), (rx, ry, 6, 4))
        for i in range(4):
            rx = (i * 13 + 7) % pw
            ry = (i * 9 + 2) % ph
            pygame.draw.rect(self.image_ruins, (40, 38, 35), (rx, ry, 8, 3))

    def _build_image(self):
        pw = self.size[0] * S.TILE_SIZE
        ph = self.size[1] * S.TILE_SIZE
        sprite_data = get_sprite_data(self.building_type)
        if sprite_data:
            pmap, palette, ps = sprite_data
            raw_w = len(pmap[0]) * ps
            raw_h = len(pmap) * ps
            raw = pygame.Surface((raw_w, raw_h), pygame.SRCALPHA)
            draw_pixel_art(raw, pmap, ps, palette)
            self.image = pygame.transform.scale(raw, (pw, ph))
        else:
            self.image = pygame.Surface((pw, ph), pygame.SRCALPHA)
            color = (0, 120, 200) if self.faction == "human" else (200, 80, 30)
            pygame.draw.rect(self.image, color, (0, 0, pw, ph))
        self.rect = self.image.get_rect(topleft=(self.px, self.py))

    def update(self):
        if self.under_construction:
            if self.faction != "human":
                # Non-human buildings auto-grow (lizard buildings are semi-organic)
                self.build_progress += 1
                if self.build_progress >= self.build_time:
                    self.under_construction = False
            # Human buildings wait for an engineer
            return

        # Production
        if self.production_queue and self.production_timer > 0:
            self.production_timer -= 1

        # Combat (turrets)
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

    def start_production(self, unit_type):
        self.production_queue.append(unit_type)
        if len(self.production_queue) == 1:
            self.production_timer = S.PRODUCTION_TIME

    def pop_produced(self):
        """If production is done, return the unit type and start next."""
        if self.production_queue and self.production_timer <= 0:
            unit_type = self.production_queue.pop(0)
            if self.production_queue:
                self.production_timer = S.PRODUCTION_TIME
            return unit_type
        return None

    def occupies_tile(self, tx, ty):
        return (
            self.tile_x <= tx < self.tile_x + self.size[0]
            and self.tile_y <= ty < self.tile_y + self.size[1]
        )

    def center_tile(self):
        return (
            self.tile_x + self.size[0] // 2,
            self.tile_y + self.size[1] // 2,
        )

    def take_damage(self, amount):
        self.hp -= amount
        self.last_hit_frame = 0
        # Update damage visual
        ratio = self.hp / self.max_hp if self.max_hp > 0 else 0
        if ratio <= 0:
            self._leave_ruins()
            self.kill()
        elif ratio < 0.33:
            self.image = self.image_damaged2
        elif ratio < 0.66:
            self.image = self.image_damaged1

    def _leave_ruins(self):
        """Mark tiles as ruins when building is destroyed."""
        if self.tile_map is None:
            return
        for dy in range(self.size[1]):
            for dx in range(self.size[0]):
                tx = self.tile_x + dx
                ty = self.tile_y + dy
                if self.tile_map.in_bounds(tx, ty):
                    self.tile_map.tiles[ty][tx] = S.RUINS
