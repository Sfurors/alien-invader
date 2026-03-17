"""Shared pause menu UI with rounded panels, key badges, and section grouping."""

import pygame

# --- Color constants (matching HUD button style) ---
OVERLAY = (0, 0, 0, 180)
PANEL_BG = (30, 30, 40, 200)
PANEL_BORDER = (60, 60, 75)
HEADER_BG = (45, 45, 58, 220)
BADGE_BG = (50, 50, 60)
BADGE_BORDER = (80, 80, 90)
BADGE_TEXT = (220, 220, 230)
TITLE_COLOR = (0, 220, 80)
FOOTER_BG = (25, 25, 35, 180)
FOOTER_BORDER = (60, 80, 60)

# --- Font cache ---
_font_cache = {}
_font_cache_scale = None


def _get_fonts(font_scale):
    """Return dict of cached fonts for the given scale, recreating if scale changed."""
    global _font_cache, _font_cache_scale
    if _font_cache_scale == font_scale and _font_cache:
        return _font_cache
    fs = font_scale
    _font_cache = {
        "title": pygame.font.SysFont("consolas", max(24, int(48 * fs)), bold=True),
        "header": pygame.font.SysFont("consolas", max(11, int(16 * fs)), bold=True),
        "entry": pygame.font.SysFont("consolas", max(10, int(14 * fs))),
        "badge": pygame.font.SysFont("consolas", max(10, int(13 * fs)), bold=True),
        "footer": pygame.font.SysFont("consolas", max(10, int(13 * fs))),
    }
    _font_cache_scale = font_scale
    return _font_cache


# --- Layout constants (multiplied by font_scale) ---
PANEL_PAD_H = 16
PANEL_PAD_V = 12
PANEL_RADIUS = 6
KEY_COL_WIDTH = 140
ROW_HEIGHT = 22
BADGE_PAD_H = 6
BADGE_PAD_V = 2
BADGE_RADIUS = 3
HEADER_HEIGHT = 28
SECTION_GAP = 16


