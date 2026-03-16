"""Unit update logic: movement, combat, harvesting."""

import pygame
from .rts_settings import RTSSettings as S
from .pathfinding import find_path
from .projectiles import Projectile
from .rts_sprites import get_sprite_data
from pixel_art import draw_pixel_art


def update_units(rts_ctx, state):
    """Per-frame update for all units."""
    occupied = _get_occupied_tiles(rts_ctx)
    _update_group(rts_ctx.player_units, rts_ctx, state, occupied, "human")
    _update_group(rts_ctx.enemy_units, rts_ctx, state, occupied, "lizard")
    # Prevent units from stacking on top of each other
    all_units = list(rts_ctx.player_units) + list(rts_ctx.enemy_units)
    _separate_units(all_units)


def _get_occupied_tiles(rts_ctx):
    """Get set of tiles occupied by buildings."""
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


def _separate_units(units):
    """Push overlapping units apart so they don't stack."""
    min_dist = S.TILE_SIZE * 0.7  # minimum pixel distance between unit centers
    for i in range(len(units)):
        a = units[i]
        for j in range(i + 1, len(units)):
            b = units[j]
            dx = a.px - b.px
            dy = a.py - b.py
            dist_sq = dx * dx + dy * dy
            if dist_sq < min_dist * min_dist and dist_sq > 0:
                dist = dist_sq**0.5
                overlap = (min_dist - dist) * 0.3
                nx = dx / dist
                ny = dy / dist
                # Don't push units that are actively pathing hard
                if not a.path:
                    a.px += nx * overlap
                    a.py += ny * overlap
                if not b.path:
                    b.px -= nx * overlap
                    b.py -= ny * overlap


def _update_group(group, rts_ctx, state, occupied, faction):
    for unit in list(group):
        unit.update()
        # Tick damage tracker
        if unit.last_hit_frame is not None:
            unit.last_hit_frame += 1

        # Handle harvesting
        if unit.can_harvest and unit.harvesting:
            _handle_harvest(unit, rts_ctx, state, occupied)
        elif unit.can_harvest and unit.returning:
            _handle_return(unit, rts_ctx, state, occupied)

        # Handle combat
        if unit.attack_target is not None:
            _handle_combat(unit, rts_ctx, occupied)


def _handle_harvest(unit, rts_ctx, state, occupied):
    """Miner harvesting logic with timed mining rounds."""
    if unit.harvest_target is None:
        unit.harvesting = False
        return

    tx, ty = unit.harvest_target
    dist = unit.distance_to_tile(tx, ty)

    if dist <= 1.5 and not unit.path:
        # At crystal tile, mine with cooldown
        crystal_left = rts_ctx.tile_map.crystal[ty][tx]
        if crystal_left > 0:
            unit.harvest_timer += 1
            if unit.harvest_timer >= unit.harvest_cooldown_max:
                amount = min(
                    unit.harvest_rate,
                    crystal_left,
                    unit.carry_capacity - unit.carrying,
                )
                rts_ctx.tile_map.crystal[ty][tx] -= amount
                unit.carrying += amount
                unit.harvest_timer = 0
                if rts_ctx.tile_map.crystal[ty][tx] <= 0:
                    rts_ctx.tile_map.tiles[ty][tx] = S.GRASS
                    unit.harvest_target = None
                if unit.carrying >= unit.carry_capacity:
                    unit.harvesting = False
                    unit.returning = True
                    unit.harvest_timer = 0
                    _send_to_base(unit, rts_ctx, occupied)
        else:
            unit.harvesting = False
            unit.harvest_target = None
            unit.harvest_timer = 0
    elif not unit.path:
        # Need to path to crystal
        path = find_path(
            rts_ctx.tile_map, (unit.tile_x, unit.tile_y), (tx, ty), occupied
        )
        if path:
            unit.set_move_target(path)
            unit.harvesting = True
            unit.harvest_target = (tx, ty)


