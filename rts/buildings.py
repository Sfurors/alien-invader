"""Building update logic: construction, production, turret combat."""

from .rts_settings import RTSSettings as S
from .entity_base import BaseUnit
from .entity_registry import UNIT_DEFS
from .projectiles import Projectile


def update_buildings(rts_ctx, state):
    """Per-frame update for all buildings."""
    _update_group(rts_ctx.player_buildings, rts_ctx, state, "human")
    _update_group(rts_ctx.enemy_buildings, rts_ctx, state, "lizard")


def _update_group(group, rts_ctx, state, faction):
    for building in list(group):
        building.update()
        # Tick damage tracker
        if building.last_hit_frame is not None:
            building.last_hit_frame += 1

        # Check production completion
        produced = building.pop_produced()
        if produced:
            _spawn_produced_unit(building, produced, rts_ctx, faction)

        # Turret/spine combat
        if building.attack_power > 0 and not building.under_construction:
            _turret_attack(building, rts_ctx)


def _spawn_produced_unit(building, unit_type, rts_ctx, faction):
    """Spawn a newly produced unit near the building's rally point."""
    rx, ry = building.rally_x, building.rally_y
    # Clamp to map
    rx = max(0, min(rx, rts_ctx.tile_map.width - 1))
    ry = max(0, min(ry, rts_ctx.tile_map.height - 1))
    # Find passable tile near rally
    spawn_x, spawn_y = rx, ry
    if not rts_ctx.tile_map.is_passable(rx, ry):
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                nx, ny = rx + dx, ry + dy
                if rts_ctx.tile_map.is_passable(nx, ny):
                    spawn_x, spawn_y = nx, ny
                    break
            else:
                continue
            break

    unit = BaseUnit(unit_type, spawn_x, spawn_y, faction)
    if faction == "human":
        rts_ctx.player_units.add(unit)
    else:
        rts_ctx.enemy_units.add(unit)
    rts_ctx.all_entities.add(unit)


def _turret_attack(building, rts_ctx):
    """Auto-attack nearest enemy in range."""
    if building.attack_cooldown > 0:
        return

    cx, cy = building.center_tile()
    enemies = (
        rts_ctx.enemy_units if building.faction == "human" else rts_ctx.player_units
    )
    enemy_buildings = (
        rts_ctx.enemy_buildings
        if building.faction == "human"
        else rts_ctx.player_buildings
    )

    best = None
    best_dist = float("inf")

    for enemy in enemies:
        dx = enemy.tile_x - cx
        dy = enemy.tile_y - cy
        dist = (dx * dx + dy * dy) ** 0.5
        if dist <= building.attack_range and dist < best_dist:
            best = enemy
            best_dist = dist

    for eb in enemy_buildings:
        ecx, ecy = eb.center_tile()
        dx = ecx - cx
        dy = ecy - cy
        dist = (dx * dx + dy * dy) ** 0.5
        if dist <= building.attack_range and dist < best_dist:
            best = eb
            best_dist = dist

    if best is not None:
        # Fire projectile from turret center
        bpx = building.px + building.size[0] * S.TILE_SIZE // 2
        bpy = building.py + building.size[1] * S.TILE_SIZE // 2
        color = (255, 200, 50) if building.faction == "human" else (200, 50, 30)
        proj = Projectile(
            bpx,
            bpy,
            best,
            building.attack_power,
            color=color,
            size=3,
            faction=building.faction,
        )
        rts_ctx.projectiles.add(proj)
        building.attack_cooldown = S.ATTACK_COOLDOWN


def can_place_building(tile_map, tx, ty, size, rts_ctx):
    """Check if a building can be placed at (tx, ty) with given size."""
    w, h = size
    for dy in range(h):
        for dx in range(w):
            nx, ny = tx + dx, ty + dy
            if not tile_map.in_bounds(nx, ny):
                return False
            if not tile_map.is_passable(nx, ny):
                return False
            # Check overlap with existing buildings
            for b in rts_ctx.player_buildings:
                if b.occupies_tile(nx, ny):
                    return False
            for b in rts_ctx.enemy_buildings:
                if b.occupies_tile(nx, ny):
                    return False
    return True
