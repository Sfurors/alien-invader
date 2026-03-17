"""Unit update logic: movement, combat, harvesting."""

import random
import pygame
from .rts_settings import RTSSettings as S
from .pathfinding import find_path
from .projectiles import Projectile
from .rts_sprites import get_sprite_data
from pixel_art import draw_pixel_art  # noqa: F401


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

        # Handle scout mode (before combat so seppuku takes priority)
        if unit.unit_type == "scout_human" and unit.scout_mode:
            _handle_scout_mode(unit, rts_ctx, state, occupied)

        # Handle building
        if unit.can_build and unit.building:
            _handle_build(unit, rts_ctx, occupied)

        # Handle harvesting
        if unit.can_harvest and unit.harvesting:
            _handle_harvest(unit, rts_ctx, state, occupied)
        elif unit.can_harvest and unit.returning:
            _handle_return(unit, rts_ctx, state, occupied)
        elif unit.can_harvest and unit.assigned_camp and not unit.path:
            # Camp-assigned idle miner: find work
            _handle_camp_idle(unit, rts_ctx, state, occupied)
        elif unit.can_harvest and unit.assigned_isotope_camp and not unit.path:
            # Isotope camp-assigned idle miner: find work
            _handle_isotope_camp_idle(unit, rts_ctx, state, occupied)

        # Handle combat
        if unit.attack_target is not None:
            _handle_combat(unit, rts_ctx, occupied)


def _send_to_camp(unit, rts_ctx, occupied):
    """Send miner to assigned mining camp."""
    camp = unit.assigned_camp
    if not camp or not camp.alive():
        _send_to_base(unit, rts_ctx, occupied)
        return

    unit.return_target = camp
    saved_target = unit.harvest_target
    dest = _find_adjacent_tile(camp, unit, rts_ctx.tile_map, occupied)
    if dest:
        path = find_path(rts_ctx.tile_map, (unit.tile_x, unit.tile_y), dest, occupied)
        if path:
            unit.set_move_target(path)
            unit.returning = True
            unit.harvest_target = saved_target


def _send_to_isotope_camp(unit, rts_ctx, occupied):
    """Send miner to assigned isotope camp."""
    camp = unit.assigned_isotope_camp
    if not camp or not camp.alive():
        _send_to_base(unit, rts_ctx, occupied)
        return

    unit.return_target = camp
    saved_target = unit.harvest_target
    dest = _find_adjacent_tile(camp, unit, rts_ctx.tile_map, occupied)
    if dest:
        path = find_path(rts_ctx.tile_map, (unit.tile_x, unit.tile_y), dest, occupied)
        if path:
            unit.set_move_target(path)
            unit.returning = True
            unit.harvest_target = saved_target


def _start_caravan(unit, rts_ctx, occupied):
    """Transform miner into caravan mode: slower, carries full load."""
    camp = unit.assigned_camp
    if not camp or not camp.alive():
        return
    if camp.stored_crystals <= 0:
        return

    # Transfer crystals from camp to miner (add to any already carried)
    amount = min(camp.crystal_capacity, camp.stored_crystals)
    camp.stored_crystals -= amount
    unit.carrying += amount

    _enter_caravan_mode(unit, rts_ctx, occupied)


def _start_isotope_caravan(unit, rts_ctx, occupied):
    """Transform miner into caravan mode carrying isotope."""
    camp = unit.assigned_isotope_camp
    if not camp or not camp.alive():
        return
    if camp.stored_isotope <= 0:
        return

    amount = min(camp.isotope_capacity, camp.stored_isotope)
    camp.stored_isotope -= amount
    unit.carrying_isotope += amount

    _enter_caravan_mode(unit, rts_ctx, occupied)


