from alien import Alien, ALIEN_WIDTH, ALIEN_HEIGHT
from game_logic import (
    compute_fleet_grid,
    compute_fleet_positions,
    ALIEN_H_MARGIN,
    ALIEN_V_MARGIN,
    FLEET_TOP_MARGIN,
)


def create_fleet(ctx):
    """Populate ctx.aliens with a fresh grid of Alien sprites."""
    screen_rect = ctx.screen.get_rect()
    scale = getattr(ctx.settings, "resolution_scale", 1.0)
    aw = max(12, int(ALIEN_WIDTH * scale))
    ah = max(9, int(ALIEN_HEIGHT * scale))
    h_margin = max(8, int(ALIEN_H_MARGIN * scale))
    v_margin = max(8, int(ALIEN_V_MARGIN * scale))
    top_margin = max(30, int(FLEET_TOP_MARGIN * scale))
    cols, rows = compute_fleet_grid(
        screen_rect.width,
        screen_rect.height,
        aw,
        ah,
        h_margin,
        v_margin,
        top_margin,
    )
    positions = compute_fleet_positions(
        screen_rect.width,
        aw,
        ah,
        cols,
        rows,
        h_margin,
        v_margin,
        top_margin,
    )
    for x, y in positions:
        ctx.aliens.add(Alien(ctx.settings, ctx.screen, x, y))


def change_fleet_direction(ctx):
    """Drop the fleet one step and reverse horizontal direction."""
    for alien in ctx.aliens.sprites():
        alien.rect.y += ctx.settings.fleet_drop_speed
    ctx.settings.fleet_direction *= -1


def update_aliens(ctx):
    """Move all aliens; reverse direction when any alien hits a screen edge."""
    screen_width = ctx.screen.get_rect().width
    for alien in ctx.aliens.sprites():
        if alien.check_edges(screen_width):
            change_fleet_direction(ctx)
            break
    ctx.aliens.update()
