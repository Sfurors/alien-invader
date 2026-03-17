"""RTS mouse/keyboard input handling."""

import sys
import pygame
from .rts_settings import RTSSettings as S
from .entity_base import BaseUnit, BaseBuilding
from .entity_registry import BUILDING_DEFS
from .pathfinding import find_path
from .buildings import can_place_building


# Build mode key bindings: B + number
BUILD_KEYS = {
    pygame.K_1: "main_base",
    pygame.K_2: "barracks",
    pygame.K_3: "turret",
    pygame.K_4: "mining_camp",
    pygame.K_5: "isotope_extractor",
}


def handle_events(rts_ctx, state, fog):
    """Process all pygame events for RTS mode. Returns 'quit' or None."""
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()

        elif event.type == pygame.KEYDOWN:
            result = _handle_keydown(event, rts_ctx, state)
            if result in ("quit", "save", "load", "pause"):
                return result

        elif event.type == pygame.KEYUP:
            _handle_keyup(event, rts_ctx)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            _handle_mouse_down(event, rts_ctx, state, fog)

        elif event.type == pygame.MOUSEBUTTONUP:
            _handle_mouse_up(event, rts_ctx, state, fog)

        elif event.type == pygame.MOUSEMOTION:
            _handle_mouse_motion(event, rts_ctx, state)

    return None


def _handle_keydown(event, rts_ctx, state):
    key = event.key
    if key == pygame.K_q:
        sys.exit()
    elif key == pygame.K_ESCAPE:
        if state.build_mode:
            state.cancel_build()
        else:
            state.paused = True
            return "pause"
    elif key == pygame.K_LEFT:
        rts_ctx.camera.scrolling_left = True
    elif key == pygame.K_RIGHT:
        rts_ctx.camera.scrolling_right = True
    elif key == pygame.K_UP:
        rts_ctx.camera.scrolling_up = True
    elif key == pygame.K_DOWN:
        rts_ctx.camera.scrolling_down = True
    elif key == pygame.K_s:
        from .hud_manager import _do_stop

        _do_stop(state)
    elif key == pygame.K_t:
        from .hud_manager import _do_scout_toggle

        _do_scout_toggle(state)
    elif key == pygame.K_b:
        # Enter build mode — need a subsequent number key
        pass
    elif key in BUILD_KEYS:
        can_build_any = any(u.can_build for u in state.selected_units)
        if can_build_any:
            from .hud_manager import _do_enter_build_mode

            _do_enter_build_mode(BUILD_KEYS[key], state, rts_ctx)
    elif key == pygame.K_F5:
        return "save"
    elif key == pygame.K_F9:
        return "load"
    elif key == pygame.K_F6:
        # Cheat: skip to RTS (already in RTS, ignore)
        pass
    # Production hotkeys: P to produce from selected building
    elif key == pygame.K_p:
        from .hud_manager import _do_produce

        _do_produce(0, state)
    elif key == pygame.K_o:
        from .hud_manager import _do_produce

        _do_produce(1, state)
    elif key == pygame.K_i:
        from .hud_manager import _do_produce

        _do_produce(2, state)
    return None


def _handle_keyup(event, rts_ctx):
    key = event.key
    if key == pygame.K_LEFT:
        rts_ctx.camera.scrolling_left = False
    elif key == pygame.K_RIGHT:
        rts_ctx.camera.scrolling_right = False
    elif key == pygame.K_UP:
        rts_ctx.camera.scrolling_up = False
    elif key == pygame.K_DOWN:
        rts_ctx.camera.scrolling_down = False


