"""Dungeon mode update logic — enemy AI, collisions, pickups."""

from .dungeon_settings import DungeonSettings
from . import dungeon_map


def update(ctx):
    """Run one frame of dungeon logic."""
    if not ctx.player.alive:
        return

    ctx.player.update()

    # Update enemies
    for enemy in ctx.enemies:
        enemy.update(ctx.player, ctx.grid)

    # Check pickup collisions
    _check_pickups(ctx)

    # Check if player reached exit
    px, py = int(ctx.player.x), int(ctx.player.y)
    if 0 <= py < len(ctx.grid) and 0 <= px < len(ctx.grid[0]):
        if ctx.grid[py][px] == dungeon_map.EXIT_TILE:
            ctx.floor_complete = True

    # Update fire flash
    if ctx.fire_flash > 0:
        ctx.fire_flash -= 1


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