def _enter_caravan_mode(unit, rts_ctx, occupied):
    """Common caravan mode setup."""
    unit._normal_speed = unit.speed
    unit._normal_image = unit.image
    unit.caravan_mode = True
    unit.speed = unit._normal_speed * 0.7

    sprite_data = get_sprite_data("cart")
    if sprite_data:
        pmap, palette, ps = sprite_data
        w = len(pmap[0]) * ps
        h = len(pmap) * ps
        cart_img = pygame.Surface((w, h), pygame.SRCALPHA)
        draw_pixel_art(cart_img, pmap, ps, palette)
        unit.image = cart_img
    else:
        unit.image = pygame.Surface((S.TILE_SIZE, S.TILE_SIZE), pygame.SRCALPHA)
        unit.image.fill((100, 50, 50))

    _send_to_base(unit, rts_ctx, occupied)


def _end_caravan(unit):
    """Transform caravan back to normal miner."""
    if unit._normal_speed and unit._normal_image:
        unit.speed = unit._normal_speed
        unit.image = unit._normal_image
    unit.caravan_mode = False


def _handle_camp_idle(unit, rts_ctx, state, occupied):
    """Camp-assigned idle miner: deposit, find work, or start caravan."""
    camp = unit.assigned_camp
    if not camp or not camp.alive():
        unit.assigned_camp = None
        if unit.carrying > 0:
            _send_to_base(unit, rts_ctx, occupied)
        return

    if unit.caravan_mode:
        return

    bx, by = camp.tile_x, camp.tile_y
    w, h = camp.size
    near_camp = bx - 1 <= unit.tile_x <= bx + w and by - 1 <= unit.tile_y <= by + h

    # If carrying crystals, deposit into camp first
    if unit.carrying > 0:
        if near_camp:
            space = camp.crystal_capacity - camp.stored_crystals
            if space > 0:
                amount = min(unit.carrying, space)
                camp.stored_crystals += amount
                unit.carrying -= amount
                if unit.carrying > 0:
                    _send_to_base(unit, rts_ctx, occupied)
                    return
            else:
                _send_to_base(unit, rts_ctx, occupied)
                return
        else:
            _send_to_camp(unit, rts_ctx, occupied)
            return

    # Camp is full — one idle miner starts caravan
    if camp.stored_crystals >= camp.crystal_capacity:
        if near_camp:
            _start_caravan(unit, rts_ctx, occupied)
        else:
            _send_to_camp(unit, rts_ctx, occupied)
        return

    # Find nearest crystal within 10 tiles of camp center
    cx, cy = camp.center_tile()
    best_crystal = None
    best_dist = float("inf")
    for ty in range(max(0, cy - 10), min(rts_ctx.tile_map.height, cy + 11)):
        for tx in range(max(0, cx - 10), min(rts_ctx.tile_map.width, cx + 11)):
            if rts_ctx.tile_map.tiles[ty][tx] == S.CRYSTAL:
                if rts_ctx.tile_map.crystal[ty][tx] > 0:
                    d = unit.distance_to_tile(tx, ty)
                    if d < best_dist:
                        best_dist = d
                        best_crystal = (tx, ty)

    if best_crystal:
        tx, ty = best_crystal
        path = find_path(
            rts_ctx.tile_map, (unit.tile_x, unit.tile_y), (tx, ty), occupied
        )
        if path:
            unit.set_move_target(path)
            unit.harvesting = True
            unit.harvest_target = (tx, ty)
            unit.harvest_resource_type = "crystal"


