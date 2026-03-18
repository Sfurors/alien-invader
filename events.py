import sys
import pygame
from bullet import Bullet
from rocket import Rocket
import fleet as fleet_module
import collision as collision_module
import level as level_module

# Menu item definitions: (label, action_type, action_value)
MENU_ITEMS = [
    ("Level 1", "start_level", 1),
    ("Level 2", "start_level", 2),
    ("Level 3", "start_level", 3),
    ("Boss Fight", "start_level", 4),
    ("RTS Mode", "rts_menu", None),
    ("Dungeon", "dungeon_menu", None),
]

RTS_SUBMENU_ITEMS = [
    ("New Game", "rts_new"),
    ("Load Save", "rts_load"),
    ("Back", "back"),
]


def fire_bullet(ctx):
    if len(ctx.bullets) < ctx.settings.bullets_allowed:
        ctx.bullets.add(Bullet(ctx.settings, ctx.screen, ctx.ship))
        ctx.sounds["shoot"].play()


def fire_rocket(ctx):
    if ctx.stats.rockets > 0 and not ctx.rockets.sprites():
        ctx.stats.rockets -= 1
        ctx.rockets.add(Rocket(ctx.settings, ctx.screen, ctx.ship))
        ctx.sounds["rocket_fire"].play()


def _start_level(ctx, level):
    """Start (or restart) a starship level."""
    ctx.stats.reset_stats()
    ctx.stats.level = level
    ctx.stats.game_active = True
    ctx.stats.game_started = True
    ctx.settings.fleet_direction = 1

    ctx.aliens.empty()
    ctx.bullets.empty()
    ctx.explosions.empty()
    ctx.drops.empty()
    ctx.rockets.empty()
    ctx.boss_group.empty()
    ctx.boss_projectiles.empty()

    if level <= 3:
        ctx.settings.apply_level(level)
        fleet_module.create_fleet(ctx)
    else:
        ctx.stats.boss_active = True
        level_module._spawn_boss(ctx)

    ctx.stats.level_transition_timer = level_module.TRANSITION_FRAMES
    ctx.ship.center()


def _is_item_unlocked(index, progress):
    """Check whether a menu item at the given index is unlocked."""
    if index < 4:
        return progress.get("max_unlocked_level", 1) >= (index + 1)
    if index == 4:
        return progress.get("rts_unlocked", False)
    if index == 5:
        return progress.get("dungeon_unlocked", False) or progress.get("rts_unlocked", False)
    return False


def _move_cursor(stats, direction, progress):
    """Move menu cursor up or down, skipping locked items."""
    count = len(MENU_ITEMS)
    cursor = stats.menu_cursor
    for _ in range(count):
        cursor = (cursor + direction) % count
        if _is_item_unlocked(cursor, progress):
            stats.menu_cursor = cursor
            return
    # No unlocked items found (shouldn't happen — level 1 is always unlocked)


def _move_rts_cursor(stats, direction, has_save):
    """Move RTS sub-menu cursor, skipping 'Load Save' if no save exists."""
    count = len(RTS_SUBMENU_ITEMS)
    cursor = stats.rts_submenu_cursor
    for _ in range(count):
        cursor = (cursor + direction) % count
        # Skip "Load Save" if no save file
        if RTS_SUBMENU_ITEMS[cursor][1] == "rts_load" and not has_save:
            continue
        stats.rts_submenu_cursor = cursor
        return


def _validate_rts_cursor(stats, has_save):
    """Ensure cursor isn't sitting on a disabled item."""
    action = RTS_SUBMENU_ITEMS[stats.rts_submenu_cursor][1]
    if action == "rts_load" and not has_save:
        stats.rts_submenu_cursor = 0


def _get_dungeon_submenu_items():
    """Build dungeon submenu: New Game, unlocked floor entries, Back."""
    import save_manager

    items = [("New Game", "dungeon_new", 0)]
    for floor in save_manager.get_dungeon_unlocked_floors():
        items.append((f"Floor {floor}", "dungeon_load", floor))
    items.append(("Back", "back", 0))
    return items


def validate_menu_cursor(stats, progress):
    """Clamp menu_cursor to an unlocked item after progress changes."""
    if not _is_item_unlocked(stats.menu_cursor, progress):
        stats.menu_cursor = 0  # Level 1 is always unlocked


def check_keydown_events(event, ctx):
    if event.key == pygame.K_ESCAPE:
        ctx.stats.paused = True
        ctx.ship.moving_right = False
        ctx.ship.moving_left = False
        ctx.ship.moving_up = False
        ctx.ship.moving_down = False
    elif event.key == pygame.K_RIGHT:
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
    elif event.key == pygame.K_F7:
        _cheat_skip_to_dungeon(ctx)


def _cheat_kill_all(ctx):
    for alien in list(ctx.aliens.sprites()):
        alien.kill()


def _cheat_skip_to_level(ctx, target_level):
    _start_level(ctx, target_level)


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


def _cheat_skip_to_dungeon(ctx):
    import save_manager

    ctx.aliens.empty()
    ctx.bullets.empty()
    ctx.drops.empty()
    ctx.rockets.empty()
    ctx.boss_group.empty()
    ctx.boss_projectiles.empty()
    ctx.stats.boss_active = False
    ctx.stats.game_won = True
    ctx.stats.victory_cutscene_active = False
    ctx.stats.chapter2_active = False
    ctx.stats.chapter3_active = True
    ctx.stats.dungeon_load_floor = 0
    ctx.stats.game_active = False
    ctx.ship.center()
    save_manager.unlock_dungeon()