def _handle_mouse_down(event, rts_ctx, state, fog):
    mx, my = event.pos
    viewport_h = rts_ctx.screen_h - S.HUD_HEIGHT

    # Minimap click (inside HUD area)
    minimap = rts_ctx.minimap
    if (
        minimap
        and minimap.last_screen_rect
        and minimap.last_screen_rect.collidepoint(mx, my)
    ):
        _handle_minimap_click(event.button, mx, my, minimap, rts_ctx, state)
        return

    # HUD area: route clicks to button panel
    if my >= viewport_h:
        if event.button == 1 and rts_ctx.hud_manager:
            rts_ctx.hud_manager.handle_click(mx, my, state, rts_ctx)
        return

    if event.button == 1:  # Left click
        if state.build_mode:
            _try_place_building(rts_ctx, state, mx, my)
        else:
            # Start box selection or single select
            state.box_selecting = True
            state.box_start = (mx, my)
            state.box_end = (mx, my)

    elif event.button == 3:  # Right click
        state.cancel_build()
        _right_click_command(rts_ctx, state, fog, mx, my)


def _handle_mouse_up(event, rts_ctx, state, fog):
    if event.button == 1 and state.box_selecting:
        mx, my = event.pos
        state.box_end = (mx, my)
        _finish_selection(rts_ctx, state, fog, event)
        state.box_selecting = False
        state.box_start = None
        state.box_end = None


def _handle_mouse_motion(event, rts_ctx, state):
    mx, my = event.pos
    viewport_h = rts_ctx.screen_h - S.HUD_HEIGHT
    if my >= viewport_h and rts_ctx.hud_manager:
        rts_ctx.hud_manager.update_hover(mx, my)
    if state.box_selecting:
        state.box_end = (mx, my)
    if state.build_mode:
        tx, ty = rts_ctx.camera.screen_to_tile(mx, my)
        state.build_preview_pos = (tx, ty)
        bdef = BUILDING_DEFS[state.build_mode]
        state.build_valid = can_place_building(
            rts_ctx.tile_map, tx, ty, bdef["size"], rts_ctx
        )


def _finish_selection(rts_ctx, state, fog, event):
    """Complete a click or box select."""
    sx, sy = state.box_start
    ex, ey = state.box_end

    shift = pygame.key.get_mods() & pygame.KMOD_SHIFT

    # If it's basically a single click (small drag)
    if abs(sx - ex) < 5 and abs(sy - ey) < 5:
        _single_select(rts_ctx, state, sx, sy, shift)
    else:
        _box_select(rts_ctx, state, sx, sy, ex, ey, shift)


def _single_select(rts_ctx, state, sx, sy, shift):
    """Select unit/building under cursor."""
    wx, wy = rts_ctx.camera.screen_to_world(sx, sy)

    if not shift:
        state.clear_selection()

    # Check player units
    for unit in rts_ctx.player_units:
        if unit.rect.collidepoint(wx, wy):
            unit.selected = True
            state.selected_units.append(unit)
            return

    # Check player buildings
    for building in rts_ctx.player_buildings:
        if building.rect.collidepoint(wx, wy):
            building.selected = True
            state.selected_building = building
            return


def _box_select(rts_ctx, state, sx, sy, ex, ey, shift):
    """Select all player units in box."""
    if not shift:
        state.clear_selection()

    # Convert screen coords to world
    wx1, wy1 = rts_ctx.camera.screen_to_world(min(sx, ex), min(sy, ey))
    wx2, wy2 = rts_ctx.camera.screen_to_world(max(sx, ex), max(sy, ey))
    sel_rect = pygame.Rect(wx1, wy1, wx2 - wx1, wy2 - wy1)

    for unit in rts_ctx.player_units:
        if sel_rect.colliderect(unit.rect):
            unit.selected = True
            if unit not in state.selected_units:
                state.selected_units.append(unit)