def draw_pause_screen(
    surface, title, sections, footer=None, footer_color=(100, 200, 100), font_scale=1.0
):
    """Draw complete pause overlay. Called by both Ch1 and RTS renderers."""
    screen_rect = surface.get_rect()
    sw, sh = screen_rect.width, screen_rect.height
    fs = font_scale
    fonts = _get_fonts(fs)

    # Dark overlay
    overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
    overlay.fill(OVERLAY)
    surface.blit(overlay, (0, 0))

    # Scaled layout values
    panel_w = min(int(500 * fs), int(sw * 0.65))
    panel_pad_h = int(PANEL_PAD_H * fs)
    panel_pad_v = int(PANEL_PAD_V * fs)
    key_col_w = int(KEY_COL_WIDTH * fs)
    row_h = int(ROW_HEIGHT * fs)
    header_h = int(HEADER_HEIGHT * fs)
    section_gap = int(SECTION_GAP * fs)
    badge_pad_h = int(BADGE_PAD_H * fs)
    badge_pad_v = int(BADGE_PAD_V * fs)
    panel_radius = int(PANEL_RADIUS * fs)
    badge_radius = int(BADGE_RADIUS * fs)

    # Calculate total height for vertical centering
    title_surf = fonts["title"].render(title, True, TITLE_COLOR)
    title_h = title_surf.get_height() + int(20 * fs)  # title + underline + gap

    total_h = title_h
    for section in sections:
        total_h += header_h + panel_pad_v * 2
        total_h += len(section["entries"]) * row_h
        total_h += section_gap

    if footer:
        total_h += int(30 * fs)

    start_y = max(int(20 * fs), (sh - total_h) // 2)
    panel_x = (sw - panel_w) // 2

    # --- Title ---
    title_rect = title_surf.get_rect(centerx=sw // 2, top=start_y)
    surface.blit(title_surf, title_rect)

    # Accent underline
    underline_w = int(120 * fs)
    underline_y = title_rect.bottom + int(4 * fs)
    pygame.draw.line(
        surface,
        TITLE_COLOR,
        (sw // 2 - underline_w // 2, underline_y),
        (sw // 2 + underline_w // 2, underline_y),
        max(2, int(2 * fs)),
    )

    y = underline_y + int(16 * fs)

    # --- Section panels ---
    for section in sections:
        entries = section["entries"]
        panel_h = header_h + panel_pad_v + len(entries) * row_h + panel_pad_v
        _draw_section_panel(
            surface,
            fonts,
            section["title"],
            entries,
            panel_x,
            y,
            panel_w,
            panel_h,
            header_h,
            panel_pad_h,
            panel_pad_v,
            key_col_w,
            row_h,
            badge_pad_h,
            badge_pad_v,
            panel_radius,
            badge_radius,
        )
        y += panel_h + section_gap

    # --- Footer ---
    if footer:
        _draw_footer_panel(surface, fonts, footer, footer_color, sw // 2, y, fs)


def _draw_section_panel(
    surface,
    fonts,
    title,
    entries,
    px,
    py,
    pw,
    ph,
    header_h,
    pad_h,
    pad_v,
    key_col_w,
    row_h,
    badge_pad_h,
    badge_pad_v,
    panel_radius,
    badge_radius,
):
    """Draw a single section: rounded panel with header strip and entry rows."""
    # Panel background
    panel_surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, PANEL_BG, (0, 0, pw, ph), border_radius=panel_radius)
    surface.blit(panel_surf, (px, py))

    # Panel border
    pygame.draw.rect(
        surface, PANEL_BORDER, (px, py, pw, ph), width=1, border_radius=panel_radius
    )

    # Header strip
    header_surf = pygame.Surface((pw - 2, header_h), pygame.SRCALPHA)
    pygame.draw.rect(
        header_surf,
        HEADER_BG,
        (0, 0, pw - 2, header_h),
        border_top_left_radius=panel_radius,
        border_top_right_radius=panel_radius,
    )
    surface.blit(header_surf, (px + 1, py + 1))

    # Header title
    header_text = fonts["header"].render(title, True, (200, 200, 210))
    header_rect = header_text.get_rect(left=px + pad_h, centery=py + header_h // 2)
    surface.blit(header_text, header_rect)

    # Entries
    entry_y = py + header_h + pad_v
    for key_label, action_text, text_color in entries:
        # Key badge
        _draw_key_badge(
            surface,
            fonts,
            key_label,
            px + pad_h,
            entry_y,
            badge_pad_h,
            badge_pad_v,
            badge_radius,
            row_h,
        )

        # Action text
        action_surf = fonts["entry"].render(action_text, True, text_color)
        action_rect = action_surf.get_rect(
            left=px + pad_h + key_col_w,
            centery=entry_y + row_h // 2,
        )
        surface.blit(action_surf, action_rect)

        entry_y += row_h


def _draw_key_badge(surface, fonts, text, x, y, pad_h, pad_v, radius, row_h):
    """Draw a small rounded-rect key badge."""
    badge_surf = fonts["badge"].render(text, True, BADGE_TEXT)
    bw = badge_surf.get_width() + pad_h * 2
    bh = badge_surf.get_height() + pad_v * 2
    badge_y = y + (row_h - bh) // 2

    # Background
    bg = pygame.Surface((bw, bh), pygame.SRCALPHA)
    pygame.draw.rect(bg, BADGE_BG, (0, 0, bw, bh), border_radius=radius)
    surface.blit(bg, (x, badge_y))

    # Border
    pygame.draw.rect(
        surface, BADGE_BORDER, (x, badge_y, bw, bh), width=1, border_radius=radius
    )

    # Text
    text_rect = badge_surf.get_rect(center=(x + bw // 2, badge_y + bh // 2))
    surface.blit(badge_surf, text_rect)


def _draw_footer_panel(surface, fonts, text, color, cx, y, fs):
    """Draw a tooltip-style footer pill with save info."""
    footer_surf = fonts["footer"].render(text, True, color)
    pad_h = int(12 * fs)
    pad_v = int(6 * fs)
    pw = footer_surf.get_width() + pad_h * 2
    ph = footer_surf.get_height() + pad_v * 2
    radius = int(4 * fs)

    fx = cx - pw // 2
    fy = y

    # Background
    bg = pygame.Surface((pw, ph), pygame.SRCALPHA)
    pygame.draw.rect(bg, FOOTER_BG, (0, 0, pw, ph), border_radius=radius)
    surface.blit(bg, (fx, fy))

    # Border
    pygame.draw.rect(
        surface, FOOTER_BORDER, (fx, fy, pw, ph), width=1, border_radius=radius
    )

    # Text
    text_rect = footer_surf.get_rect(center=(fx + pw // 2, fy + ph // 2))
    surface.blit(footer_surf, text_rect)