def check_pause_events(ctx):
    """Handle events while Ch1 is paused. Returns 'menu' or None."""
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                ctx.stats.paused = False
            elif event.key == pygame.K_m:
                ctx.stats.paused = False
                ctx.stats.game_active = False
                ctx.stats.game_started = False
                ctx.stats.game_won = False
                ctx.stats.game_over_sound_played = False
                return "menu"
            elif event.key == pygame.K_q:
                sys.exit()
    return None


def check_keyup_events(event, ctx):
    if event.key == pygame.K_RIGHT:
        ctx.ship.moving_right = False
    elif event.key == pygame.K_LEFT:
        ctx.ship.moving_left = False
    elif event.key == pygame.K_UP:
        ctx.ship.moving_up = False
    elif event.key == pygame.K_DOWN:
        ctx.ship.moving_down = False


def check_events(ctx, progress=None):
    """Handle events. `progress` is needed on menu screens for cursor navigation."""
    import save_manager

    if progress is None:
        progress = save_manager.load_progress()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if not ctx.stats.game_active:
                _handle_menu_or_gameover_key(event, ctx, progress)
            else:
                check_keydown_events(event, ctx)
        elif event.type == pygame.KEYUP:
            check_keyup_events(event, ctx)


def _handle_menu_or_gameover_key(event, ctx, progress):
    """Route key events for menu, game-over, victory, and cutscene screens."""
    stats = ctx.stats

    # Main menu (not started yet)
    if not stats.game_started:
        _handle_menu_key(event, ctx, progress)
        return

    # Game over (started but not won, not active)
    if stats.game_started and not stats.game_won:
        if event.key == pygame.K_RETURN:
            # Restart the level the player died on
            _start_level(ctx, stats.level)
        elif event.key == pygame.K_m:
            stats.game_started = False
            stats.game_over_sound_played = False
        elif event.key == pygame.K_q:
            sys.exit()
        return

    # Victory / cutscene / RTS screens — keep existing behavior
    if event.key == pygame.K_q:
        sys.exit()


def _handle_menu_key(event, ctx, progress):
    """Handle Up/Down/Enter navigation on the main menu."""
    stats = ctx.stats
    has_save = False

    if stats.dungeon_submenu_active:
        items = _get_dungeon_submenu_items()
        count = len(items)
        if event.key == pygame.K_UP:
            stats.dungeon_submenu_cursor = (stats.dungeon_submenu_cursor - 1) % count
        elif event.key == pygame.K_DOWN:
            stats.dungeon_submenu_cursor = (stats.dungeon_submenu_cursor + 1) % count
        elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            stats.dungeon_submenu_active = False
        elif event.key == pygame.K_RETURN:
            _, action, floor = items[stats.dungeon_submenu_cursor]
            if action == "dungeon_new":
                stats.dungeon_load_floor = 0
                stats.game_won = True
                stats.victory_cutscene_active = False
                stats.chapter3_active = True
                stats.game_started = True
            elif action == "dungeon_load":
                stats.dungeon_load_floor = floor
                stats.game_won = True
                stats.victory_cutscene_active = False
                stats.chapter3_active = True
                stats.game_started = True
            elif action == "back":
                stats.dungeon_submenu_active = False
        elif event.key == pygame.K_q:
            sys.exit()
        return

    if stats.rts_submenu_active:
        import save_manager

        has_save = save_manager.has_chapter2_save()
        # Ensure cursor isn't on a locked item (e.g. Load Save with no save)
        _validate_rts_cursor(stats, has_save)
        if event.key == pygame.K_UP:
            _move_rts_cursor(stats, -1, has_save)
        elif event.key == pygame.K_DOWN:
            _move_rts_cursor(stats, 1, has_save)
        elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            stats.rts_submenu_active = False
        elif event.key == pygame.K_RETURN:
            action = RTS_SUBMENU_ITEMS[stats.rts_submenu_cursor][1]
            if action == "rts_new":
                stats.rts_load_save = False
                stats.game_won = True
                stats.victory_cutscene_active = False
                stats.chapter2_active = True
                stats.game_started = True
            elif action == "rts_load" and has_save:
                stats.rts_load_save = True
                stats.game_won = True
                stats.victory_cutscene_active = False
                stats.chapter2_active = True
                stats.game_started = True
            elif action == "back":
                stats.rts_submenu_active = False
        elif event.key == pygame.K_q:
            sys.exit()
        return

    # Main menu navigation
    if event.key == pygame.K_UP:
        _move_cursor(stats, -1, progress)
    elif event.key == pygame.K_DOWN:
        _move_cursor(stats, 1, progress)
    elif event.key == pygame.K_RETURN:
        idx = stats.menu_cursor
        if not _is_item_unlocked(idx, progress):
            return
        _, action_type, action_value = MENU_ITEMS[idx]
        if action_type == "start_level":
            _start_level(ctx, action_value)
        elif action_type == "rts_menu":
            stats.rts_submenu_active = True
            stats.rts_submenu_cursor = 0
        elif action_type == "dungeon_menu":
            stats.dungeon_submenu_active = True
            stats.dungeon_submenu_cursor = 0
    elif event.key == pygame.K_q:
        sys.exit()
