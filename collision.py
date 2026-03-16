import random
import pygame
from explosion import Explosion, MAX_RADIUS
from weapon_drop import WeaponDrop


def _scaled_explosion(ctx, center):
    scale = getattr(ctx.settings, "resolution_scale", 1.0)
    return Explosion(ctx.screen, center, max_radius=int(MAX_RADIUS * scale))


def _scaled_rocket_explosion(ctx, center):
    scale = getattr(ctx.settings, "resolution_scale", 1.0)
    return Explosion(ctx.screen, center, total_frames=25, max_radius=int(80 * scale))


def _end_game(ctx):
    ctx.stats.game_active = False
    if not ctx.stats.game_over_sound_played:
        ctx.sounds["game_over"].play()
        ctx.stats.game_over_sound_played = True


def check_bullet_alien_collisions(ctx):
    hits = pygame.sprite.groupcollide(ctx.bullets, ctx.aliens, True, True)
    for _bullet, hit_aliens in hits.items():
        for alien in hit_aliens:
            ctx.stats.score += ctx.settings.alien_points
            ctx.explosions.add(_scaled_explosion(ctx, alien.rect.center))
            if random.random() < ctx.settings.drop_chance:
                ctx.drops.add(WeaponDrop(ctx.settings, ctx.screen, alien.rect.center))
        ctx.sounds["explosion"].play()


def check_drop_ship_collisions(ctx):
    collected = [d for d in ctx.drops.sprites() if ctx.ship.rect.colliderect(d.rect)]
    for drop in collected:
        drop.kill()
        ctx.stats.rockets += 1
    if collected:
        ctx.sounds["pickup"].play()


def _detonate_rocket(ctx, rocket):
    ctx.explosions.add(_scaled_rocket_explosion(ctx, rocket.rect.center))
    exp_center = pygame.math.Vector2(rocket.rect.center)
    for alien in ctx.aliens.sprites():
        if (
            exp_center.distance_to(pygame.math.Vector2(alien.rect.center))
            <= ctx.settings.rocket_radius
        ):
            ctx.stats.score += ctx.settings.alien_points
            alien.kill()
    rocket.kill()
    ctx.sounds["rocket_explosion"].play()


def check_rocket_detonations(ctx):
    for rocket in list(ctx.rockets.sprites()):
        if rocket.rect.top <= rocket.detonate_y:
            _detonate_rocket(ctx, rocket)


def detonate_all_rockets(ctx):
    for rocket in list(ctx.rockets.sprites()):
        _detonate_rocket(ctx, rocket)


def check_asteroid_ship_collision(ctx):
    ship_pos = pygame.math.Vector2(ctx.ship.rect.center)
    for asteroid in ctx.asteroids:
        dist = ship_pos.distance_to(pygame.math.Vector2(asteroid.rect.center))
        if dist < ctx.ship.radius + asteroid.radius:
            ctx.explosions.add(_scaled_explosion(ctx, ctx.ship.rect.center))
            _end_game(ctx)
            return


def check_aliens_ship_collision(ctx):
    """End game if an alien touches the ship or reaches the bottom."""
    if pygame.sprite.spritecollideany(ctx.ship, ctx.aliens):
        _end_game(ctx)
        return
    screen_rect = ctx.screen.get_rect()
    for alien in ctx.aliens.sprites():
        if alien.rect.bottom >= screen_rect.bottom:
            _end_game(ctx)
            return


def check_bullet_boss_collisions(ctx):
    for boss in ctx.boss_group.sprites():
        hits = pygame.sprite.spritecollide(boss, ctx.bullets, True)
        for _bullet in hits:
            ctx.sounds["boss_hit"].play()
            dead = boss.take_damage(1)
            if dead:
                ctx.explosions.add(_scaled_rocket_explosion(ctx, boss.rect.center))
                ctx.stats.score += ctx.settings.boss_points
                boss.kill()
                ctx.boss_projectiles.empty()
                ctx.aliens.empty()
                ctx.stats.boss_active = False
                ctx.stats.game_won = True
                ctx.stats.victory_cutscene_active = True
                ctx.stats.game_active = False
                ctx.sounds["boss_death"].play()
                ctx.sounds["victory"].play()
                return


def check_boss_projectile_ship_collision(ctx):
    if pygame.sprite.spritecollideany(ctx.ship, ctx.boss_projectiles):
        _end_game(ctx)
