import math
import random
from alien import Alien
from boss import Boss
from boss_projectile import BossProjectile
import fleet as fleet_module

TRANSITION_FRAMES = 120  # 2 seconds at 60fps


def advance_level(ctx):
    ctx.stats.level += 1
    ctx.bullets.empty()
    ctx.drops.empty()
    ctx.settings.fleet_direction = 1
    ctx.stats.level_transition_timer = TRANSITION_FRAMES
    ctx.sounds["level_up"].play()

    import save_manager

    save_manager.unlock_next_level(ctx.stats.level)

    if ctx.stats.level <= 3:
        ctx.settings.apply_level(ctx.stats.level)
        fleet_module.create_fleet(ctx)
    else:
        ctx.stats.boss_active = True
        _spawn_boss(ctx)


def _spawn_boss(ctx):
    boss = Boss(ctx.settings, ctx.screen)
    ctx.boss_group.add(boss)


def handle_boss_actions(ctx):
    for boss in ctx.boss_group.sprites():
        if boss.should_shoot:
            boss.should_shoot = False
            _boss_shoot(ctx, boss)
            ctx.sounds["boss_shoot"].play()
        if boss.should_spawn:
            boss.should_spawn = False
            _boss_spawn_helpers(ctx, boss)


def _boss_shoot(ctx, boss):
    s = ctx.settings
    count = s.boss_projectile_count
    spread_rad = math.radians(s.boss_projectile_spread)
    start_angle = math.pi / 2 - spread_rad / 2
    for i in range(count):
        angle = (
            start_angle if count == 1 else start_angle + spread_rad * i / (count - 1)
        )
        dx = math.cos(angle)
        dy = math.sin(angle)
        proj = BossProjectile(
            ctx.screen,
            boss.rect.centerx,
            boss.rect.bottom,
            dx,
            dy,
            s.boss_projectile_speed,
        )
        ctx.boss_projectiles.add(proj)


def _boss_spawn_helpers(ctx, boss):
    s = ctx.settings
    screen_w = ctx.screen.get_rect().width
    for i in range(s.boss_helper_count):
        x = boss.rect.centerx + random.randint(-100, 100)
        x = max(0, min(x, screen_w - 48))
        y = boss.rect.bottom + 10
        ctx.aliens.add(Alien(s, ctx.screen, x, y, drift_y=0.8))
