import pygame

_ROCKET_ICON = None
_BOSS_LABEL_FONT = None
_BOSS_LABEL_FONT_SIZE = None


def _get_boss_label_font(screen_w=768):
    global _BOSS_LABEL_FONT, _BOSS_LABEL_FONT_SIZE
    size = max(10, int(14 * screen_w / 768))
    if _BOSS_LABEL_FONT is None or _BOSS_LABEL_FONT_SIZE != size:
        _BOSS_LABEL_FONT = pygame.font.SysFont("consolas", size)
        _BOSS_LABEL_FONT_SIZE = size
    return _BOSS_LABEL_FONT


def _reset_rocket_icon():
    """Clear the cached icon — used in tests for a clean slate."""
    global _ROCKET_ICON
    _ROCKET_ICON = None


_HUD_ROCKET_MAP = [
    # 0  1  2  3  4  5
    [0, 0, 1, 1, 0, 0],  # 0  nose tip
    [0, 0, 3, 3, 0, 0],  # 1  nose cone
    [0, 3, 3, 3, 3, 0],  # 2  nose base
    [0, 1, 1, 1, 1, 0],  # 3  body top
    [0, 1, 2, 2, 1, 0],  # 4  body
    [0, 1, 2, 2, 1, 0],  # 5  body
    [0, 1, 2, 2, 1, 0],  # 6  body
    [0, 1, 1, 1, 1, 0],  # 7  body bottom
    [3, 3, 3, 3, 3, 3],  # 8  flame base
    [0, 0, 4, 4, 0, 0],  # 9  flame tip
]
_HUD_PALETTE = {
    1: (220, 220, 230),
    2: (160, 160, 180),
    3: (255, 100, 30),
    4: (255, 220, 60),
}


def _get_rocket_icon():
    global _ROCKET_ICON
    if _ROCKET_ICON is None:
        from pixel_art import draw_pixel_art

        ps = 4  # 6 cols × 10 rows × 4 = 24 × 40 px
        icon_w = len(_HUD_ROCKET_MAP[0]) * ps  # 24
        icon_h = len(_HUD_ROCKET_MAP) * ps  # 40
        _ROCKET_ICON = pygame.Surface((icon_w, icon_h), pygame.SRCALPHA)
        draw_pixel_art(_ROCKET_ICON, _HUD_ROCKET_MAP, ps, _HUD_PALETTE)
    return _ROCKET_ICON


def draw_score(screen, stats, font):
    score_str = f"Score: {stats.score}"
    img = font.render(score_str, True, (255, 255, 255))
    screen_rect = screen.get_rect()
    rect = img.get_rect()
    rect.topright = (screen_rect.right - 10, 10)
    screen.blit(img, rect)


def draw_rocket_hud(screen, stats, font):
    screen_rect = screen.get_rect()
    icon = _get_rocket_icon()
    icon_rect = icon.get_rect(topright=(screen_rect.right - 10, 45))
    screen.blit(icon, icon_rect)
    count_img = font.render(f"\u00d7{stats.rockets}", True, (255, 255, 255))
    count_rect = count_img.get_rect(right=icon_rect.left - 6, centery=icon_rect.centery)
    screen.blit(count_img, count_rect)


