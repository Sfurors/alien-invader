import sys
import pygame
from bullet import Bullet
from rocket import Rocket
import fleet as fleet_module
import collision as collision_module
import level as level_module


def fire_bullet(ctx):
    if len(ctx.bullets) < ctx.settings.bullets_allowed:
        ctx.bullets.add(Bullet(ctx.settings, ctx.screen, ctx.ship))
        ctx.sounds["shoot"].play()


def fire_rocket(ctx):
    if ctx.stats.rockets > 0 and not ctx.rockets.sprites():
        ctx.stats.rockets -= 1
        ctx.rockets.add(Rocket(ctx.settings, ctx.screen, ctx.ship))
        ctx.sounds["rocket_fire"].play()


def check_keydown_events(event, ctx):
    if event.key == pygame.K_RIGHT:
        ctx.ship.moving_right = True
    elif event.key == pygame.K_LEFT:
        ctx.ship.moving_left = True
    elif event.key == pygame.K_UP:
        ctx.ship.moving_up = True
    elif event.key == pygame.K_DOWN:
        ctx.ship.moving_down = True
    elif event.key == pygame.K_SPACE:
        fire_bullet(ctx)
    elif event.key == pygame.K_b:
        if ctx.rockets.sprites():
            collision_module.detonate_all_rockets(ctx)
        else:
            fire_rocket(ctx)
    elif event.key == pygame.K_q:
        sys.exit()
    elif event.key == pygame.K_k:
        _cheat_kill_all(ctx)
    elif event.key in (pygame.K_F1, pygame.K_F2, pygame.K_F3, pygame.K_F4):
        _cheat_skip_to_level(ctx, event.key - pygame.K_F1 + 1)
    elif event.key == pygame.K_F5:
        _cheat_skip_to_cutscene(ctx)
    elif event.key == pygame.K_F6:
        _cheat_skip_to_rts(ctx)


def _cheat_kill_all(ctx):
    for alien in list(ctx.aliens.sprites()):
        alien.kill()


def _cheat_skip_to_level(ctx, target_level):
    ctx.aliens.empty()
    ctx.bullets.empty()
    ctx.drops.empty()
    ctx.rockets.empty()
    ctx.boss_group.empty()
    ctx.boss_projectiles.empty()
    ctx.stats.boss_active = False
    ctx.settings.fleet_direction = 1
    ctx.stats.level = target_level
    ctx.stats.level_transition_timer = level_module.TRANSITION_FRAMES

    if target_level <= 3:
        ctx.settings.apply_level(target_level)
        fleet_module.create_fleet(ctx)
    else:
        ctx.stats.boss_active = True
        level_module._spawn_boss(ctx)


def _cheat_skip_to_cutscene(ctx):
    ctx.aliens.empty()
    ctx.bullets.empty()
    ctx.drops.empty()
    ctx.rockets.empty()
    ctx.boss_group.empty()
    ctx.boss_projectiles.empty()
    ctx.stats.boss_active = False
    ctx.stats.game_won = True
    ctx.stats.victory_cutscene_active = True
    ctx.stats.game_active = False

    ctx.ship.center()


def _cheat_skip_to_rts(ctx):
    ctx.aliens.empty()
    ctx.bullets.empty()
    ctx.drops.empty()
    ctx.rockets.empty()
    ctx.boss_group.empty()
    ctx.boss_projectiles.empty()
    ctx.stats.boss_active = False
    ctx.stats.game_won = True
    ctx.stats.victory_cutscene_active = False
    ctx.stats.chapter2_active = True
    ctx.stats.game_active = False
    ctx.ship.center()


def check_keyup_events(event, ctx):
    if event.key == pygame.K_RIGHT:
        ctx.ship.moving_right = False
    elif event.key == pygame.K_LEFT:
        ctx.ship.moving_left = False
    elif event.key == pygame.K_UP:
        ctx.ship.moving_up = False
    elif event.key == pygame.K_DOWN:
        ctx.ship.moving_down = False


def check_events(ctx):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if not ctx.stats.game_active:
                if event.key == pygame.K_RETURN:
                    ctx.stats.reset_stats()
                    ctx.stats.game_active = True
                    ctx.stats.game_started = True
                    ctx.settings.fleet_direction = 1
                    ctx.settings.apply_level(1)
                    ctx.aliens.empty()
                    ctx.bullets.empty()
                    ctx.explosions.empty()
                    ctx.drops.empty()
                    ctx.rockets.empty()
                    ctx.boss_group.empty()
                    ctx.boss_projectiles.empty()
                    fleet_module.create_fleet(ctx)
                    ctx.ship.center()
                elif event.key == pygame.K_q:
                    sys.exit()
            else:
                check_keydown_events(event, ctx)
        elif event.type == pygame.KEYUP:
            check_keyup_events(event, ctx)
