"""Draw map, entities, HUD, fog overlay, selection box."""

import pygame
from .rts_settings import RTSSettings as S


def draw_frame(screen, rts_ctx, state, fog, minimap_renderer):
    """Draw one complete RTS frame."""
    screen_w = rts_ctx.screen_w
    screen_h = rts_ctx.screen_h
    viewport_h = screen_h - S.HUD_HEIGHT

    # Clear
    screen.fill((0, 0, 0))

    # Draw terrain
    _draw_terrain(screen, rts_ctx.tile_map, rts_ctx.camera, fog)

    # Draw buildings (sorted by y for overlap)
    _draw_buildings(screen, rts_ctx, rts_ctx.camera, fog)

    # Draw units
    _draw_units(screen, rts_ctx, rts_ctx.camera, fog)

    # Draw projectiles
    _draw_projectiles(screen, rts_ctx, rts_ctx.camera)

    # Fog overlay
    fog.draw_overlay(screen, rts_ctx.camera)

    # Build preview
    if state.build_mode and state.build_preview_pos:
        _draw_build_preview(screen, state, rts_ctx.camera)

    # Selection box
    if state.box_selecting and state.box_start and state.box_end:
        _draw_selection_box(screen, state)

    # Clip viewport (prevent drawing into HUD)
    pygame.draw.rect(screen, (30, 30, 40), (0, viewport_h, screen_w, S.HUD_HEIGHT))

    # HUD
    _draw_hud(
        screen, rts_ctx, state, fog, minimap_renderer, screen_w, screen_h, viewport_h
    )

    # Hover tooltip (drawn last, on top of everything)
    _draw_tooltip(screen, rts_ctx, fog, viewport_h)

    pygame.display.flip()