def _handle_isotope_camp_idle(unit, rts_ctx, state, occupied):
    """Isotope camp-assigned idle miner: deposit, find work, or start caravan."""
    camp = unit.assigned_isotope_camp
    if not camp or not camp.alive():
        unit.assigned_isotope_camp = None
        if unit.carrying_isotope > 0:
            _send_to_base(unit, rts_ctx, occupied)
        return

    if unit.caravan_mode:
        return

    bx, by = camp.tile_x, camp.tile_y
    w, h = camp.size
    near_camp = bx - 1 <= unit.tile_x <= bx + w and by - 1 <= unit.tile_y <= by + h

    # If carrying isotope, deposit into camp first
    if unit.carrying_isotope > 0:
        if near_camp:
            space = camp.isotope_capacity - camp.stored_isotope
            if space > 0:
                amount = min(unit.carrying_isotope, space)
                camp.stored_isotope += amount
                unit.carrying_isotope -= amount
                if unit.carrying_isotope > 0:
                    _send_to_base(unit, rts_ctx, occupied)
                    return
            else:
                _send_to_base(unit, rts_ctx, occupied)
                return
        else:
            _send_to_isotope_camp(unit, rts_ctx, occupied)
            return

    # Camp is full — start isotope caravan
    if camp.stored_isotope >= camp.isotope_capacity:
        if near_camp:
            _start_isotope_caravan(unit, rts_ctx, occupied)
        else:
            _send_to_isotope_camp(unit, rts_ctx, occupied)
        return

    # Find nearest isotope within 10 tiles of camp center
    cx, cy = camp.center_tile()
    best_iso = None
    best_dist = float("inf")
    for ty in range(max(0, cy - 10), min(rts_ctx.tile_map.height, cy + 11)):
        for tx in range(max(0, cx - 10), min(rts_ctx.tile_map.width, cx + 11)):
            if rts_ctx.tile_map.tiles[ty][tx] == S.ISOTOPE:
                if rts_ctx.tile_map.isotope[ty][tx] > 0:
                    d = unit.distance_to_tile(tx, ty)
                    if d < best_dist:
                        best_dist = d
                        best_iso = (tx, ty)

    if best_iso:
        tx, ty = best_iso
        path = find_path(
            rts_ctx.tile_map, (unit.tile_x, unit.tile_y), (tx, ty), occupied
        )
        if path:
            unit.set_move_target(path)
            unit.harvesting = True
            unit.harvest_target = (tx, ty)
            unit.harvest_resource_type = "isotope"


def _handle_scout_mode(unit, rts_ctx, state, occupied):
    """Auto-explore fog and seppuku when spotting enemies."""
    # Seppuku check: if any enemy unit/building within vision range, self-destruct
    enemies = rts_ctx.enemy_units if unit.faction == "human" else rts_ctx.player_units
    enemy_buildings = (
        rts_ctx.enemy_buildings if unit.faction == "human" else rts_ctx.player_buildings
    )
    for e in enemies:
        d = unit.distance_to_tile(e.tile_x, e.tile_y)
        if d <= unit.vision + 1:
            # Seppuku!
            state.minimap_alerts.append((unit.tile_x, unit.tile_y, state.frame))
            unit.kill()
            return
    for eb in enemy_buildings:
        cx, cy = eb.center_tile()
        d = unit.distance_to_tile(cx, cy)
        if d <= unit.vision + 1:
            state.minimap_alerts.append((unit.tile_x, unit.tile_y, state.frame))
            unit.kill()
            return

    # Auto-explore: when idle, pick a random unexplored tile and path to it
    unit.scout_timer += 1
    if unit.path:
        return  # still moving to a target

    if unit.scout_timer < 60:
        return  # throttle re-pathing
    unit.scout_timer = 0

    # Collect unexplored tiles within ~30 tiles
    fog = rts_ctx.fog
    candidates = []
    cx, cy = unit.tile_x, unit.tile_y
    search_range = 30
    for ty in range(
        max(0, cy - search_range), min(rts_ctx.tile_map.height, cy + search_range + 1)
    ):
        for tx in range(
            max(0, cx - search_range),
            min(rts_ctx.tile_map.width, cx + search_range + 1),
        ):
            if fog.state[ty][tx] == S.FOG_UNEXPLORED:
                candidates.append((tx, ty))

    if not candidates:
        return  # everything explored

    # Pick a random target from candidates (sample a few for performance)
    sample = random.sample(candidates, min(10, len(candidates)))
    for target in sample:
        tx, ty = target
        if not rts_ctx.tile_map.is_passable(tx, ty):
            continue
        path = find_path(
            rts_ctx.tile_map, (unit.tile_x, unit.tile_y), (tx, ty), occupied
        )
        if path:
            unit.set_move_target(path)
            unit.scout_mode = True  # re-set since set_move_target clears it
            return