def draw_menu(
    screen,
    ai_settings,
    title_font,
    menu_font,
    bg=None,
    menu_anim=None,
    progress=None,
    stats=None,
):
    from events import MENU_ITEMS, RTS_SUBMENU_ITEMS
    import save_manager

    if progress is None:
        progress = save_manager.load_progress()

    screen.fill(ai_settings.bg_color)
    if bg is not None:
        bg.draw(screen)
    screen_rect = screen.get_rect()
    cx = screen_rect.centerx
    fs = ai_settings.font_scale

    if menu_anim is not None:
        menu_anim.draw(screen)

    title = title_font.render("ALIEN INVASION", True, (0, 220, 80))
    title_rect = title.get_rect(center=(cx, screen_rect.centery - 80))
    screen.blit(title, title_rect)

    item_font = pygame.font.SysFont("consolas", max(14, int(24 * fs)))
    small_font = pygame.font.SysFont("consolas", max(12, int(18 * fs)))
    line_h = int(36 * fs)
    start_y = screen_rect.centery + 10

    if stats is not None and stats.rts_submenu_active:
        # RTS sub-menu
        header = item_font.render("RTS Mode", True, (0, 220, 80))
        screen.blit(header, header.get_rect(center=(cx, start_y - line_h)))

        has_save = save_manager.has_chapter2_save()
        for i, (label, action) in enumerate(RTS_SUBMENU_ITEMS):
            if action == "rts_load" and not has_save:
                color = (60, 60, 60)
            elif stats.rts_submenu_cursor == i:
                color = (0, 220, 80)
                label = "> " + label
            else:
                color = (200, 200, 200)
            surf = item_font.render(label, True, color)
            screen.blit(surf, surf.get_rect(center=(cx, start_y + i * line_h)))

        hint = small_font.render("ESC to go back", True, (120, 120, 120))
        screen.blit(
            hint,
            hint.get_rect(center=(cx, start_y + len(RTS_SUBMENU_ITEMS) * line_h + 20)),
        )
    else:
        # Main menu item list
        max_level = progress.get("max_unlocked_level", 1)
        rts_unlocked = progress.get("rts_unlocked", False)
        cursor = stats.menu_cursor if stats else 0

        for i, (label, _action_type, _action_value) in enumerate(MENU_ITEMS):
            if i < 4:
                unlocked = max_level >= (i + 1)
            else:
                unlocked = rts_unlocked

            if not unlocked:
                color = (60, 60, 60)
                display = label + "  (locked)"
            elif cursor == i:
                color = (0, 220, 80)
                display = "> " + label
            else:
                color = (200, 200, 200)
                display = label

            surf = item_font.render(display, True, color)
            screen.blit(surf, surf.get_rect(center=(cx, start_y + i * line_h)))

        quit_y = start_y + len(MENU_ITEMS) * line_h + 20
        quit_hint = small_font.render("Q to Quit", True, (120, 120, 120))
        screen.blit(quit_hint, quit_hint.get_rect(center=(cx, quit_y)))

    pygame.display.flip()


def draw_game_over(screen, ai_settings, title_font, menu_font, bg=None, stats=None):
    screen.fill(ai_settings.bg_color)
    if bg is not None:
        bg.draw(screen)
    screen_rect = screen.get_rect()
    cx = screen_rect.centerx

    over = title_font.render("GAME OVER", True, (220, 50, 50))
    over_rect = over.get_rect(center=(cx, screen_rect.centery - 80))
    screen.blit(over, over_rect)

    if stats is not None:
        score_text = menu_font.render(f"Score: {stats.score}", True, (200, 200, 200))
        score_rect = score_text.get_rect(center=(cx, screen_rect.centery - 20))
        screen.blit(score_text, score_rect)

        lvl = stats.level
        prompt = menu_font.render(
            f"Press ENTER to Retry Level {lvl}", True, (0, 220, 80)
        )
        prompt_rect = prompt.get_rect(center=(cx, screen_rect.centery + 30))
        screen.blit(prompt, prompt_rect)

    menu_hint = menu_font.render("M for Main Menu", True, (180, 180, 180))
    menu_rect = menu_hint.get_rect(center=(cx, screen_rect.centery + 70))
    screen.blit(menu_hint, menu_rect)

    pygame.display.flip()


def draw_victory(screen, ai_settings, stats, title_font, menu_font, bg=None):
    screen.fill(ai_settings.bg_color)
    if bg is not None:
        bg.draw(screen)
    screen_rect = screen.get_rect()

    win = title_font.render("YOU WIN!", True, (0, 220, 80))
    win_rect = win.get_rect(center=(screen_rect.centerx, screen_rect.centery - 80))

    score_text = menu_font.render(f"Final Score: {stats.score}", True, (255, 255, 255))
    score_rect = score_text.get_rect(center=(screen_rect.centerx, screen_rect.centery))

    prompt = menu_font.render("Press ENTER to Play Again", True, (200, 200, 200))
    prompt_rect = prompt.get_rect(
        center=(screen_rect.centerx, screen_rect.centery + 60)
    )

    screen.blit(win, win_rect)
    screen.blit(score_text, score_rect)
    screen.blit(prompt, prompt_rect)
    pygame.display.flip()