def _handle_return(unit, rts_ctx, state, occupied):
    """Miner returning crystals to base with capacity check."""
    if unit.return_target is None or not unit.return_target.alive():
        _send_to_base(unit, rts_ctx, occupied)
        return

    base = unit.return_target
    bx, by = base.tile_x, base.tile_y
    w, h = base.size
    adjacent = bx - 1 <= unit.tile_x <= bx + w and by - 1 <= unit.tile_y <= by + h

    if adjacent and not unit.path:
        # Deposit crystals — single pool per faction, capped at total base capacity
        if unit.faction == "human":
            pool = state.crystals
            cap = _total_base_capacity(rts_ctx.player_buildings)
            amount = min(unit.carrying, max(0, cap - pool))
            state.crystals += amount
            unit.carrying -= amount
        else:
            if rts_ctx.ai:
                pool = rts_ctx.ai.crystals
                cap = _total_base_capacity(rts_ctx.enemy_buildings)
                amount = min(unit.carrying, max(0, cap - pool))
                rts_ctx.ai.crystals += amount
                unit.carrying -= amount
            else:
                unit.carrying = 0

        if unit.carrying > 0:
            # Storage full — miner waits here holding crystals
            # Will deposit next frame when capacity frees up
            return

        unit.returning = False
        # Go back for more if harvest target still valid
        if unit.harvest_target:
            saved_target = unit.harvest_target
            unit.harvesting = True
            path = find_path(
                rts_ctx.tile_map,
                (unit.tile_x, unit.tile_y),
                saved_target,
                occupied,
            )
            if path:
                unit.set_move_target(path)
                unit.harvesting = True
                unit.harvest_target = saved_target
    elif not unit.path:
        _send_to_base(unit, rts_ctx, occupied)


def _total_base_capacity(buildings):
    """Sum crystal_capacity across all bases in a group."""
    return sum(b.crystal_capacity for b in buildings if b.crystal_capacity > 0)


def _find_adjacent_tile(building, unit, tile_map, occupied):
    """Find the closest passable tile adjacent to a building."""
    bx, by = building.tile_x, building.tile_y
    w, h = building.size
    best = None
    best_dist = float("inf")
    # Check tiles around the building perimeter
    for tx in range(bx - 1, bx + w + 1):
        for ty in range(by - 1, by + h + 1):
            # Skip tiles inside the building
            if bx <= tx < bx + w and by <= ty < by + h:
                continue
            if not tile_map.in_bounds(tx, ty):
                continue
            if not tile_map.is_passable(tx, ty):
                continue
            if occupied and (tx, ty) in occupied:
                continue
            d = unit.distance_to_tile(tx, ty)
            if d < best_dist:
                best_dist = d
                best = (tx, ty)
    return best


def _send_to_base(unit, rts_ctx, occupied):
    """Send miner to nearest base."""
    buildings = (
        rts_ctx.player_buildings if unit.faction == "human" else rts_ctx.enemy_buildings
    )
    nearest = None
    best_dist = float("inf")
    for b in buildings:
        if b.building_type in ("main_base", "hive"):
            cx, cy = b.center_tile()
            d = unit.distance_to_tile(cx, cy)
            if d < best_dist:
                best_dist = d
                nearest = b
    if nearest:
        unit.return_target = nearest
        saved_target = unit.harvest_target
        dest = _find_adjacent_tile(nearest, unit, rts_ctx.tile_map, occupied)
        if dest:
            path = find_path(
                rts_ctx.tile_map, (unit.tile_x, unit.tile_y), dest, occupied
            )
            if path:
                unit.set_move_target(path)
                unit.returning = True
                unit.harvest_target = saved_target


def _handle_combat(unit, rts_ctx, occupied):
    """Unit attacking a target."""
    target = unit.attack_target
    if target is None or not target.alive():
        unit.attack_target = None
        return

    # Calculate distance to target
    if hasattr(target, "tile_x"):
        tx, ty = target.tile_x, target.tile_y
        if hasattr(target, "size"):
            # Building: aim for center
            tx, ty = target.center_tile()
    else:
        unit.attack_target = None
        return

    dist = unit.distance_to_tile(tx, ty)

    if dist <= unit.attack_range + 0.5:
        # In range, attack
        if not unit.path:
            unit.path = []
            unit.moving = False
        if unit.attack_cooldown <= 0:
            if unit.attack_range >= 3:
                # Ranged unit — fire projectile
                if unit.faction == "human":
                    color = (255, 255, 100)  # yellow tracer
                else:
                    color = (100, 220, 50)  # green acid
                proj = Projectile(
                    unit.px,
                    unit.py,
                    target,
                    unit.attack_power,
                    color=color,
                    size=2,
                    faction=unit.faction,
                )
                rts_ctx.projectiles.add(proj)
            else:
                # Melee unit — direct damage
                target.take_damage(unit.attack_power)
                if not target.alive():
                    unit.attack_target = None
            unit.attack_cooldown = S.ATTACK_COOLDOWN
    elif not unit.path:
        # Move toward target
        path = find_path(
            rts_ctx.tile_map, (unit.tile_x, unit.tile_y), (tx, ty), occupied
        )
        if path:
            unit.set_move_target(path)
            unit.attack_target = target  # re-set since set_move_target clears it