def _handle_build(unit, rts_ctx, occupied):
    """Engineer building logic: walk to site, then construct."""
    target = unit.build_target
    if target is None or not target.alive() or not target.under_construction:
        # Building finished or destroyed — clear state
        unit.build_target = None
        unit.building = False
        return

    # Check adjacency: unit within 1 tile of building edges
    bx, by = target.tile_x, target.tile_y
    w, h = target.size
    adjacent = bx - 1 <= unit.tile_x <= bx + w and by - 1 <= unit.tile_y <= by + h

    if adjacent and not unit.path:
        # Increment build progress
        target.build_progress += 1
        if target.build_progress >= target.build_time:
            target.under_construction = False
            unit.build_target = None
            unit.building = False
    elif not unit.path:
        # Re-path to building
        dest = _find_adjacent_tile(target, unit, rts_ctx.tile_map, occupied)
        if dest:
            path = find_path(
                rts_ctx.tile_map, (unit.tile_x, unit.tile_y), dest, occupied
            )
            if path:
                unit.path = list(path)
                unit.moving = True


def _handle_harvest(unit, rts_ctx, state, occupied):
    """Miner harvesting logic with timed mining rounds — supports crystal and isotope."""
    if unit.harvest_target is None:
        unit.harvesting = False
        return

    tx, ty = unit.harvest_target
    dist = unit.distance_to_tile(tx, ty)

    if dist <= 1.5 and not unit.path:
        # Determine resource type from tile
        tile_type = rts_ctx.tile_map.tiles[ty][tx]
        if tile_type == S.ISOTOPE and rts_ctx.tile_map.isotope[ty][tx] > 0:
            # Isotope harvesting
            unit.harvest_resource_type = "isotope"
            cooldown = S.ISOTOPE_HARVEST_COOLDOWN
            resource_left = rts_ctx.tile_map.isotope[ty][tx]
            carry_cap = unit.isotope_carry_capacity
            current_carry = unit.carrying_isotope
            harvest_rate = unit.isotope_harvest_rate

            unit.harvest_cooldown_max = cooldown
            unit.harvest_timer += 1
            if unit.harvest_timer >= cooldown:
                amount = min(harvest_rate, resource_left, carry_cap - current_carry)
                rts_ctx.tile_map.isotope[ty][tx] -= amount
                unit.carrying_isotope += amount
                unit.harvest_timer = 0
                if rts_ctx.tile_map.isotope[ty][tx] <= 0:
                    rts_ctx.tile_map.tiles[ty][tx] = S.GRASS
                    unit.harvest_target = None
                if unit.carrying_isotope >= carry_cap:
                    unit.harvesting = False
                    unit.returning = True
                    unit.harvest_timer = 0
                    if (
                        unit.assigned_isotope_camp
                        and unit.assigned_isotope_camp.alive()
                    ):
                        _send_to_isotope_camp(unit, rts_ctx, occupied)
                    else:
                        _send_to_base(unit, rts_ctx, occupied)
        elif tile_type == S.CRYSTAL and rts_ctx.tile_map.crystal[ty][tx] > 0:
            # Crystal harvesting (original logic)
            unit.harvest_resource_type = "crystal"
            unit.harvest_cooldown_max = S.HARVEST_COOLDOWN
            crystal_left = rts_ctx.tile_map.crystal[ty][tx]
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
                    if unit.assigned_camp and unit.assigned_camp.alive():
                        _send_to_camp(unit, rts_ctx, occupied)
                    else:
                        _send_to_base(unit, rts_ctx, occupied)
        else:
            unit.harvesting = False
            unit.harvest_target = None
            unit.harvest_timer = 0
    elif not unit.path:
        # Need to path to resource
        path = find_path(
            rts_ctx.tile_map, (unit.tile_x, unit.tile_y), (tx, ty), occupied
        )
        if path:
            unit.set_move_target(path)
            unit.harvesting = True
            unit.harvest_target = (tx, ty)