def draw_level_banner(ctx, font, title_font):
    screen = ctx.screen
    screen.fill(ctx.settings.bg_color)
    ctx.background.draw(screen)
    ctx.asteroids.draw(screen)
    screen_rect = screen.get_rect()

    if ctx.stats.boss_active:
        text = "BOSS FIGHT"
        color = (220, 50, 50)
    else:
        text = f"LEVEL {ctx.stats.level}"
        color = (0, 220, 80)

    banner = title_font.render(text, True, color)
    banner_rect = banner.get_rect(center=screen_rect.center)
    screen.blit(banner, banner_rect)

    draw_score(screen, ctx.stats, font)
    draw_level(screen, ctx.stats, font)
    pygame.display.flip()


def draw_level(screen, stats, font):
    level_str = f"Level: {stats.level}"
    img = font.render(level_str, True, (255, 255, 255))
    screen.blit(img, (10, 10))


def draw_boss_hp_bar(screen, boss_group):
    for boss in boss_group.sprites():
        screen_rect = screen.get_rect()
        bar_w = int(300 * screen_rect.width / 768)
        bar_h = 16
        bar_x = screen_rect.centerx - bar_w // 2
        bar_y = 14

        txt = _get_boss_label_font(screen_rect.width).render(
            "BOSS", True, (255, 255, 255)
        )
        txt_rect = txt.get_rect(centerx=screen_rect.centerx, bottom=bar_y - 2)
        screen.blit(txt, txt_rect)

        pygame.draw.rect(screen, (80, 0, 0), (bar_x, bar_y, bar_w, bar_h))
        hp_w = int(bar_w * boss.hp / boss.max_hp)
        pygame.draw.rect(screen, (220, 30, 30), (bar_x, bar_y, hp_w, bar_h))
        pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), 1)


def draw_pause_menu(screen):
    """Draw a translucent pause overlay with controls reference."""
    from pause_ui import draw_pause_screen

    sections = [
        {
            "title": "Controls",
            "entries": [
                ("Arrow Keys", "Move ship", (180, 180, 180)),
                ("Space", "Fire bullet", (180, 180, 180)),
                ("B", "Fire / Detonate rocket", (180, 180, 180)),
            ],
        },
        {
            "title": "Menu",
            "entries": [
                ("ESC", "Resume game", (0, 220, 80)),
                ("M", "Quit to main menu", (220, 180, 50)),
                ("Q", "Quit game", (220, 50, 50)),
            ],
        },
    ]

    font_scale = screen.get_rect().width / 768
    draw_pause_screen(screen, "PAUSED", sections, font_scale=font_scale)
    pygame.display.flip()


def update_screen(ctx, font, hint_font):
    screen = ctx.screen
    screen.fill(ctx.settings.bg_color)
    ctx.background.draw(screen)
    ctx.asteroids.draw(screen)
    for bullet in ctx.bullets.sprites():
        bullet.draw()
    ctx.ship.blitme()
    ctx.aliens.draw(screen)
    ctx.boss_group.draw(screen)
    ctx.boss_projectiles.draw(screen)
    ctx.explosions.draw(screen)
    ctx.drops.draw(screen)
    ctx.rockets.draw(screen)
    draw_score(screen, ctx.stats, font)
    draw_rocket_hud(screen, ctx.stats, font)
    draw_level(screen, ctx.stats, font)
    if ctx.stats.boss_active:
        draw_boss_hp_bar(screen, ctx.boss_group)
    if ctx.rockets.sprites():
        screen_rect = screen.get_rect()
        hint = hint_font.render("Press B to detonate", True, (0, 220, 80))
        hint_rect = hint.get_rect(centerx=screen_rect.centerx, top=10)
        screen.blit(hint, hint_rect)
    pygame.display.flip()