def _draw_terrain(screen, tile_map, camera, fog):
    """Draw visible terrain tiles."""
    ts = S.TILE_SIZE
    start_tx = max(0, int(camera.x // ts))
    start_ty = max(0, int(camera.y // ts))
    end_tx = min(tile_map.width, int((camera.x + camera.screen_w) // ts) + 1)
    end_ty = min(tile_map.height, int((camera.y + camera.viewport_h) // ts) + 1)

    for ty in range(start_ty, end_ty):
        for tx in range(start_tx, end_tx):
            sx, sy = camera.world_to_screen(tx * ts, ty * ts)
            terrain = tile_map.tiles[ty][tx]
            color = S.TERRAIN_COLORS.get(terrain, (60, 120, 40))

            # Slight variation for visual interest
            variation = ((tx * 7 + ty * 13) % 5) - 2
            color = tuple(max(0, min(255, c + variation * 3)) for c in color)

            pygame.draw.rect(screen, color, (sx, sy, ts, ts))

            # Draw rock/mountain detail
            if terrain == S.ROCK:
                _draw_rock_tile(screen, sx, sy, ts, tx, ty)
            elif terrain == S.RUINS:
                _draw_ruins_tile(screen, sx, sy, ts, tx, ty)

            # Draw crystal sparkle
            if terrain == S.CRYSTAL and tile_map.crystal[ty][tx] > 0:
                cx = sx + ts // 2
                cy = sy + ts // 2
                pygame.draw.circle(screen, (200, 240, 255), (cx, cy), 3)

            # Draw isotope sparkle (green/white)
            if terrain == S.ISOTOPE and tile_map.isotope[ty][tx] > 0:
                cx = sx + ts // 2
                cy = sy + ts // 2
                pygame.draw.circle(screen, (200, 255, 210), (cx, cy), 3)

            # Grid lines
            pygame.draw.rect(screen, (0, 0, 0, 30), (sx, sy, ts, ts), 1)


def _draw_buildings(screen, rts_ctx, camera, fog):
    """Draw all buildings."""
    all_buildings = list(rts_ctx.player_buildings) + list(rts_ctx.enemy_buildings)
    all_buildings.sort(key=lambda b: b.py)

    for b in all_buildings:
        # Skip if not visible in fog
        cx, cy = b.center_tile()
        if b.faction == "lizard" and not fog.is_visible(cx, cy):
            continue

        sx, sy = camera.world_to_screen(b.px, b.py)
        pw = b.size[0] * S.TILE_SIZE
        ph = b.size[1] * S.TILE_SIZE

        if not camera.is_visible(b.px, b.py, pw, ph):
            continue

        screen.blit(b.image, (sx, sy))

        # Construction progress bar
        if b.under_construction:
            bar_w = pw
            bar_h = 4
            progress = b.build_progress / b.build_time
            pygame.draw.rect(screen, (60, 60, 60), (sx, sy - 6, bar_w, bar_h))
            pygame.draw.rect(
                screen, (0, 200, 100), (sx, sy - 6, int(bar_w * progress), bar_h)
            )

        # HP bar
        if b.hp < b.max_hp:
            _draw_hp_bar(screen, sx, sy - 8, pw, b.hp, b.max_hp)

        # Selection highlight
        if b.selected:
            pygame.draw.rect(
                screen, S.SELECTION_COLOR, (sx - 1, sy - 1, pw + 2, ph + 2), 2
            )

        # Production progress
        if b.production_queue:
            bar_w = pw
            bar_h = 3
            progress = 1.0 - (b.production_timer / S.PRODUCTION_TIME)
            pygame.draw.rect(screen, (40, 40, 80), (sx, sy + ph + 2, bar_w, bar_h))
            pygame.draw.rect(
                screen, (100, 100, 255), (sx, sy + ph + 2, int(bar_w * progress), bar_h)
            )


def _draw_units(screen, rts_ctx, camera, fog):
    """Draw all units."""
    all_units = list(rts_ctx.player_units) + list(rts_ctx.enemy_units)
    all_units.sort(key=lambda u: u.py)

    for unit in all_units:
        # Skip enemies not in visible fog
        if unit.faction == "lizard" and not fog.is_visible(unit.tile_x, unit.tile_y):
            continue

        sx, sy = camera.world_to_screen(
            unit.px - unit.image.get_width() // 2,
            unit.py - unit.image.get_height() // 2,
        )

        if not camera.is_visible(
            unit.px - unit.image.get_width() // 2,
            unit.py - unit.image.get_height() // 2,
            unit.image.get_width(),
            unit.image.get_height(),
        ):
            continue

        screen.blit(unit.image, (sx, sy))

        # Selection circle
        if unit.selected:
            center_sx, center_sy = camera.world_to_screen(unit.px, unit.py)
            pygame.draw.circle(screen, S.SELECTION_COLOR, (center_sx, center_sy), 12, 1)

        # HP bar (only if damaged)
        if unit.hp < unit.max_hp:
            bar_sx = sx
            bar_sy = sy - 4
            _draw_hp_bar(
                screen, bar_sx, bar_sy, unit.image.get_width(), unit.hp, unit.max_hp
            )

        # Carrying indicator for miners
        if unit.can_harvest and unit.carrying > 0:
            center_sx, center_sy = camera.world_to_screen(unit.px, unit.py)
            pygame.draw.circle(screen, (80, 200, 220), (center_sx, center_sy - 12), 3)
            carry_font = pygame.font.SysFont("consolas", 10)
            carry_text = carry_font.render(str(unit.carrying), True, (200, 240, 255))
            screen.blit(
                carry_text,
                (center_sx + 5, center_sy - 16),
            )

        # Carrying isotope indicator (green dot)
        if unit.can_harvest and unit.carrying_isotope > 0:
            center_sx, center_sy = camera.world_to_screen(unit.px, unit.py)
            pygame.draw.circle(screen, (50, 220, 80), (center_sx, center_sy - 12), 3)
            carry_font = pygame.font.SysFont("consolas", 10)
            carry_text = carry_font.render(
                str(unit.carrying_isotope), True, (150, 255, 150)
            )
            screen.blit(
                carry_text,
                (center_sx + 5, center_sy - 16),
            )

        # Mining progress bar
        if unit.can_harvest and unit.harvesting and not unit.path:
            bar_w = unit.image.get_width()
            bar_h = 3
            bar_sx = sx
            bar_sy = sy - 8
            progress = unit.harvest_timer / unit.harvest_cooldown_max
            bar_color = (0, 200, 220)
            if unit.harvest_resource_type == "isotope":
                bar_color = (50, 220, 80)
            pygame.draw.rect(screen, (40, 40, 40), (bar_sx, bar_sy, bar_w, bar_h))
            pygame.draw.rect(
                screen, bar_color, (bar_sx, bar_sy, int(bar_w * progress), bar_h)
            )


def _draw_hp_bar(screen, x, y, width, hp, max_hp):
    """Draw a small HP bar."""
    bar_h = 3
    ratio = hp / max_hp
    if ratio > 0.6:
        color = (0, 200, 0)
    elif ratio > 0.3:
        color = (200, 200, 0)
    else:
        color = (200, 0, 0)
    pygame.draw.rect(screen, (40, 40, 40), (x, y, width, bar_h))
    pygame.draw.rect(screen, color, (x, y, int(width * ratio), bar_h))


def _draw_projectiles(screen, rts_ctx, camera):
    """Draw all active projectiles."""
    for proj in rts_ctx.projectiles:
        sx, sy = camera.world_to_screen(proj.px, proj.py)
        pygame.draw.circle(screen, proj.color, (int(sx), int(sy)), proj.size)
        # Draw a small trail
        trail_color = tuple(max(0, c - 80) for c in proj.color)
        pygame.draw.circle(
            screen, trail_color, (int(sx) - 1, int(sy) - 1), max(1, proj.size - 1)
        )


def _draw_rock_tile(screen, sx, sy, ts, tx, ty):
    """Draw a mountain/rock tile with 3D shading and cracks."""
    seed = tx * 31 + ty * 17
    highlight = (130, 125, 115)
    shadow = (70, 65, 55)
    crack = (55, 50, 42)
    pygame.draw.line(screen, highlight, (sx + 2, sy + 1), (sx + ts - 3, sy + 1))
    pygame.draw.line(screen, highlight, (sx + 1, sy + 2), (sx + 1, sy + ts // 2))
    pygame.draw.line(screen, shadow, (sx + 3, sy + ts - 2), (sx + ts - 2, sy + ts - 2))
    pygame.draw.line(
        screen, shadow, (sx + ts - 2, sy + ts // 2), (sx + ts - 2, sy + ts - 2)
    )
    cx1 = sx + 6 + (seed % 11)
    cy1 = sy + 5 + (seed % 7)
    cx2 = cx1 + 4 + (seed % 8)
    cy2 = cy1 + 6 + (seed % 6)
    pygame.draw.line(screen, crack, (cx1, cy1), (cx2, cy2))
    cx3 = sx + 4 + ((seed * 3) % 13)
    cy3 = sy + 12 + ((seed * 3) % 9)
    cx4 = cx3 + 5
    cy4 = cy3 + 3
    pygame.draw.line(screen, crack, (cx3, cy3), (cx4, cy4))
    rx = sx + 8 + (seed % 10)
    ry = sy + 4 + ((seed * 7) % 12)
    pygame.draw.circle(screen, highlight, (rx, ry), 2)
    rx2 = sx + 4 + ((seed * 5) % 14)
    ry2 = sy + 14 + ((seed * 11) % 10)
    pygame.draw.circle(screen, highlight, (rx2, ry2), 1)


def _draw_ruins_tile(screen, sx, sy, ts, tx, ty):
    """Draw rubble/ruins on a destroyed building tile."""
    seed = tx * 23 + ty * 37
    for i in range(5):
        rx = sx + ((seed + i * 17) % (ts - 8)) + 2
        ry = sy + ((seed + i * 11) % (ts - 6)) + 2
        rw = 4 + (seed + i * 7) % 5
        rh = 3 + (seed + i * 3) % 4
        shade = 55 + ((seed + i * 13) % 30)
        pygame.draw.rect(screen, (shade, shade - 5, shade - 10), (rx, ry, rw, rh))
    pygame.draw.line(
        screen,
        (35, 30, 25),
        (sx + 4 + seed % 8, sy + 6 + seed % 10),
        (sx + 18 + seed % 10, sy + 20 + seed % 8),
    )


def _draw_build_preview(screen, state, camera):
    """Draw ghost of building to place."""
    from .entity_registry import BUILDING_DEFS

    tx, ty = state.build_preview_pos
    bdef = BUILDING_DEFS[state.build_mode]
    w, h = bdef["size"]
    sx, sy = camera.world_to_screen(tx * S.TILE_SIZE, ty * S.TILE_SIZE)
    pw = w * S.TILE_SIZE
    ph = h * S.TILE_SIZE

    color = (0, 255, 0, 80) if state.build_valid else (255, 0, 0, 80)
    ghost = pygame.Surface((pw, ph), pygame.SRCALPHA)
    ghost.fill(color)
    screen.blit(ghost, (sx, sy))
    border_color = (0, 255, 0) if state.build_valid else (255, 0, 0)
    pygame.draw.rect(screen, border_color, (sx, sy, pw, ph), 2)


def _draw_selection_box(screen, state):
    """Draw the drag-selection rectangle."""
    sx, sy = state.box_start
    ex, ey = state.box_end
    rect = pygame.Rect(min(sx, ex), min(sy, ey), abs(ex - sx), abs(ey - sy))
    pygame.draw.rect(screen, (0, 255, 0), rect, 1)


def _draw_hud(
    screen, rts_ctx, state, fog, minimap_renderer, screen_w, screen_h, viewport_h
):
    """Draw the bottom HUD panel."""
    hud_y = viewport_h
    font = pygame.font.SysFont("consolas", max(12, int(16 * rts_ctx.font_scale)))
    small_font = pygame.font.SysFont("consolas", max(10, int(12 * rts_ctx.font_scale)))

    # Minimap
    mm_x = 8
    mm_y = hud_y + 8
    minimap_renderer.draw(
        screen, mm_x, mm_y, rts_ctx.tile_map, fog, rts_ctx.camera, rts_ctx
    )

    # Resource display
    info_x = S.MINIMAP_SIZE + 24
    total_crystal_cap = sum(
        b.crystal_capacity for b in rts_ctx.player_buildings if b.crystal_capacity > 0
    )
    total_isotope_cap = sum(
        b.isotope_capacity for b in rts_ctx.player_buildings if b.isotope_capacity > 0
    )

    if total_crystal_cap > 0:
        crystal_text = font.render(
            f"Crystals: {state.crystals}/{total_crystal_cap}", True, (80, 220, 255)
        )
    else:
        crystal_text = font.render(f"Crystals: {state.crystals}", True, (80, 220, 255))
    screen.blit(crystal_text, (info_x, hud_y + 10))

    if total_isotope_cap > 0:
        isotope_text = font.render(
            f"Isotope: {state.isotope}/{total_isotope_cap}", True, (50, 220, 80)
        )
    else:
        isotope_text = font.render(f"Isotope: {state.isotope}", True, (50, 220, 80))
    screen.blit(isotope_text, (info_x, hud_y + 28))

    # Selected info
    if state.selected_units:
        types = {}
        for u in state.selected_units:
            types[u.unit_type] = types.get(u.unit_type, 0) + 1
        info = ", ".join(f"{v}x {k}" for k, v in types.items())
        sel_text = small_font.render(f"Selected: {info}", True, (200, 200, 200))
        screen.blit(sel_text, (info_x, hud_y + 50))

    elif state.selected_building:
        b = state.selected_building
        bname = b.building_type.replace("_", " ").title()
        b_text = font.render(bname, True, (200, 200, 200))
        screen.blit(b_text, (info_x, hud_y + 50))

        hp_text = small_font.render(f"HP: {b.hp}/{b.max_hp}", True, (200, 200, 200))
        screen.blit(hp_text, (info_x, hud_y + 68))

        prod_y = hud_y + 85
        # Mining camp storage
        if b.is_mining_camp:
            camp_text = small_font.render(
                f"Stored: {b.stored_crystals}/{b.crystal_capacity}",
                True,
                (100, 200, 220),
            )
            screen.blit(camp_text, (info_x, prod_y))
            prod_y += 16

        # Isotope camp storage
        if b.is_isotope_camp:
            camp_text = small_font.render(
                f"Stored: {b.stored_isotope}/{b.isotope_capacity}",
                True,
                (50, 220, 80),
            )
            screen.blit(camp_text, (info_x, prod_y))
            prod_y += 16

        if b.produces:
            from .entity_registry import UNIT_DEFS as _UD

            for i, utype in enumerate(b.produces):
                cost = (
                    _UD[utype]["cost"]
                    if utype in _UD
                    else {"crystals": 0, "isotope": 0}
                )
                hotkey = "P" if i == 0 else "O"
                cost_str = f"{cost['crystals']}c"
                if cost["isotope"] > 0:
                    cost_str += f" {cost['isotope']}i"
                prod_text = small_font.render(
                    f"[{hotkey}] {utype} ({cost_str})", True, (180, 180, 200)
                )
                screen.blit(prod_text, (info_x, prod_y + i * 16))

        if b.production_queue:
            q_text = small_font.render(
                f"Queue: {', '.join(b.production_queue)}", True, (150, 150, 200)
            )
            screen.blit(q_text, (info_x, hud_y + 130))

    # Build mode hint
    if state.build_mode:
        hint = font.render(
            f"Building: {state.build_mode} (ESC to cancel)", True, (255, 200, 0)
        )
        screen.blit(hint, (info_x, hud_y + 140))
    else:
        # Show build hints if engineer selected
        has_engineer = any(u.can_build for u in state.selected_units)
        if has_engineer:
            hint = small_font.render(
                "[1] Base  [2] Barracks  [3] Turret  [4] M.Camp  [5] Extractor",
                True,
                (150, 150, 150),
            )
            screen.blit(hint, (info_x, hud_y + 140))

    # Game over / victory overlay
    if state.game_over:
        title_font = pygame.font.SysFont(
            "consolas", max(24, int(48 * rts_ctx.font_scale)), bold=True
        )
        if state.victory:
            text = title_font.render("VICTORY!", True, (0, 255, 100))
        else:
            text = title_font.render("DEFEATED!", True, (255, 60, 60))
        tr = text.get_rect(center=(screen_w // 2, viewport_h // 2))
        screen.blit(text, tr)
        sub = font.render("Press ENTER to continue", True, (200, 200, 200))
        sr = sub.get_rect(center=(screen_w // 2, viewport_h // 2 + 50))
        screen.blit(sub, sr)


_TILE_HINTS = {
    S.GRASS: ("Grass", "Open terrain. Units move freely here.", (120, 180, 100)),
    S.ROCK: ("Rock", "Impassable rock formation.", (160, 150, 130)),
    S.CRYSTAL: (
        "Crystal Deposit",
        "Right-click with a Miner to harvest crystals.",
        (80, 220, 255),
    ),
    S.WATER: ("Water", "Impassable body of water.", (80, 130, 200)),
    S.SAND: ("Sand", "Sandy shore. Units can pass through.", (200, 190, 140)),
    S.RUINS: ("Ruins", "Destroyed structure. Impassable rubble.", (120, 110, 100)),
    S.ISOTOPE: (
        "Isotope Vent",
        "Right-click with a Miner to harvest isotope.",
        (50, 220, 80),
    ),
}


def _get_tooltip_text(rts_ctx, fog, mx, my, viewport_h):
    """Return (title, detail, color) for what's under the cursor, or None."""
    if my >= viewport_h:
        return None

    camera = rts_ctx.camera
    wx, wy = camera.screen_to_world(mx, my)
    tx, ty = camera.screen_to_tile(mx, my)
    tile_map = rts_ctx.tile_map

    if not tile_map.in_bounds(tx, ty):
        return None

    # Don't show tooltips in unexplored fog
    if fog.state[ty][tx] == S.FOG_UNEXPLORED:
        return ("Unexplored", "This area has not been scouted yet.", (100, 100, 100))

    # Check units under cursor (player first, then visible enemies)
    for unit in rts_ctx.player_units:
        if unit.rect.collidepoint(wx, wy):
            name = unit.unit_type.replace("_", " ").title()
            detail = f"HP: {unit.hp}/{unit.max_hp}"
            if unit.can_harvest:
                detail += "  |  Harvester unit"
            elif unit.can_build:
                detail += "  |  Can construct buildings"
            elif unit.attack_power > 0:
                detail += f"  |  ATK: {unit.attack_power}  RNG: {unit.attack_range}"
            return (name, detail, S.SELECTION_COLOR)

    for unit in rts_ctx.enemy_units:
        if fog.is_visible(unit.tile_x, unit.tile_y) and unit.rect.collidepoint(wx, wy):
            name = unit.unit_type.replace("_", " ").title()
            detail = f"HP: {unit.hp}/{unit.max_hp}  |  Enemy"
            return (name, detail, S.ENEMY_COLOR)

    # Check buildings
    for b in rts_ctx.player_buildings:
        if b.rect.collidepoint(wx, wy):
            name = b.building_type.replace("_", " ").title()
            detail = f"HP: {b.hp}/{b.max_hp}"
            if b.produces:
                detail += f"  |  Produces: {', '.join(b.produces)}"
            return (name, detail, S.SELECTION_COLOR)

    for b in rts_ctx.enemy_buildings:
        cx, cy = b.center_tile()
        if fog.is_visible(cx, cy) and b.rect.collidepoint(wx, wy):
            name = b.building_type.replace("_", " ").title()
            detail = f"HP: {b.hp}/{b.max_hp}  |  Enemy"
            return (name, detail, S.ENEMY_COLOR)

    # Tile info
    terrain = tile_map.tiles[ty][tx]
    hint = _TILE_HINTS.get(terrain)
    if hint is None:
        return None

    title, detail, color = hint

    # Add resource amount for crystal/isotope
    if terrain == S.CRYSTAL:
        amt = tile_map.crystal[ty][tx]
        if amt > 0:
            detail = f"{amt} crystals remaining. " + detail
        else:
            detail = "Depleted. " + detail
            color = (100, 100, 100)
    elif terrain == S.ISOTOPE:
        amt = tile_map.isotope[ty][tx]
        if amt > 0:
            detail = f"{amt} isotope remaining. " + detail
        else:
            detail = "Depleted. " + detail
            color = (100, 100, 100)

    return (title, detail, color)


def _draw_tooltip(screen, rts_ctx, fog, viewport_h):
    """Draw a single-line info bar just above the HUD."""
    mx, my = pygame.mouse.get_pos()
    info = _get_tooltip_text(rts_ctx, fog, mx, my, viewport_h)
    if info is None:
        return

    title, detail, color = info
    font = pygame.font.SysFont("consolas", max(10, int(13 * rts_ctx.font_scale)))

    text = f"{title}  —  {detail}"
    text_surf = font.render(text, True, color)

    bar_h = text_surf.get_height() + 6
    bar_y = viewport_h - bar_h
    screen_w = rts_ctx.screen_w

    bg = pygame.Surface((screen_w, bar_h), pygame.SRCALPHA)
    bg.fill((20, 20, 30, 180))
    screen.blit(bg, (0, bar_y))

    screen.blit(text_surf, (8, bar_y + 3))