def _handle_return(unit, rts_ctx, state, occupied):
    """Miner returning resources to base/camp with capacity check."""
    if unit.return_target is None or not unit.return_target.alive():
        # Return target dead, redirect
        if (
            unit.carrying_isotope > 0
            and unit.assigned_isotope_camp
            and unit.assigned_isotope_camp.alive()
            and not unit.caravan_mode
        ):
            _send_to_isotope_camp(unit, rts_ctx, occupied)
        elif (
            unit.carrying > 0
            and unit.assigned_camp
            and unit.assigned_camp.alive()
            and not unit.caravan_mode
        ):
            _send_to_camp(unit, rts_ctx, occupied)
        else:
            _send_to_base(unit, rts_ctx, occupied)
        return

    target = unit.return_target
    tx, ty = target.tile_x, target.tile_y
    w, h = target.size
    adjacent = tx - 1 <= unit.tile_x <= tx + w and ty - 1 <= unit.tile_y <= ty + h

    if adjacent and not unit.path:
        if (
            target.is_isotope_camp
            and not unit.caravan_mode
            and unit.carrying_isotope > 0
        ):
            # Deposit isotope into isotope camp
            space = target.isotope_capacity - target.stored_isotope
            amount = min(unit.carrying_isotope, space)
            target.stored_isotope += amount
            unit.carrying_isotope -= amount

            if unit.carrying_isotope > 0:
                # Camp full with leftover — start caravan to haul everything
                _start_isotope_caravan(unit, rts_ctx, occupied)
                return

            unit.returning = False
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
        elif (
            target.is_isotope_camp
            and not unit.caravan_mode
            and unit.carrying_isotope == 0
        ):
            # Miner arrived at camp empty (e.g. after caravan return trip)
            unit.returning = False
        elif target.is_mining_camp and not unit.caravan_mode and unit.carrying > 0:
            # Deposit crystals into mining camp
            space = target.crystal_capacity - target.stored_crystals
            amount = min(unit.carrying, space)
            target.stored_crystals += amount
            unit.carrying -= amount

            if unit.carrying > 0:
                # Camp full with leftover — start caravan to haul everything
                _start_caravan(unit, rts_ctx, occupied)
                return

            unit.returning = False
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
        elif target.is_mining_camp and not unit.caravan_mode and unit.carrying == 0:
            # Miner arrived at camp empty (e.g. after caravan return trip)
            unit.returning = False
        elif unit.caravan_mode:
            # Caravan arriving at base — deposit and transform back
            if unit.faction == "human":
                if unit.carrying > 0:
                    cap = _total_base_capacity(rts_ctx.player_buildings)
                    amount = min(unit.carrying, max(0, cap - state.crystals))
                    state.crystals += amount
                    unit.carrying -= amount
                if unit.carrying_isotope > 0:
                    cap = _total_isotope_capacity(rts_ctx.player_buildings)
                    amount = min(unit.carrying_isotope, max(0, cap - state.isotope))
                    state.isotope += amount
                    unit.carrying_isotope -= amount
            else:
                if rts_ctx.ai:
                    if unit.carrying > 0:
                        cap = _total_base_capacity(rts_ctx.enemy_buildings)
                        amount = min(unit.carrying, max(0, cap - rts_ctx.ai.crystals))
                        rts_ctx.ai.crystals += amount
                        unit.carrying -= amount
                    if unit.carrying_isotope > 0:
                        cap = _total_isotope_capacity(rts_ctx.enemy_buildings)
                        amount = min(
                            unit.carrying_isotope, max(0, cap - rts_ctx.ai.isotope)
                        )
                        rts_ctx.ai.isotope += amount
                        unit.carrying_isotope -= amount

            # If still carrying resources (base full), wait at base in caravan mode
            if unit.carrying > 0 or unit.carrying_isotope > 0:
                unit.moving = False
                unit.path = []
                return

            _end_caravan(unit)
            unit.returning = False
            # Return to camp
            if unit.assigned_camp and unit.assigned_camp.alive():
                _send_to_camp(unit, rts_ctx, occupied)
            elif unit.assigned_isotope_camp and unit.assigned_isotope_camp.alive():
                _send_to_isotope_camp(unit, rts_ctx, occupied)
        else:
            # Normal base deposit
            if unit.faction == "human":
                if unit.carrying > 0:
                    cap = _total_base_capacity(rts_ctx.player_buildings)
                    amount = min(unit.carrying, max(0, cap - state.crystals))
                    state.crystals += amount
                    unit.carrying -= amount
                if unit.carrying_isotope > 0:
                    cap = _total_isotope_capacity(rts_ctx.player_buildings)
                    amount = min(unit.carrying_isotope, max(0, cap - state.isotope))
                    state.isotope += amount
                    unit.carrying_isotope -= amount
            else:
                if rts_ctx.ai:
                    if unit.carrying > 0:
                        cap = _total_base_capacity(rts_ctx.enemy_buildings)
                        amount = min(unit.carrying, max(0, cap - rts_ctx.ai.crystals))
                        rts_ctx.ai.crystals += amount
                        unit.carrying -= amount
                    if unit.carrying_isotope > 0:
                        cap = _total_isotope_capacity(rts_ctx.enemy_buildings)
                        amount = min(
                            unit.carrying_isotope, max(0, cap - rts_ctx.ai.isotope)
                        )
                        rts_ctx.ai.isotope += amount
                        unit.carrying_isotope -= amount
                else:
                    unit.carrying = 0
                    unit.carrying_isotope = 0

            if unit.carrying > 0 or unit.carrying_isotope > 0:
                # Storage full — miner waits here
                return

            unit.returning = False
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


