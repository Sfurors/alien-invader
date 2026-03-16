"""Per-frame RTS game logic orchestration."""

from .rts_settings import RTSSettings as S
from . import units as units_module
from . import buildings as buildings_module


def update(rts_ctx, state, fog, ai):
    """One frame of RTS game logic."""
    state.frame += 1

    # Camera
    rts_ctx.camera.update()

    # Update fog of war
    fog.reset_visible()
    _update_fog(rts_ctx, fog)

    # Update entities
    units_module.update_units(rts_ctx, state)
    buildings_module.update_buildings(rts_ctx, state)

    # Update projectiles
    rts_ctx.projectiles.update()

    # Auto-engage: units without orders attack nearby enemies
    _auto_engage(rts_ctx)

    # AI
    ai.update(rts_ctx)

    # Check win/lose conditions
    _check_victory(rts_ctx, state)


def _update_fog(rts_ctx, fog):
    """Reveal tiles around player units and buildings."""
    for unit in rts_ctx.player_units:
        fog.reveal(unit.tile_x, unit.tile_y, unit.vision)
    for building in rts_ctx.player_buildings:
        cx, cy = building.center_tile()
        fog.reveal(cx, cy, building.vision)


def _auto_engage(rts_ctx):
    """Units without orders attack nearby enemies."""
    _auto_engage_group(
        rts_ctx.player_units, rts_ctx.enemy_units, rts_ctx.enemy_buildings
    )
    _auto_engage_group(
        rts_ctx.enemy_units, rts_ctx.player_units, rts_ctx.player_buildings
    )


def _auto_engage_group(friendly_units, enemy_units, enemy_buildings):
    for unit in friendly_units:
        if unit.attack_power <= 0:
            continue
        if unit.attack_target is not None and unit.attack_target.alive():
            continue

        # Find nearest enemy in range
        best = None
        best_dist = float("inf")
        for enemy in enemy_units:
            d = unit.distance_to_tile(enemy.tile_x, enemy.tile_y)
            if d <= unit.attack_range + 2 and d < best_dist:
                best = enemy
                best_dist = d
        # Also check enemy buildings
        if not best:
            for eb in enemy_buildings:
                cx, cy = eb.center_tile()
                d = unit.distance_to_tile(cx, cy)
                if d <= unit.attack_range + 2 and d < best_dist:
                    best = eb
                    best_dist = d
        if best:
            unit.attack_target = best


def _check_victory(rts_ctx, state):
    """Check win/lose conditions."""
    if state.game_over:
        return

    # Lose: no player buildings left
    if not rts_ctx.player_buildings:
        state.game_over = True
        state.victory = False
        return

    # Win: no enemy buildings left (specifically the hive)
    has_hive = any(b.building_type == "hive" for b in rts_ctx.enemy_buildings)
    if not has_hive:
        state.game_over = True
        state.victory = True