def _right_click_command(rts_ctx, state, fog, mx, my):
    """Context-sensitive right-click: move, attack, or harvest."""
    if not state.selected_units:
        return

    tx, ty = rts_ctx.camera.screen_to_tile(mx, my)
    if not rts_ctx.tile_map.in_bounds(tx, ty):
        return

    occupied = set()
    for b in rts_ctx.player_buildings:
        for dy in range(b.size[1]):
            for dx in range(b.size[0]):
                occupied.add((b.tile_x + dx, b.tile_y + dy))
    for b in rts_ctx.enemy_buildings:
        for dy in range(b.size[1]):
            for dx in range(b.size[0]):
                occupied.add((b.tile_x + dx, b.tile_y + dy))

    # Check if clicking on enemy
    wx, wy = rts_ctx.camera.screen_to_world(mx, my)
    target_enemy = None
    for enemy in rts_ctx.enemy_units:
        if enemy.rect.collidepoint(wx, wy):
            target_enemy = enemy
            break
    if target_enemy is None:
        for eb in rts_ctx.enemy_buildings:
            if eb.rect.collidepoint(wx, wy):
                target_enemy = eb
                break

    # Check if clicking on crystal (for miners)
    is_crystal = (
        rts_ctx.tile_map.tiles[ty][tx] == S.CRYSTAL
        and rts_ctx.tile_map.crystal[ty][tx] > 0
    )
    is_isotope = (
        rts_ctx.tile_map.tiles[ty][tx] == S.ISOTOPE
        and rts_ctx.tile_map.isotope[ty][tx] > 0
    )

    # Check if clicking on own building (for miner deposit / camp assign)
    target_friendly_building = None
    for fb in rts_ctx.player_buildings:
        if fb.rect.collidepoint(wx, wy):
            target_friendly_building = fb
            break

    from .units import _find_adjacent_tile, _send_to_base

    for unit in state.selected_units:
        if target_enemy and unit.attack_power > 0:
            # Attack command
            unit.attack_target = target_enemy
            path = find_path(
                rts_ctx.tile_map, (unit.tile_x, unit.tile_y), (tx, ty), occupied
            )
            if path:
                unit.set_move_target(path)
                unit.attack_target = target_enemy
        elif (
            target_friendly_building
            and target_friendly_building.under_construction
            and unit.can_build
        ):
            # Send engineer to resume construction
            fb = target_friendly_building
            dest = _find_adjacent_tile(fb, unit, rts_ctx.tile_map, occupied)
            if dest:
                path = find_path(
                    rts_ctx.tile_map, (unit.tile_x, unit.tile_y), dest, occupied
                )
                if path:
                    unit.set_move_target(path)
                    unit.build_target = fb
                    unit.building = True
        elif target_friendly_building and unit.can_harvest:
            fb = target_friendly_building
            if fb.is_mining_camp:
                # Assign miner to mining camp
                unit.assigned_camp = fb
                unit.assigned_isotope_camp = None
                unit.harvest_resource_type = "crystal"
                unit.harvesting = False
                unit.returning = False
                unit.harvest_timer = 0
                dest = _find_adjacent_tile(fb, unit, rts_ctx.tile_map, occupied)
                if dest:
                    path = find_path(
                        rts_ctx.tile_map, (unit.tile_x, unit.tile_y), dest, occupied
                    )
                    if path:
                        unit.set_move_target(path)
            elif fb.is_isotope_camp:
                # Assign miner to isotope camp
                unit.assigned_isotope_camp = fb
                unit.assigned_camp = None
                unit.harvest_resource_type = "isotope"
                unit.harvesting = False
                unit.returning = False
                unit.harvest_timer = 0
                dest = _find_adjacent_tile(fb, unit, rts_ctx.tile_map, occupied)
                if dest:
                    path = find_path(
                        rts_ctx.tile_map, (unit.tile_x, unit.tile_y), dest, occupied
                    )
                    if path:
                        unit.set_move_target(path)
            elif unit.carrying > 0 or unit.carrying_isotope > 0:
                # Deposit at base (partial or full)
                unit.returning = True
                unit.return_target = fb
                dest = _find_adjacent_tile(fb, unit, rts_ctx.tile_map, occupied)
                if dest:
                    path = find_path(
                        rts_ctx.tile_map, (unit.tile_x, unit.tile_y), dest, occupied
                    )
                    if path:
                        saved = unit.harvest_target
                        unit.set_move_target(path)
                        unit.returning = True
                        unit.return_target = fb
                        unit.harvest_target = saved
        elif is_crystal and unit.can_harvest:
            # Harvest crystal command
            unit.harvest_target = (tx, ty)
            unit.harvest_resource_type = "crystal"
            unit.harvesting = True
            unit.returning = False
            unit.harvest_timer = 0
            unit.assigned_camp = None
            unit.assigned_isotope_camp = None
            path = find_path(
                rts_ctx.tile_map, (unit.tile_x, unit.tile_y), (tx, ty), occupied
            )
            if path:
                unit.set_move_target(path)
                unit.harvesting = True
                unit.harvest_target = (tx, ty)
                unit.harvest_resource_type = "crystal"
        elif is_isotope and unit.can_harvest:
            # Harvest isotope command
            unit.harvest_target = (tx, ty)
            unit.harvest_resource_type = "isotope"
            unit.harvesting = True
            unit.returning = False
            unit.harvest_timer = 0
            unit.assigned_camp = None
            unit.assigned_isotope_camp = None
            path = find_path(
                rts_ctx.tile_map, (unit.tile_x, unit.tile_y), (tx, ty), occupied
            )
            if path:
                unit.set_move_target(path)
                unit.harvesting = True
                unit.harvest_target = (tx, ty)
                unit.harvest_resource_type = "isotope"
        else:
            # Move command
            path = find_path(
                rts_ctx.tile_map, (unit.tile_x, unit.tile_y), (tx, ty), occupied
            )
            if path:
                unit.set_move_target(path)