def _total_isotope_capacity(buildings):
    """Sum isotope_capacity across all bases in a group."""
    return sum(b.isotope_capacity for b in buildings if b.isotope_capacity > 0)


def _find_adjacent_tile(building, unit, tile_map, occupied):
    """Find the closest passable tile adjacent to a building."""
    bx, by = building.tile_x, building.tile_y
    w, h = building.size
    best = None
    best_dist = float("inf")
    for tx in range(bx - 1, bx + w + 1):
        for ty in range(by - 1, by + h + 1):
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


def _retarget_nearest_enemy(unit, rts_ctx):
    """Find and assign the nearest enemy within vision range."""
    enemies = rts_ctx.player_units if unit.faction == "lizard" else rts_ctx.enemy_units
    enemy_buildings = (
        rts_ctx.player_buildings
        if unit.faction == "lizard"
        else rts_ctx.enemy_buildings
    )
    best = None
    best_dist = float("inf")
    for e in enemies:
        d = unit.distance_to_tile(e.tile_x, e.tile_y)
        if d <= unit.vision + 1 and d < best_dist:
            best_dist = d
            best = e
    for eb in enemy_buildings:
        cx, cy = eb.center_tile()
        d = unit.distance_to_tile(cx, cy)
        if d <= unit.vision + 1 and d < best_dist:
            best_dist = d
            best = eb
    if best:
        unit.attack_target = best


def _handle_combat(unit, rts_ctx, occupied):
    """Unit attacking a target."""
    target = unit.attack_target
    if target is None or not target.alive():
        unit.attack_target = None
        _retarget_nearest_enemy(unit, rts_ctx)
        if unit.attack_target is None:
            return
        target = unit.attack_target

    if hasattr(target, "tile_x"):
        tx, ty = target.tile_x, target.tile_y
        if hasattr(target, "size"):
            tx, ty = target.center_tile()
    else:
        unit.attack_target = None
        return

    dist = unit.distance_to_tile(tx, ty)

    if dist <= unit.attack_range + 0.5:
        if not unit.path:
            unit.path = []
            unit.moving = False
        if unit.attack_cooldown <= 0:
            if unit.attack_range >= 3:
                if unit.faction == "human":
                    color = (255, 255, 100)
                else:
                    color = (100, 220, 50)
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
                target.take_damage(unit.attack_power)
                if not target.alive():
                    unit.attack_target = None
            unit.attack_cooldown = S.ATTACK_COOLDOWN
    elif not unit.path:
        path = find_path(
            rts_ctx.tile_map, (unit.tile_x, unit.tile_y), (tx, ty), occupied
        )
        if path:
            unit.set_move_target(path)
            unit.attack_target = target
