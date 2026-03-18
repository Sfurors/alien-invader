"""Dungeon mode update logic — enemy AI, projectiles, collisions, pickups."""

from .dungeon_settings import DungeonSettings
from . import dungeon_map


def update(ctx):
    """Run one frame of dungeon logic."""
    if not ctx.player.alive:
        return

    ctx.player.update()

    # Update enemies
    for enemy in ctx.enemies:
        enemy.update(ctx)

    # Update projectiles
    _update_projectiles(ctx)

    # Check pickup collisions
    _check_pickups(ctx)

    # Check if player reached exit (only active when all enemies are dead)
    enemies_alive = any(e.alive for e in ctx.enemies)
    ctx.exit_locked = enemies_alive
    if not enemies_alive:
        px, py = int(ctx.player.x), int(ctx.player.y)
        if 0 <= py < len(ctx.grid) and 0 <= px < len(ctx.grid[0]):
            if ctx.grid[py][px] == dungeon_map.EXIT_TILE:
                ctx.floor_complete = True

    # Update fire flash
    if ctx.fire_flash > 0:
        ctx.fire_flash -= 1


def _update_projectiles(ctx):
    """Move all projectiles and check collisions."""
    player = ctx.player
    hit_radius = DungeonSettings.PROJECTILE_RADIUS

    alive = []
    for proj in ctx.projectiles:
        proj.update(ctx.grid)
        if not proj.alive:
            continue

        if proj.owner == "player":
            # Check hit against enemies
            hit = False
            for enemy in ctx.enemies:
                if not enemy.alive:
                    continue
                dx = proj.x - enemy.x
                dy = proj.y - enemy.y
                # XY proximity
                r = hit_radius + enemy.size
                if dx * dx + dy * dy < r * r:
                    # Z check: enemy occupies z 0.0 to ~0.8
                    if 0.0 <= proj.z <= enemy.size * 2:
                        _damage_enemy(ctx, enemy, proj.damage)
                        hit = True
                        break
            if hit:
                continue
        elif proj.owner == "enemy":
            # Check hit against player
            dx = proj.x - player.x
            dy = proj.y - player.y
            r = hit_radius + DungeonSettings.PLAYER_SIZE
            if dx * dx + dy * dy < r * r:
                # Z check: player at z ~0.5 ± 0.4
                if 0.1 <= proj.z <= 0.9:
                    player.take_damage(proj.damage)
                    continue

        alive.append(proj)
    ctx.projectiles = alive


def _damage_enemy(ctx, enemy, damage):
    """Apply damage to an enemy and handle death/loot."""
    player = ctx.player
    enemy.take_damage(damage)
    if not enemy.alive:
        player.score += enemy.points
        player.kills += 1
        if enemy.should_drop_loot():
            loot_type = enemy.get_loot()
            pickup_cfg = DungeonSettings.PICKUP_TYPES.get(loot_type, {})
            ctx.pickups.append(
                {
                    "type": loot_type,
                    "x": enemy.x,
                    "y": enemy.y,
                    "color": pickup_cfg.get("color", (200, 200, 200)),
                }
            )


def _check_pickups(ctx):
    """Check if player is close enough to pick up items."""
    player = ctx.player
    pickup_range = 0.6

    remaining = []
    for p in ctx.pickups:
        dx = player.x - p["x"]
        dy = player.y - p["y"]
        if dx * dx + dy * dy < pickup_range * pickup_range:
            _apply_pickup(ctx, p)
        else:
            remaining.append(p)
    ctx.pickups = remaining


def _apply_pickup(ctx, pickup):
    """Apply a pickup to the player."""
    ptype = pickup["type"]
    cfg = DungeonSettings.PICKUP_TYPES.get(ptype, {})

    if ptype == "health":
        ctx.player.heal(cfg.get("value", 25))
    elif ptype == "ammo":
        ctx.player.give_ammo(cfg.get("value", 10))
    elif "weapon" in cfg:
        ctx.player.give_weapon(cfg["weapon"])

    if "pickup" in ctx.sounds:
        ctx.sounds["pickup"].play()