def _handle_minimap_click(button, mx, my, minimap, rts_ctx, state):
    """Handle left/right click on the minimap."""
    world_px, world_py, tx, ty = minimap.minimap_to_world(mx, my)

    if not rts_ctx.tile_map.in_bounds(tx, ty):
        return

    if button == 1:
        # Left-click: jump camera to location
        rts_ctx.camera.center_on(world_px, world_py)

    elif button == 3:
        # Right-click: move selected units to location
        state.cancel_build()
        if not state.selected_units:
            return

        occupied = set()
        for b in rts_ctx.player_buildings:
            for dy in range(b.size[1]):
                for dx in range(b.size[0]):
                    occupied.add((b.tile_x + dx, b.tile_y + dy))
        for b in rts_ctx.enemy_buildings:
            for dy in range(b.size[1]):
                for dx in range(b.size[0]):
                    occupied.add((b.tile_x + dx, b.tile_y + dy))

        for unit in state.selected_units:
            path = find_path(
                rts_ctx.tile_map, (unit.tile_x, unit.tile_y), (tx, ty), occupied
            )
            if path:
                unit.set_move_target(path)


def _try_place_building(rts_ctx, state, mx, my):
    """Attempt to place a building at cursor position."""
    tx, ty = rts_ctx.camera.screen_to_tile(mx, my)
    btype = state.build_mode
    bdef = BUILDING_DEFS[btype]

    if not can_place_building(rts_ctx.tile_map, tx, ty, bdef["size"], rts_ctx):
        return

    cost = bdef["cost"]
    if state.crystals < cost["crystals"] or state.isotope < cost["isotope"]:
        return

    state.crystals -= cost["crystals"]
    state.isotope -= cost["isotope"]
    building = BaseBuilding(btype, tx, ty, "human")
    building.under_construction = True
    building.tile_map = rts_ctx.tile_map
    rts_ctx.player_buildings.add(building)
    rts_ctx.all_entities.add(building)

    # Auto-send selected engineers to build site
    from .units import _find_adjacent_tile

    occupied = set()
    for b in rts_ctx.player_buildings:
        for dy in range(b.size[1]):
            for dx in range(b.size[0]):
                occupied.add((b.tile_x + dx, b.tile_y + dy))
    for b in rts_ctx.enemy_buildings:
        for dy in range(b.size[1]):
            for dx in range(b.size[0]):
                occupied.add((b.tile_x + dx, b.tile_y + dy))

    for unit in state.selected_units:
        if unit.can_build:
            dest = _find_adjacent_tile(building, unit, rts_ctx.tile_map, occupied)
            if dest:
                path = find_path(
                    rts_ctx.tile_map, (unit.tile_x, unit.tile_y), dest, occupied
                )
                if path:
                    unit.set_move_target(path)
                    unit.build_target = building
                    unit.building = True

    # Mark tiles as occupied in map (for pathfinding)
    state.cancel_build()
