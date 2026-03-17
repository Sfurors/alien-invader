"""Cyber lizard AI controller — adaptive state machine with fog of war."""

import random
from .rts_settings import RTSSettings as S
from .entity_base import BaseBuilding
from .entity_registry import UNIT_DEFS, BUILDING_DEFS
from .pathfinding import find_path
from .buildings import can_place_building
from .ai_memory import AIMemory


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
        self.supply_drop_count = 0  # tracks number of drops for scaling
        self.desired_drones = 3  # target number of drones
        self.memory = AIMemory()

    def update(self, rts_ctx):
        self.frame += 1

        # Update AI fog of war
        self.memory.reset_visible()
        self._update_ai_fog(rts_ctx)
        self.memory.update_sightings(rts_ctx, self.frame)
        if self.frame % 300 == 0:  # every 5 seconds: purge dead + decay stale
            self.memory.purge_dead(rts_ctx)
            self.memory.decay_knowledge(self.frame)

        # Supply drop from starships
        self._supply_drop(rts_ctx)

        # Manage drones — send idle ones to harvest
        self._manage_drones(rts_ctx)

        # State transitions
        if self.state == self.BUILDUP:
            if self.frame >= S.AI_BUILDUP_DURATION:
                self.state = self.SCOUT
        elif self.state == self.SCOUT:
            time_since_attack = self.frame - self.last_attack_frame
            min_cooldown = 4800  # 80s minimum between attacks
            max_wait = 9000  # 150s forced attack
            if time_since_attack >= min_cooldown:
                if time_since_attack >= max_wait:
                    self.state = self.ATTACK
                elif time_since_attack >= S.AI_ATTACK_INTERVAL:
                    # Adaptive: only attack if military strength is sufficient
                    ai_strength = self._get_military_strength(rts_ctx, "lizard")
                    player_strength = self._get_military_strength(rts_ctx, "human")
                    if ai_strength >= player_strength * 0.8 or player_strength == 0:
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

    def _update_ai_fog(self, rts_ctx):
        """Reveal tiles around all AI units and buildings."""
        for unit in rts_ctx.enemy_units:
            self.memory.reveal(unit.tile_x, unit.tile_y, unit.vision)
        for building in rts_ctx.enemy_buildings:
            cx, cy = building.center_tile()
            self.memory.reveal(cx, cy, building.vision)

    def _get_military_strength(self, rts_ctx, faction):
        """Count military strength: combat units + turrets × 2.

        For the human faction, only counts what the AI can currently see.
        """
        if faction == "human":
            # Only count visible player forces
            units = self.memory.get_visible_player_units(rts_ctx)
            buildings = self.memory.get_visible_player_buildings(rts_ctx)
            turret_types = ("turret",)
        else:
            units = rts_ctx.enemy_units
            buildings = rts_ctx.enemy_buildings
            turret_types = ("spine",)
        strength = sum(1 for u in units if u.attack_power > 0)
        strength += sum(
            2
            for b in buildings
            if b.building_type in turret_types and not b.under_construction
        )
        return strength

    def _produce(self, rts_ctx):
        if self.frame - self.last_produce_frame < S.AI_PRODUCE_INTERVAL:
            return

        # Count current drones and assess military balance
        drone_count = sum(1 for u in rts_ctx.enemy_units if u.unit_type == "drone")
        ai_military = self._get_military_strength(rts_ctx, "lizard")
        player_military = self._get_military_strength(rts_ctx, "human")
        need_military = ai_military < player_military

        for building in rts_ctx.enemy_buildings:
            if building.under_construction or not building.produces:
                continue
            if len(building.production_queue) >= 2:
                continue

            # Decide what to produce
            if building.building_type == "hive":
                # Prioritize drones if below target, unless outgunned
                if drone_count < self.desired_drones and not need_military:
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
        # During defense, don't send drones out — recall idle ones to base
        if self.state == self.DEFEND:
            self._recall_drones(rts_ctx)
            return

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

    def _recall_drones(self, rts_ctx):
        """Recall idle drones to base during defense — stop sending them out."""
        occupied = self._get_occupied(rts_ctx)
        hive = self._get_hive(rts_ctx)
        if not hive:
            return
        hx, hy = hive.center_tile()
        for unit in rts_ctx.enemy_units:
            if unit.unit_type != "drone":
                continue
            # If drone is far from base and idle, send it home
            d = unit.distance_to_tile(hx, hy)
            if d > 10 and not unit.returning and not unit.moving:
                unit.harvesting = False
                unit.harvest_target = None
                from .units import _send_to_base

                _send_to_base(unit, rts_ctx, occupied)

    def _supply_drop(self, rts_ctx):
        """Periodic starship supply drop — scales down over time."""
        # Each subsequent drop takes 600 frames longer
        interval = S.AI_SUPPLY_DROP_INTERVAL + self.supply_drop_count * 600
        if self.frame - self.last_supply_drop < interval:
            return
        self.last_supply_drop = self.frame
        self.supply_drop_count += 1

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
        """Send scouts to explore unscouted sectors. React to spotted enemies."""
        occupied = self._get_occupied(rts_ctx)

        for unit in rts_ctx.enemy_units:
            if unit.attack_power <= 0:
                continue

            # Check if this unit can see player entities (within own vision)
            nearest_enemy = None
            nearest_dist = float("inf")
            visible_units = self.memory.get_visible_player_units(rts_ctx)
            visible_buildings = self.memory.get_visible_player_buildings(rts_ctx)
            for pu in visible_units:
                d = unit.distance_to_tile(pu.tile_x, pu.tile_y)
                if d <= unit.vision + 1 and d < nearest_dist:
                    nearest_dist = d
                    nearest_enemy = pu
            for pb in visible_buildings:
                cx, cy = pb.center_tile()
                d = unit.distance_to_tile(cx, cy)
                if d <= unit.vision + 1 and d < nearest_dist:
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
                    for u in visible_units
                    if u.attack_power > 0
                    and unit.distance_to_tile(u.tile_x, u.tile_y) <= 10
                )

                # Smarter engagement: need 1.5× advantage, or target is non-combat
                target_is_harmless = (
                    hasattr(nearest_enemy, "attack_power")
                    and nearest_enemy.attack_power == 0
                    and enemy_nearby <= 1
                )
                if (
                    friendly_nearby >= enemy_nearby * 1.5
                    or enemy_nearby == 0
                    or target_is_harmless
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

            # No enemies spotted — send idle scouts to unscouted sectors
            if (
                self.frame % S.AI_SCOUT_INTERVAL == 0
                and unit.unit_type == "scout"
                and not unit.moving
                and unit.attack_target is None
            ):
                unscouted = self.memory.get_unscouted_sectors()
                if unscouted:
                    # Bias toward sectors far from hive (more likely player base)
                    hive = self._get_hive(rts_ctx)
                    if hive:
                        hcx, hcy = hive.center_tile()
                        unscouted.sort(
                            key=lambda s: -(abs(s[0] - hcx) + abs(s[1] - hcy))
                        )
                    # Pick from top candidates with some randomness
                    pick = unscouted[random.randint(0, min(3, len(unscouted) - 1))]
                    tx, ty = pick
                else:
                    # All sectors explored — random patrol
                    tx = random.randint(0, rts_ctx.tile_map.width - 1)
                    ty = random.randint(0, rts_ctx.tile_map.height - 1)
                if rts_ctx.tile_map.is_passable(tx, ty):
                    path = find_path(
                        rts_ctx.tile_map,
                        (unit.tile_x, unit.tile_y),
                        (tx, ty),
                        occupied,
                    )
                    if path:
                        unit.set_move_target(path)

    def _do_attack(self, rts_ctx):
        """Group military units and send toward player base."""
        target = self._find_player_base(rts_ctx)
        if target is None:
            # No known target — switch to scout to find the player
            self.state = self.SCOUT
            return

        tx, ty = target
        occupied = self._get_occupied(rts_ctx)
        # Only target visible enemies for direct engagement
        visible = self.memory.get_visible_enemies(rts_ctx)

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
                # Assign nearest visible enemy as attack target
                best = None
                best_dist = float("inf")
                for e in visible:
                    if hasattr(e, "center_tile"):
                        ex, ey = e.center_tile()
                    else:
                        ex, ey = e.tile_x, e.tile_y
                    d = unit.distance_to_tile(ex, ey)
                    if d < best_dist:
                        best_dist = d
                        best = e
                if best:
                    unit.attack_target = best

    def _retarget_idle(self, rts_ctx):
        """Give idle military units near visible enemies a new attack target."""
        extra_range = 10 if self.state == self.ATTACK else 0
        visible = self.memory.get_visible_enemies(rts_ctx)
        if not visible:
            return

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
            for e in visible:
                if hasattr(e, "center_tile"):
                    ex, ey = e.center_tile()
                else:
                    ex, ey = e.tile_x, e.tile_y
                d = unit.distance_to_tile(ex, ey)
                if d <= search_range and d < best_dist:
                    best_dist = d
                    best = e
            if best:
                unit.attack_target = best
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
        """Find location of threat: own building/unit recently hit, or visible enemy near base."""
        for b in rts_ctx.enemy_buildings:
            if b.last_hit_frame is not None and b.last_hit_frame < 120:
                return b.center_tile()
        for u in rts_ctx.enemy_units:
            if u.last_hit_frame is not None and u.last_hit_frame < 120:
                return (u.tile_x, u.tile_y)
        # Check for visible player units near AI buildings
        visible = self.memory.get_visible_enemies(rts_ctx)
        for b in rts_ctx.enemy_buildings:
            cx, cy = b.center_tile()
            for pu in visible:
                if hasattr(pu, "tile_x"):
                    px, py = pu.tile_x, pu.tile_y
                else:
                    px, py = pu.center_tile()
                if abs(px - cx) + abs(py - cy) < 8:
                    return (px, py)
        return None

    def _do_defend(self, rts_ctx):
        """Send military units to defend the threatened location."""
        if not self.defend_target:
            return

        tx, ty = self.defend_target
        occupied = self._get_occupied(rts_ctx)
        visible = self.memory.get_visible_enemies(rts_ctx)

        for unit in rts_ctx.enemy_units:
            if unit.attack_power <= 0:
                continue
            if unit.attack_target is not None and unit.attack_target.alive():
                continue

            # Find closest visible player entity
            best = None
            best_dist = float("inf")
            for e in visible:
                if hasattr(e, "center_tile"):
                    ex, ey = e.center_tile()
                else:
                    ex, ey = e.tile_x, e.tile_y
                d = unit.distance_to_tile(ex, ey)
                if d < best_dist:
                    best_dist = d
                    best = e

            if best and best_dist <= unit.vision + 6:
                # Engage any visible enemy within extended vision range
                unit.attack_target = best
                if not unit.path:
                    if hasattr(best, "center_tile"):
                        bx, by = best.center_tile()
                    else:
                        bx, by = best.tile_x, best.tile_y
                    path = find_path(
                        rts_ctx.tile_map,
                        (unit.tile_x, unit.tile_y),
                        (bx, by),
                        occupied,
                    )
                    if path:
                        unit.set_move_target(path)
                        unit.attack_target = best
            elif not unit.moving:
                # No nearby visible enemy — path toward the threat location
                path = find_path(
                    rts_ctx.tile_map, (unit.tile_x, unit.tile_y), (tx, ty), occupied
                )
                if path:
                    unit.set_move_target(path)

    def _find_player_base(self, rts_ctx):
        """Find player base using AI memory — no omniscience."""
        # Check if we can currently see the base
        for b in rts_ctx.player_buildings:
            if b.building_type == "main_base":
                cx, cy = b.center_tile()
                if self.memory.is_visible(cx, cy):
                    self.memory.last_known_base = (cx, cy)
                    return (cx, cy)
        # Use last known base location
        if self.memory.last_known_base:
            return self.memory.last_known_base
        # Use most recent sighting of any player entity
        return self.memory.get_most_recent_sighting()

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
