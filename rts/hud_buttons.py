"""HUD button system: compact icon buttons with hover tooltips."""

import pygame


class HudButton:
    """A single clickable HUD button."""

    __slots__ = (
        "rect",
        "icon",
        "hotkey",
        "action_id",
        "enabled",
        "hovered",
        "tooltip_title",
        "tooltip_detail",
    )

    def __init__(
        self,
        x,
        y,
        w,
        h,
        icon,
        hotkey,
        action_id,
        enabled=True,
        tooltip_title="",
        tooltip_detail="",
    ):
        self.rect = pygame.Rect(x, y, w, h)
        self.icon = icon  # short 1-3 char icon/initial
        self.hotkey = hotkey  # e.g. "1", "P", "S"
        self.action_id = action_id
        self.enabled = enabled
        self.hovered = False
        self.tooltip_title = tooltip_title
        self.tooltip_detail = tooltip_detail


# Colors
_BG_NORMAL = (50, 50, 60)
_BG_HOVER = (65, 68, 82)
_BG_DISABLED = (35, 35, 42)
_BORDER_NORMAL = (80, 80, 90)
_BORDER_HOVER = (140, 150, 180)
_BORDER_DISABLED = (50, 50, 55)
_ICON_NORMAL = (220, 220, 230)
_ICON_DISABLED = (90, 90, 100)
_HOTKEY_COLOR = (120, 120, 145)
_TOOLTIP_BG = (25, 25, 35, 230)
_TOOLTIP_TITLE = (230, 230, 240)
_TOOLTIP_DETAIL = (160, 170, 190)
_TOOLTIP_COST_C = (80, 220, 255)
_TOOLTIP_COST_I = (50, 220, 80)


class HudButtonPanel:
    """Manages a grid of HudButtons with layout, drawing, and hit-testing."""

    def __init__(self):
        self.buttons = []
        self._icon_font = None
        self._hotkey_font = None
        self._tip_font = None
        self._tip_small_font = None

    def _ensure_fonts(self, font_scale):
        if self._icon_font is None:
            self._icon_font = pygame.font.SysFont(
                "consolas", max(12, int(15 * font_scale)), bold=True
            )
            self._hotkey_font = pygame.font.SysFont(
                "consolas", max(8, int(9 * font_scale))
            )
            self._tip_font = pygame.font.SysFont(
                "consolas", max(11, int(13 * font_scale)), bold=True
            )
            self._tip_small_font = pygame.font.SysFont(
                "consolas", max(10, int(11 * font_scale))
            )

    def clear(self):
        self.buttons = []

    def add(
        self,
        x,
        y,
        w,
        h,
        icon,
        hotkey,
        action_id,
        enabled=True,
        tooltip_title="",
        tooltip_detail="",
    ):
        btn = HudButton(
            x,
            y,
            w,
            h,
            icon,
            hotkey,
            action_id,
            enabled,
            tooltip_title,
            tooltip_detail,
        )
        self.buttons.append(btn)
        return btn

    def hit_test(self, mx, my):
        """Return the enabled button at (mx, my) or None."""
        for btn in self.buttons:
            if btn.rect.collidepoint(mx, my) and btn.enabled:
                return btn
        return None

    def update_hover(self, mx, my):
        for btn in self.buttons:
            btn.hovered = btn.rect.collidepoint(mx, my)

    def get_hovered(self):
        """Return the currently hovered button, or None."""
        for btn in self.buttons:
            if btn.hovered:
                return btn
        return None

    def draw(self, screen, font_scale):
        self._ensure_fonts(font_scale)
        for btn in self.buttons:
            self._draw_button(screen, btn)

    def draw_tooltip(self, screen, font_scale):
        """Draw tooltip for hovered button (call after all other HUD drawing)."""
        self._ensure_fonts(font_scale)
        hovered = self.get_hovered()
        if hovered is None or not hovered.tooltip_title:
            return

        title = hovered.tooltip_title
        detail = hovered.tooltip_detail

        title_surf = self._tip_font.render(title, True, _TOOLTIP_TITLE)
        lines = [title_surf]
        if detail:
            detail_surf = self._tip_small_font.render(detail, True, _TOOLTIP_DETAIL)
            lines.append(detail_surf)

        pad = 6
        tip_w = max(s.get_width() for s in lines) + pad * 2
        tip_h = sum(s.get_height() for s in lines) + pad * 2 + (len(lines) - 1) * 2

        # Position above the button
        r = hovered.rect
        tx = r.x
        ty = r.y - tip_h - 4
        # Keep on screen
        sw = screen.get_width()
        if tx + tip_w > sw:
            tx = sw - tip_w - 4
        if ty < 0:
            ty = r.bottom + 4

        bg = pygame.Surface((tip_w, tip_h), pygame.SRCALPHA)
        bg.fill(_TOOLTIP_BG)
        screen.blit(bg, (tx, ty))
        pygame.draw.rect(screen, (80, 80, 100), (tx, ty, tip_w, tip_h), 1)

        cy = ty + pad
        for surf in lines:
            screen.blit(surf, (tx + pad, cy))
            cy += surf.get_height() + 2

    def _draw_button(self, screen, btn):
        r = btn.rect
        if not btn.enabled:
            bg, border, icon_c = _BG_DISABLED, _BORDER_DISABLED, _ICON_DISABLED
        elif btn.hovered:
            bg, border, icon_c = _BG_HOVER, _BORDER_HOVER, _ICON_NORMAL
        else:
            bg, border, icon_c = _BG_NORMAL, _BORDER_NORMAL, _ICON_NORMAL

        pygame.draw.rect(screen, bg, r)
        pygame.draw.rect(screen, border, r, 1)

        # Icon centered
        icon_surf = self._icon_font.render(btn.icon, True, icon_c)
        ix = r.x + (r.width - icon_surf.get_width()) // 2
        iy = r.y + (r.height - icon_surf.get_height()) // 2
        screen.blit(icon_surf, (ix, iy))

        # Hotkey badge top-left
        if btn.hotkey:
            hk_surf = self._hotkey_font.render(btn.hotkey, True, _HOTKEY_COLOR)
            screen.blit(hk_surf, (r.x + 2, r.y + 1))
