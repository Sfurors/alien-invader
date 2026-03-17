"""Cyber lizard AI controller — simple state machine."""

import random
from .rts_settings import RTSSettings as S
from .entity_base import BaseBuilding
from .entity_registry import UNIT_DEFS, BUILDING_DEFS
from .pathfinding import find_path
from .buildings import can_place_building


class LizardAI:
    """AI that controls the cyber lizard faction."""

    # States
    BUILDUP = "buildup"
    SCOUT = "scout"
    ATTACK = "attack"
    DEFEND = "defend"

    def __init__(self):
        self.state = self.BUILDUP
        self.frame = 0
        self.crystals = 300  # AI has its own resource pool
        self.isotope = S.AI_STARTING_ISOTOPE
        self.last_produce_frame = 0
        self.last_attack_frame = 0
        self.attack_target = None
        self.defend_target = None  # (tx, ty) location to defend
        self.has_war_pit = False
        self.has_isotope_siphon = False
        self.last_supply_drop = 0
        self.desired_drones = 2  # target number of drones

    def update(self, rts_ctx):
        self.frame += 1

        # Supply drop from starships
        self._supply_drop(rts_ctx)

        # Manage drones — send idle ones to harvest
        self._manage_drones(rts_ctx)

        # State transitions
        if self.state == self.BUILDUP:
            if self.frame >= S.AI_BUILDUP_DURATION:
                self.state = self.SCOUT
        elif self.state == self.SCOUT:
            if self.frame - self.last_attack_frame >= S.AI_ATTACK_INTERVAL:
                self.state = self.ATTACK
        elif self.state == self.ATTACK:
            # Stay in attack until all military units are idle (arrived or dead)
            military = [u for u in rts_ctx.enemy_units if u.attack_power > 0]
            if not military:
                self.state = self.BUILDUP
            else:
                all_idle = all(
                    not u.moving and u.attack_target is None for u in military
                )
                if all_idle:
                    self.state = self.SCOUT
                    self.last_attack_frame = self.frame
        elif self.state == self.DEFEND:
            # Check if threat is gone
            threat = self._find_threat(rts_ctx)
            if threat:
                self.defend_target = threat
            else:
                self.defend_target = None
                self.state = self.SCOUT

        # Check if any building or unit is under attack -> switch to defend
        threat = self._find_threat(rts_ctx)
        if threat and self.state != self.DEFEND:
            self.state = self.DEFEND
            self.defend_target = threat

        # Produce units
        self._produce(rts_ctx)

        # Build isotope siphon first (needed for war_pit isotope cost)
        if not self.has_isotope_siphon and self.crystals >= 150:
            self._build_isotope_siphon(rts_ctx)

        # Build war pit if enough resources and don't have one
        if not self.has_war_pit:
            cost = BUILDING_DEFS["war_pit"]["cost"]
            if self.crystals >= cost["crystals"] and self.isotope >= cost["isotope"]:
                self._build_war_pit(rts_ctx)

        # Retarget idle military units near enemies
        self._retarget_idle(rts_ctx)

        # Execute state behavior
        if self.state == self.SCOUT:
            self._do_scout(rts_ctx)
        elif self.state == self.ATTACK:
            self._do_attack(rts_ctx)
        elif self.state == self.DEFEND:
            self._do_defend(rts_ctx)

    def _get_hive(self, rts_ctx):
        for b in rts_ctx.enemy_buildings:
            if b.building_type == "hive":
                return b
        return None

    def _produce(self, rts_ctx):
        if self.frame - self.last_produce_frame < S.AI_PRODUCE_INTERVAL:
            return

        # Count current drones
        drone_count = sum(1 for u in rts_ctx.enemy_units if u.unit_type == "drone")

        for building in rts_ctx.enemy_buildings:
            if building.under_construction or not building.produces:
                continue
            if len(building.production_queue) >= 2:
                continue

            # Decide what to produce
            if building.building_type == "hive":
                # Prioritize drones if below target
                if drone_count < self.desired_drones:
                    unit_type = "drone"
                else:
                    unit_type = "scout"
            elif building.building_type == "war_pit":
                unit_type = random.choice(["warrior", "spitter"])
            else:
                continue

            cost = UNIT_DEFS[unit_type]["cost"]
            if self.crystals >= cost["crystals"] and self.isotope >= cost["isotope"]:
                self.crystals -= cost["crystals"]
                self.isotope -= cost["isotope"]
                building.start_production(unit_type)
                self.last_produce_frame = self.frame
                if unit_type == "drone":
                    drone_count += 1

    def _build_isotope_siphon(self, rts_ctx):
        """Build isotope siphon near nearest isotope deposit."""
        hive = self._get_hive(rts_ctx)
        if not hive:
            return

        # Find nearest isotope tile to hive
        hcx, hcy = hive.center_tile()
        best_tile = None
        best_dist = float("inf")
        tm = rts_ctx.tile_map
        for ty in range(tm.height):
            for tx in range(tm.width):
                if tm.tiles[ty][tx] == S.ISOTOPE and tm.isotope[ty][tx] > 0:
                    d = abs(tx - hcx) + abs(ty - hcy)
                    if d < best_dist:
                        best_dist = d
                        best_tile = (tx, ty)

        if not best_tile:
            return

        # Try to place siphon within 2 tiles of the isotope deposit
        itx, ity = best_tile
        size = BUILDING_DEFS["isotope_siphon"]["size"]
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                px, py = itx + dx, ity + dy
                if can_place_building(tm, px, py, size, rts_ctx):
                    self.crystals -= 150
                    building = BaseBuilding("isotope_siphon", px, py, "lizard")
                    building.under_construction = True
                    building.build_time = 360  # half speed: 6 sec
                    building.tile_map = tm
                    rts_ctx.enemy_buildings.add(building)
                    rts_ctx.all_entities.add(building)
                    self.has_isotope_siphon = True
                    return

    def _build_war_pit(self, rts_ctx):
        hive = self._get_hive(rts_ctx)
        if not hive:
            return

        cost = BUILDING_DEFS["war_pit"]["cost"]
        # Try to place near hive
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                tx = hive.tile_x + hive.size[0] + dx
                ty = hive.tile_y + dy
                size = BUILDING_DEFS["war_pit"]["size"]
                if can_place_building(rts_ctx.tile_map, tx, ty, size, rts_ctx):
                    self.crystals -= cost["crystals"]
                    self.isotope -= cost["isotope"]
                    building = BaseBuilding("war_pit", tx, ty, "lizard")
                    building.under_construction = True
                    building.build_time = 360  # half speed: 6 sec
                    building.tile_map = rts_ctx.tile_map
                    rts_ctx.enemy_buildings.add(building)
                    rts_ctx.all_entities.add(building)
                    self.has_war_pit = True
                    return

    def _manage_drones(self, rts_ctx):
        """Send idle drones to nearest resource tile to harvest."""
        occupied = self._get_occupied(rts_ctx)

        # Check if we have an isotope siphon that needs a drone
        isotope_siphon = None
        for b in rts_ctx.enemy_buildings:
            if b.building_type == "isotope_siphon" and not b.under_construction:
                isotope_siphon = b
                break

        # Check if any drone is already assigned to isotope
        has_isotope_drone = any(
            u.unit_type == "drone" and u.assigned_isotope_camp is not None
            for u in rts_ctx.enemy_units
        )

        for unit in rts_ctx.enemy_units:
            if unit.unit_type != "drone":
                continue
            # Skip drones already harvesting/returning/moving
            if unit.harvesting or unit.returning or unit.moving:
                continue

            # Full of crystals — send to base
            if unit.carrying >= unit.carry_capacity:
                unit.returning = True
                from .units import _send_to_base

                _send_to_base(unit, rts_ctx, occupied)
                continue

            # Full of isotope — send to siphon or base
            if (
                unit.carrying_isotope >= unit.isotope_carry_capacity
                and unit.isotope_carry_capacity > 0
            ):
                unit.returning = True
                if unit.assigned_isotope_camp and unit.assigned_isotope_camp.alive():
                    from .units import _send_to_isotope_camp

                    _send_to_isotope_camp(unit, rts_ctx, occupied)
                else:
                    from .units import _send_to_base

                    _send_to_base(unit, rts_ctx, occupied)
                continue

            # Assign one drone to isotope if siphon exists and no drone assigned yet
            if (
                isotope_siphon
                and not has_isotope_drone
                and not unit.assigned_isotope_camp
            ):
                unit.assigned_isotope_camp = isotope_siphon
                unit.harvest_resource_type = "isotope"
                has_isotope_drone = True
                # Will be handled by _handle_isotope_camp_idle
                continue

            # Find nearest crystal tile
            best_tile = None
            best_dist = float("inf")
            tm = rts_ctx.tile_map
            for ty in range(tm.height):
                for tx in range(tm.width):
                    if tm.tiles[ty][tx] == S.CRYSTAL and tm.crystal[ty][tx] > 0:
                        d = unit.distance_to_tile(tx, ty)
                        if d < best_dist:
                            best_dist = d
                            best_tile = (tx, ty)
            if best_tile:
                unit.harvest_target = best_tile
                unit.harvesting = True
                unit.harvest_resource_type = "crystal"
                path = find_path(
                    rts_ctx.tile_map,
                    (unit.tile_x, unit.tile_y),
                    best_tile,
                    occupied,
                )
                if path:
                    unit.set_move_target(path)
                    unit.harvesting = True
                    unit.harvest_target = best_tile
                    unit.harvest_resource_type = "crystal"

    def _supply_drop(self, rts_ctx):
        """Periodic starship supply drop — creates a new crystal tile on the map."""
        if self.frame - self.last_supply_drop < S.AI_SUPPLY_DROP_INTERVAL:
            return
        self.last_supply_drop = self.frame

        # Find a random passable tile on the map for the drop
        tm = rts_ctx.tile_map
        for _ in range(50):
            tx = random.randint(5, tm.width - 6)
            ty = random.randint(5, tm.height - 6)
            if tm.tiles[ty][tx] == S.GRASS and tm.is_passable(tx, ty):
                tm.tiles[ty][tx] = S.CRYSTAL
                tm.crystal[ty][tx] = S.AI_SUPPLY_DROP_AMOUNT
                break

    def _do_scout(self, rts_ctx):
        """Send idle scouts to explore. Scouts that spot enemies assess and react."""
        occupied = self._get_occupied(rts_ctx)

        for unit in rts_ctx.enemy_units:
            if unit.attack_power <= 0:
                continue

            # Check if this unit can see player entities
            nearest_enemy = None
            nearest_dist = float("inf")
            for pu in rts_ctx.player_units:
                d = unit.distance_to_tile(pu.tile_x, pu.tile_y)
                if d < nearest_dist:
                    nearest_dist = d
                    nearest_enemy = pu
            for pb in rts_ctx.player_buildings:
                cx, cy = pb.center_tile()
                d = unit.distance_to_tile(cx, cy)
                if d < nearest_dist:
                    nearest_dist = d
                    nearest_enemy = pb

            if nearest_enemy and nearest_dist <= unit.vision + 1:
                friendly_nearby = sum(
                    1
                    for u in rts_ctx.enemy_units
                    if u.attack_power > 0
                    and unit.distance_to_tile(u.tile_x, u.tile_y) <= 8
                )
                enemy_nearby = sum(
                    1
                    for u in rts_ctx.player_units
                    if u.attack_power > 0
                    and unit.distance_to_tile(u.tile_x, u.tile_y) <= 10
                )

                if (
                    friendly_nearby >= enemy_nearby
                    or enemy_nearby == 0
                    or nearest_dist <= unit.attack_range + 2
                ):
                    unit.attack_target = nearest_enemy
                else:
                    hive = self._get_hive(rts_ctx)
                    if hive and not unit.moving:
                        cx, cy = hive.center_tile()
                        path = find_path(
                            rts_ctx.tile_map,
                            (unit.tile_x, unit.tile_y),
                            (cx, cy),
                            occupied,
                        )
                        if path:
                            unit.set_move_target(path)
                    remaining = S.AI_ATTACK_INTERVAL - (
                        self.frame - self.last_attack_frame
                    )
                    if remaining > S.AI_ATTACK_INTERVAL // 3:
                        self.last_attack_frame = (
                            self.frame - S.AI_ATTACK_INTERVAL * 2 // 3
                        )
                continue

            # No enemies spotted — send idle scouts to explore
            if (
                self.frame % S.AI_SCOUT_INTERVAL == 0
                and unit.unit_type == "scout"
                and not unit.moving
                and unit.attack_target is None
            ):
                tx = random.randint(0, rts_ctx.tile_map.width - 1)
                ty = random.randint(0, rts_ctx.tile_map.height - 1)
                path = find_path(
                    rts_ctx.tile_map, (unit.tile_x, unit.tile_y), (tx, ty), occupied
                )
                if path:
                    unit.set_move_target(path)
                break

    def _do_attack(self, rts_ctx):
        """Group military units and send toward player base."""
        target = self._find_player_base(rts_ctx)
        if target is None:
            return

        tx, ty = target
        occupied = self._get_occupied(rts_ctx)
        for unit in rts_ctx.enemy_units:
            if unit.attack_power <= 0:
                continue
            # Skip units already fighting
            if unit.attack_target is not None and unit.attack_target.alive():
                continue
            if not unit.moving:
                path = find_path(
                    rts_ctx.tile_map, (unit.tile_x, unit.tile_y), (tx, ty), occupied
                )
                if path:
                    unit.set_move_target(path)
                # Find nearest player entity to target
                best = None
                best_dist = float("inf")
                for pu in rts_ctx.player_units:
                    d = unit.distance_to_tile(pu.tile_x, pu.tile_y)
                    if d < best_dist:
                        best_dist = d
                        best = pu
                for pb in rts_ctx.player_buildings:
                    cx, cy = pb.center_tile()
                    d = unit.distance_to_tile(cx, cy)
                    if d < best_dist:
                        best_dist = d
                        best = pb
                unit.attack_target = best

    def _retarget_idle(self, rts_ctx):
        """Give idle military units near enemies a new attack target."""
        # Use wider search range during attack state
        extra_range = 10 if self.state == self.ATTACK else 0

        for unit in rts_ctx.enemy_units:
            if unit.attack_power <= 0:
                continue
            if unit.attack_target is not None and unit.attack_target.alive():
                continue
            if unit.moving:
                continue
            search_range = unit.vision + 1 + extra_range
            best = None
            best_dist = float("inf")
            for pu in rts_ctx.player_units:
                d = unit.distance_to_tile(pu.tile_x, pu.tile_y)
                if d <= search_range and d < best_dist:
                    best_dist = d
                    best = pu
            for pb in rts_ctx.player_buildings:
                cx, cy = pb.center_tile()
                d = unit.distance_to_tile(cx, cy)
                if d <= search_range and d < best_dist:
                    best_dist = d
                    best = pb
            if best:
                unit.attack_target = best
                # Also path toward it if not already moving
                if not unit.path:
                    if hasattr(best, "center_tile"):
                        tx, ty = best.center_tile()
                    else:
                        tx, ty = best.tile_x, best.tile_y
                    occupied = self._get_occupied(rts_ctx)
                    path = find_path(
                        rts_ctx.tile_map,
                        (unit.tile_x, unit.tile_y),
                        (tx, ty),
                        occupied,
                    )
                    if path:
                        unit.set_move_target(path)
                        unit.attack_target = best

    def _find_threat(self, rts_ctx):
        """Find location of threat: any enemy building or unit recently hit."""
        for b in rts_ctx.enemy_buildings:
            if b.last_hit_frame is not None and b.last_hit_frame < 120:
                return b.center_tile()
        for u in rts_ctx.enemy_units:
            if u.last_hit_frame is not None and u.last_hit_frame < 120:
                return (u.tile_x, u.tile_y)
        for b in rts_ctx.enemy_buildings:
            cx, cy = b.center_tile()
            for pu in rts_ctx.player_units:
                if pu.distance_to_tile(cx, cy) < 8:
                    return (pu.tile_x, pu.tile_y)
        return None

    def _do_defend(self, rts_ctx):
        """Send military units to defend the threatened location."""
        if not self.defend_target:
            return

        tx, ty = self.defend_target
        occupied = self._get_occupied(rts_ctx)

        for unit in rts_ctx.enemy_units:
            if unit.attack_power <= 0:
                continue
            if unit.attack_target is not None and unit.attack_target.alive():
                continue

            best = None
            best_dist = float("inf")
            for pu in rts_ctx.player_units:
                d = unit.distance_to_tile(pu.tile_x, pu.tile_y)
                if d < best_dist:
                    best_dist = d
                    best = pu

            if best and best_dist <= unit.attack_range + 2:
                unit.attack_target = best
            elif not unit.moving:
                path = find_path(
                    rts_ctx.tile_map, (unit.tile_x, unit.tile_y), (tx, ty), occupied
                )
                if path:
                    unit.set_move_target(path)
                    if best:
                        unit.attack_target = best

    def _find_player_base(self, rts_ctx):
        """Find player's main base tile position."""
        for b in rts_ctx.player_buildings:
            if b.building_type == "main_base":
                return b.center_tile()
        for b in rts_ctx.player_buildings:
            return b.center_tile()
        for u in rts_ctx.player_units:
            return (u.tile_x, u.tile_y)
        return None

    def _get_occupied(self, rts_ctx):
        occupied = set()
        for b in rts_ctx.player_buildings:
            for dy in range(b.size[1]):
                for dx in range(b.size[0]):
                    occupied.add((b.tile_x + dx, b.tile_y + dy))
        for b in rts_ctx.enemy_buildings:
            for dy in range(b.size[1]):
                for dx in range(b.size[0]):
                    occupied.add((b.tile_x + dx, b.tile_y + dy))
        return occupied
