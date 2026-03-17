import argparse
import sys

import pygame
from settings1 import Settings, RESOLUTION_PRESETS
from ship import Ship
from game_stats import GameStats
from sounds import load_sounds
from background import SpaceBackground
from asteroid import Asteroid, ASTEROID_COUNT
from game_context import GameContext
import fleet as fleet_module
import collision as collision_module
import events as events_module
import renderer as renderer_module
import level as level_module
from menu_animation import MenuAnimation
from victory_cutscene import VictoryCutscene
from rts import RTSMode
import save_manager


def run_game():
    parser = argparse.ArgumentParser(description="Alien Invasion")
    parser.add_argument(
        "--size",
        choices=RESOLUTION_PRESETS.keys(),
        default="medium",
        help="Window size preset (default: medium)",
    )
    args = parser.parse_args()

    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    ai_settings = Settings()
    ai_settings.apply_resolution(args.size)

    screen = pygame.display.set_mode(
        (ai_settings.screen_width, ai_settings.screen_height)
    )
    pygame.display.set_caption("Alien Invasion")

    bg = SpaceBackground(screen, num_stars=120)
    asteroids = pygame.sprite.Group()
    for _ in range(ASTEROID_COUNT):
        asteroids.add(Asteroid(ai_settings.screen_width, ai_settings.screen_height))

    sounds = load_sounds()
    stats = GameStats()
    ship = Ship(screen, ai_settings)

    ctx = GameContext(
        settings=ai_settings,
        stats=stats,
        screen=screen,
        sounds=sounds,
        ship=ship,
        bullets=pygame.sprite.Group(),
        aliens=pygame.sprite.Group(),
        explosions=pygame.sprite.Group(),
        asteroids=asteroids,
        rockets=pygame.sprite.Group(),
        drops=pygame.sprite.Group(),
        boss_group=pygame.sprite.Group(),
        boss_projectiles=pygame.sprite.Group(),
        background=bg,
    )

    fs = ai_settings.font_scale
    score_font = pygame.font.SysFont("consolas", max(14, int(28 * fs)))
    hint_font = pygame.font.SysFont("consolas", max(16, int(32 * fs)))
    title_font = pygame.font.SysFont("consolas", max(36, int(72 * fs)), bold=True)
    menu_font = pygame.font.SysFont("consolas", max(16, int(32 * fs)))

    screen_rect = screen.get_rect()
    alien_center_y = screen_rect.centery - 80 - 90
    menu_anim = MenuAnimation(
        ai_settings.screen_width,
        ai_settings.screen_height,
        (screen_rect.centerx, alien_center_y),
    )

    clock = pygame.time.Clock()
    menu_music_playing = False
    current_music = None  # tracks which gameplay music is active
    victory_cutscene = None
    cutscene_sounds_played = False
    rts_mode = None
    progress = save_manager.load_progress()
    events_module.validate_menu_cursor(ctx.stats, progress)

    while True:
        clock.tick(60)

        if not ctx.stats.game_active:
            ctx.background.update()
            ctx.asteroids.update()
            # Stop gameplay music when returning to menu/game-over
            if current_music is not None:
                sounds[current_music].stop()
                current_music = None
                progress = save_manager.load_progress()
                events_module.validate_menu_cursor(ctx.stats, progress)
            if not ctx.stats.game_started:
                if not menu_music_playing:
                    sounds["menu_melody"].play(-1)
                    menu_music_playing = True
                menu_anim.update()
                renderer_module.draw_menu(
                    screen,
                    ai_settings,
                    title_font,
                    menu_font,
                    bg,
                    menu_anim,
                    progress,
                    ctx.stats,
                )
                events_module.check_events(ctx, progress)
            elif ctx.stats.game_won:
                if ctx.stats.victory_cutscene_active:
                    # Create cutscene on first frame
                    if victory_cutscene is None:
                        victory_cutscene = VictoryCutscene(
                            ai_settings.screen_width,
                            ai_settings.screen_height,
                            ai_settings.font_scale,
                        )
                        cutscene_sounds_played = False
                    if not cutscene_sounds_played:
                        sounds["comm_call"].play()
                        cutscene_sounds_played = True
                    victory_cutscene.update()
                    victory_cutscene.draw(screen)
                    # Handle events during cutscene (Q to quit, ENTER to advance)
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            sys.exit()
                        elif event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_q:
                                sys.exit()
                            elif event.key == pygame.K_k:
                                ctx.stats.victory_cutscene_active = False
                                ctx.stats.chapter2_active = True
                                sounds["comm_open"].play()
                            elif event.key == pygame.K_RETURN:
                                if victory_cutscene.finished:
                                    ctx.stats.victory_cutscene_active = False
                                    ctx.stats.chapter2_active = True
                                    sounds["comm_open"].play()
                                else:
                                    victory_cutscene.advance()
                elif ctx.stats.chapter2_active:
                    # RTS Mode — Chapter 2
                    if rts_mode is None:
                        rts_mode = RTSMode(
                            screen,
                            sounds,
                            ai_settings.font_scale,
                            load_save=ctx.stats.rts_load_save,
                        )
                    result = rts_mode.update()
                    if result == "menu":
                        # Return to main menu
                        ctx.stats.chapter2_active = False
                        ctx.stats.game_won = False
                        ctx.stats.game_started = False
                        rts_mode = None
                        progress = save_manager.load_progress()
                        events_module.validate_menu_cursor(ctx.stats, progress)
                    elif result == "done":
                        # Return to victory screen
                        ctx.stats.chapter2_active = False
                        rts_mode = None
                else:
                    renderer_module.draw_victory(
                        screen, ai_settings, ctx.stats, title_font, menu_font, bg
                    )
                    events_module.check_events(ctx, progress)
            else:
                renderer_module.draw_game_over(
                    screen, ai_settings, title_font, menu_font, bg, ctx.stats
                )
                events_module.check_events(ctx, progress)
        else:
            if menu_music_playing:
                sounds["menu_melody"].stop()
                menu_music_playing = False
            if victory_cutscene is not None:
                victory_cutscene = None

            # Switch between level music and boss music
            wanted_music = "boss_music" if ctx.stats.boss_active else "level_music"
            if current_music != wanted_music:
                if current_music is not None:
                    sounds[current_music].stop()
                sounds[wanted_music].play(-1)
                current_music = wanted_music

            if ctx.stats.paused:
                result = events_module.check_pause_events(ctx)
                if result == "menu":
                    progress = save_manager.load_progress()
                    continue
                renderer_module.draw_pause_menu(screen)
                continue

            events_module.check_events(ctx, progress)

            if ctx.stats.level_transition_timer > 0:
                ctx.stats.level_transition_timer -= 1
                ctx.background.update()
                ctx.asteroids.update()
                renderer_module.draw_level_banner(ctx, score_font, title_font)
                continue

            ctx.ship.update()
            ctx.bullets.update()
            collision_module.check_bullet_alien_collisions(ctx)
            ctx.drops.update()
            collision_module.check_drop_ship_collisions(ctx)
            ctx.rockets.update()
            collision_module.check_rocket_detonations(ctx)
            if not ctx.stats.boss_active and not ctx.aliens:
                ctx.bullets.empty()
                level_module.advance_level(ctx)
            fleet_module.update_aliens(ctx)
            collision_module.check_aliens_ship_collision(ctx)
            if ctx.stats.boss_active:
                ctx.boss_group.update()
                level_module.handle_boss_actions(ctx)
                ctx.boss_projectiles.update()
                collision_module.check_bullet_boss_collisions(ctx)
                collision_module.check_boss_projectile_ship_collision(ctx)
            ctx.explosions.update()
            ctx.background.update()
            ctx.asteroids.update()
            collision_module.check_asteroid_ship_collision(ctx)
            renderer_module.update_screen(ctx, score_font, hint_font)


run_game()
