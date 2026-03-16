"""Post-boss-fight victory cutscene.

Shows the player in their cockpit receiving a video call from the
High Commander of the United Earth Army, who warns about robotic
lizards attacking the colony planet Nova Kepler-7.
"""

import math
import random
import pygame
from pixel_art import draw_pixel_art

# ── Cockpit frame (drawn once) ──────────────────────────────────────

_COCKPIT_COLOR = (45, 50, 65)
_COCKPIT_TRIM = (70, 80, 100)
_COCKPIT_DARK = (25, 28, 38)
_LED_GREEN = (0, 200, 80)
_LED_RED = (200, 40, 30)
_LED_AMBER = (200, 160, 30)

# ── Commander pixel art (12 x 14 grid, ps=4 → 48 x 56 px) ──────────

_CMD_PS = 4

_CMD_PALETTE = {
    1: (60, 80, 50),  # uniform dark green
    2: (80, 110, 65),  # uniform green
    3: (200, 160, 120),  # skin
    4: (170, 130, 95),  # skin shadow
    5: (50, 50, 60),  # hair dark
    6: (255, 200, 0),  # medal / insignia gold
    7: (220, 220, 230),  # collar white
    8: (0, 0, 0),  # eyes
    9: (180, 60, 60),  # mouth / lips
}

_CMD_MAP = [
    # 0  1  2  3  4  5  6  7  8  9 10 11
    [0, 0, 0, 0, 5, 5, 5, 5, 0, 0, 0, 0],  #  0  hair top
    [0, 0, 0, 5, 5, 5, 5, 5, 5, 0, 0, 0],  #  1  hair
    [0, 0, 5, 5, 3, 3, 3, 3, 5, 5, 0, 0],  #  2  forehead
    [0, 0, 5, 3, 3, 3, 3, 3, 3, 5, 0, 0],  #  3  temples
    [0, 0, 0, 3, 8, 3, 3, 8, 3, 0, 0, 0],  #  4  eyes
    [0, 0, 0, 3, 3, 3, 3, 3, 3, 0, 0, 0],  #  5  cheeks
    [0, 0, 0, 4, 3, 4, 4, 3, 4, 0, 0, 0],  #  6  nose
    [0, 0, 0, 3, 3, 9, 9, 3, 3, 0, 0, 0],  #  7  mouth
    [0, 0, 0, 0, 4, 3, 3, 4, 0, 0, 0, 0],  #  8  chin
    [0, 0, 0, 7, 7, 7, 7, 7, 7, 0, 0, 0],  #  9  collar
    [0, 0, 1, 2, 2, 2, 2, 2, 2, 1, 0, 0],  # 10  uniform top
    [0, 1, 1, 2, 6, 2, 2, 6, 2, 1, 1, 0],  # 11  uniform medals
    [0, 1, 1, 2, 2, 2, 2, 2, 2, 1, 1, 0],  # 12  uniform
    [1, 1, 1, 2, 2, 2, 2, 2, 2, 1, 1, 1],  # 13  uniform bottom
]

# ── Robotic lizard pixel art (14 x 10 grid, ps=4 → 56 x 40 px) ─────

_LIZ_PS = 4

_LIZ_PALETTE = {
    1: (100, 120, 130),  # metal body
    2: (140, 160, 170),  # metal highlight
    3: (255, 30, 30),  # red eye
    4: (60, 70, 80),  # dark armor
    5: (180, 200, 50),  # circuit glow yellow-green
    6: (80, 90, 100),  # limbs
    7: (50, 60, 70),  # tail / claws dark
}

_LIZ_MAP = [
    # 0  1  2  3  4  5  6  7  8  9 10 11 12 13
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 1, 0],  # 0  head top
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 2, 1],  # 1  head + eye
    [7, 7, 0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 1, 0],  # 2  tail + head
    [0, 7, 7, 4, 4, 1, 1, 1, 1, 5, 1, 1, 0, 0],  # 3  tail + body
    [0, 0, 0, 4, 1, 1, 2, 2, 1, 1, 1, 0, 0, 0],  # 4  body main
    [0, 0, 0, 1, 1, 5, 1, 1, 5, 1, 0, 0, 0, 0],  # 5  body circuits
    [0, 0, 0, 1, 4, 1, 1, 1, 1, 4, 0, 0, 0, 0],  # 6  body lower
    [0, 0, 6, 0, 6, 0, 0, 6, 0, 6, 0, 0, 0, 0],  # 7  legs upper
    [0, 0, 6, 0, 6, 0, 0, 6, 0, 6, 0, 0, 0, 0],  # 8  legs lower
    [0, 7, 7, 0, 7, 7, 0, 7, 7, 0, 7, 7, 0, 0],  # 9  claws / feet
]

# ── Dialogue lines ──────────────────────────────────────────────────

_DIALOGUE = [
    ("CMD", "Pilot, this is High Commander"),
    ("CMD", "Vasquez. United Earth Army."),
    ("CMD", "Outstanding work destroying"),
    ("CMD", "that alien mothership."),
    ("CMD", "But we have no time to"),
    ("CMD", "celebrate. Nova Kepler-7 is"),
    ("CMD", "under attack. Something new."),
    ("CMD", "Super-intelligent robotic"),
    ("CMD", "lizards. Take a look..."),
    ("LIZ", ""),
    ("CMD", "They're tearing through our"),
    ("CMD", "defenses. We need you there"),
    ("CMD", "NOW. Godspeed, pilot."),
]

# Timing
_FADE_IN_FRAMES = 40  # cockpit fades in
_CALL_ALERT_FRAMES = 90  # "INCOMING TRANSMISSION" blinks
_CHARS_PER_FRAME = 0.8  # typewriter speed


class VictoryCutscene:
    """Manages the post-boss victory cutscene animation."""

    def __init__(self, screen_w, screen_h, font_scale=1.0):
        self._sw = screen_w
        self._sh = screen_h
        self._fs = font_scale
        self._frame = 0
        self._finished = False
        self._prompt_visible = False

        # Build fonts
        body_size = max(12, int(18 * font_scale))
        label_size = max(10, int(14 * font_scale))
        title_size = max(16, int(24 * font_scale))
        self._font = pygame.font.SysFont("consolas", body_size)
        self._label_font = pygame.font.SysFont("consolas", label_size)
        self._title_font = pygame.font.SysFont("consolas", title_size, bold=True)
        self._prompt_font = pygame.font.SysFont(
            "consolas", max(14, int(20 * font_scale))
        )

        # Build pixel art surfaces
        self._cmd_img = self._build_sprite(_CMD_MAP, _CMD_PS, _CMD_PALETTE, font_scale)
        self._liz_img = self._build_sprite(_LIZ_MAP, _LIZ_PS, _LIZ_PALETTE, font_scale)

        # Layout
        self._screen_area = self._calc_screen_area()

        # Pre-render scanline overlay (avoids hundreds of blits per frame)
        sa = self._screen_area
        self._scanline_surf = pygame.Surface((sa.width, sa.height), pygame.SRCALPHA)
        for y in range(0, sa.height, 3):
            pygame.draw.line(self._scanline_surf, (0, 0, 0, 40), (0, y), (sa.width, y))

        # Dialogue state
        self._dial_index = 0
        self._dial_char = 0.0
        self._dial_lines_shown = []  # list of rendered surfaces
        self._current_display = "CMD"  # "CMD" or "LIZ"
        self._dial_phase = "FADE_IN"
        # phases: FADE_IN -> ALERT -> DIALOGUE -> DONE
        self._waiting_for_input = False  # True = line done, waiting for ENTER
        self._typing_done = False  # True = current line fully typed out

        # Stars for cockpit window
        self._stars = []
        for _ in range(60):
            self._stars.append(
                (
                    float(random.randint(0, screen_w)),
                    float(random.randint(0, screen_h)),
                    random.choice([1, 1, 1, 2]),
                    random.uniform(0.3, 1.0),
                    random.uniform(0.01, 0.04),
                    random.uniform(0, 6.28),
                )
            )

    @staticmethod
    def _build_sprite(pixel_map, ps, palette, font_scale):
        cols = len(pixel_map[0])
        rows = len(pixel_map)
        w, h = cols * ps, rows * ps
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        draw_pixel_art(surf, pixel_map, ps, palette)
        # Scale proportionally
        sw = max(8, int(w * font_scale))
        sh = max(8, int(h * font_scale))
        if font_scale != 1.0:
            return pygame.transform.smoothscale(surf, (sw, sh))
        return surf

    def _calc_screen_area(self):
        """The comm screen rectangle in the center of the cockpit."""
        margin_x = int(self._sw * 0.12)
        margin_top = int(self._sh * 0.10)
        margin_bot = int(self._sh * 0.35)
        return pygame.Rect(
            margin_x,
            margin_top,
            self._sw - 2 * margin_x,
            self._sh - margin_top - margin_bot,
        )

    @property
    def finished(self):
        return self._finished

    @property
    def prompt_visible(self):
        return self._prompt_visible

    def update(self):
        self._frame += 1

        if self._dial_phase == "FADE_IN":
            if self._frame >= _FADE_IN_FRAMES:
                self._dial_phase = "ALERT"
                self._frame = 0
        elif self._dial_phase == "ALERT":
            if self._frame >= _CALL_ALERT_FRAMES:
                self._dial_phase = "DIALOGUE"
                self._frame = 0
        elif self._dial_phase == "DIALOGUE":
            self._update_dialogue()
        # DONE — just wait for input

    def advance(self):
        """Called when the player presses ENTER during the cutscene."""
        if self._dial_phase == "FADE_IN":
            self._dial_phase = "ALERT"
            self._frame = 0
            return
        if self._dial_phase == "ALERT":
            self._dial_phase = "DIALOGUE"
            self._frame = 0
            return
        if self._dial_phase == "DONE":
            return

        # During DIALOGUE
        if self._waiting_for_input:
            tag, text = _DIALOGUE[self._dial_index]

            if tag == "LIZ" and text == "":
                # Dismiss lizard screen
                self._dial_index += 1
                self._current_display = "CMD"
                self._dial_lines_shown.clear()
                self._waiting_for_input = False
                self._typing_done = False
                return

            # Paused at end of a group — advance to next line
            self._dial_index += 1
            self._dial_char = 0.0
            self._waiting_for_input = False
            self._typing_done = False
            return

        elif not self._typing_done:
            # Skip typewriter — show full line immediately, auto-advance will
            # commit it on the next update() call
            if self._dial_index < len(_DIALOGUE):
                tag, text = _DIALOGUE[self._dial_index]
                if text:
                    self._dial_char = float(len(text))

    def _update_dialogue(self):
        if self._dial_index >= len(_DIALOGUE):
            if not self._finished:
                self._dial_phase = "DONE"
                self._finished = True
                self._prompt_visible = True
            return

        if self._waiting_for_input:
            return  # paused, waiting for ENTER

        tag, text = _DIALOGUE[self._dial_index]

        # Switch display if tag changes
        if tag == "LIZ" and self._current_display != "LIZ":
            self._current_display = "LIZ"
            self._dial_lines_shown.clear()

        if tag == "LIZ" and text == "":
            # Show lizard and wait for input
            self._waiting_for_input = True
            self._typing_done = True
            return

        # Typewriter effect
        self._dial_char += _CHARS_PER_FRAME
        shown = int(self._dial_char)
        if shown >= len(text):
            # Line fully typed — commit rendered text
            self._typing_done = True
            rendered = self._font.render(text, True, (200, 220, 200))
            self._dial_lines_shown.append(rendered)
            max_lines = max(
                3, self._screen_area.height // (self._font.get_height() + 4) - 5
            )
            if len(self._dial_lines_shown) > max_lines:
                self._dial_lines_shown.pop(0)

            # Pause before switching to a different display (e.g. LIZ)
            next_idx = self._dial_index + 1
            if next_idx < len(_DIALOGUE) and _DIALOGUE[next_idx][0] != tag:
                self._waiting_for_input = True
            else:
                self._dial_index += 1
                self._dial_char = 0.0
                self._typing_done = False

    def draw(self, screen):
        screen.fill((5, 5, 15))

        # Draw stars through windshield
        for sx, sy, size, brightness, speed, phase in self._stars:
            flicker = 0.6 + 0.4 * math.sin(phase + self._frame * speed)
            alpha = int(255 * brightness * flicker)
            c = min(255, alpha)
            pygame.draw.circle(screen, (c, c, int(c * 0.9)), (int(sx), int(sy)), size)

        # Draw cockpit frame
        self._draw_cockpit(screen)

        # Draw comm screen content
        sa = self._screen_area
        if self._dial_phase == "FADE_IN":
            # Fade in the screen
            progress = min(1.0, self._frame / max(1, _FADE_IN_FRAMES))
            alpha = int(255 * progress)
            overlay = pygame.Surface((sa.width, sa.height), pygame.SRCALPHA)
            overlay.fill((10, 20, 15, alpha))
            screen.blit(overlay, sa.topleft)
            # Scanline effect
            self._draw_scanlines(screen, sa, alpha // 3)

        elif self._dial_phase == "ALERT":
            # Dark screen with blinking "INCOMING TRANSMISSION"
            pygame.draw.rect(screen, (10, 20, 15), sa)
            self._draw_scanlines(screen, sa, 40)
            if (self._frame // 15) % 2 == 0:
                alert = self._title_font.render(
                    "INCOMING TRANSMISSION", True, (0, 255, 100)
                )
                ar = alert.get_rect(center=sa.center)
                screen.blit(alert, ar)

        elif self._dial_phase in ("DIALOGUE", "DONE"):
            # Screen background
            pygame.draw.rect(screen, (10, 20, 15), sa)
            self._draw_scanlines(screen, sa, 25)

            if self._current_display == "CMD":
                self._draw_commander_screen(screen, sa)
            else:
                self._draw_lizard_screen(screen, sa)

        # Screen border (CRT-style)
        pygame.draw.rect(screen, (100, 120, 140), sa, 2)
        # Corner dots
        for cx, cy in [sa.topleft, sa.topright, sa.bottomleft, sa.bottomright]:
            pygame.draw.circle(screen, (120, 140, 160), (cx, cy), 3)

        # Prompt — show whenever waiting for input (per-line or final)
        if self._waiting_for_input or self._prompt_visible:
            if (self._frame // 20) % 2 == 0:
                label = "Press ENTER to continue"
                prompt = self._prompt_font.render(label, True, (200, 200, 200))
                pr = prompt.get_rect(
                    centerx=self._sw // 2,
                    bottom=self._sh - int(20 * self._fs),
                )
                screen.blit(prompt, pr)

        pygame.display.flip()

    def _draw_cockpit(self, screen):
        """Draw cockpit frame around the comm screen."""
        sw, sh = self._sw, self._sh
        sa = self._screen_area

        # Top panel
        pygame.draw.rect(screen, _COCKPIT_COLOR, (0, 0, sw, sa.top))
        # Bottom panel (instrument panel)
        bot_y = sa.bottom
        pygame.draw.rect(screen, _COCKPIT_COLOR, (0, bot_y, sw, sh - bot_y))
        # Side panels
        pygame.draw.rect(screen, _COCKPIT_COLOR, (0, sa.top, sa.left, sa.height))
        pygame.draw.rect(
            screen, _COCKPIT_COLOR, (sa.right, sa.top, sw - sa.right, sa.height)
        )

        # Panel details — horizontal lines on bottom panel
        panel_y = bot_y + int(15 * self._fs)
        for i in range(3):
            y = panel_y + i * int(18 * self._fs)
            pygame.draw.line(
                screen,
                _COCKPIT_TRIM,
                (int(30 * self._fs), y),
                (sw - int(30 * self._fs), y),
                1,
            )

        # LED indicators on bottom panel
        led_y = bot_y + int(70 * self._fs)
        led_x_start = int(40 * self._fs)
        led_spacing = int(20 * self._fs)
        led_r = max(2, int(4 * self._fs))
        colors = [
            _LED_GREEN,
            _LED_GREEN,
            _LED_AMBER,
            _LED_GREEN,
            _LED_RED,
            _LED_GREEN,
            _LED_AMBER,
        ]
        for i, color in enumerate(colors):
            x = led_x_start + i * led_spacing
            # Blink the red one
            if color == _LED_RED and (self._frame // 20) % 2 == 0:
                color = (60, 15, 10)
            pygame.draw.circle(screen, color, (x, led_y), led_r)

        # Label on bottom panel
        status = self._label_font.render("COMM ACTIVE", True, _LED_GREEN)
        sr = status.get_rect(
            right=sw - int(40 * self._fs),
            top=bot_y + int(10 * self._fs),
        )
        screen.blit(status, sr)

        # Top panel struts (diagonal cockpit window frame)
        strut_w = max(3, int(5 * self._fs))
        # Left strut
        pygame.draw.line(screen, _COCKPIT_DARK, (sa.left, sa.top), (0, 0), strut_w)
        # Right strut
        pygame.draw.line(screen, _COCKPIT_DARK, (sa.right, sa.top), (sw, 0), strut_w)
        # Bottom struts
        pygame.draw.line(screen, _COCKPIT_DARK, (sa.left, sa.bottom), (0, sh), strut_w)
        pygame.draw.line(
            screen, _COCKPIT_DARK, (sa.right, sa.bottom), (sw, sh), strut_w
        )

        # Rim around screen cutout
        rim = pygame.Rect(sa.left - 3, sa.top - 3, sa.width + 6, sa.height + 6)
        pygame.draw.rect(screen, _COCKPIT_TRIM, rim, 2)

    def _draw_scanlines(self, screen, area, alpha):
        """Draw faint CRT scanlines over the screen area."""
        if alpha <= 0:
            return
        self._scanline_surf.set_alpha(min(255, alpha * 255 // 40))
        screen.blit(self._scanline_surf, area.topleft)

    def _draw_commander_screen(self, screen, sa):
        """Draw the commander's face and dialogue text."""
        # Commander portrait in upper-left of screen area
        portrait_x = sa.left + int(12 * self._fs)
        portrait_y = sa.top + int(12 * self._fs)
        screen.blit(self._cmd_img, (portrait_x, portrait_y))

        # Name label next to portrait
        img_w = self._cmd_img.get_width()
        name_x = portrait_x + img_w + int(10 * self._fs)
        name_y = portrait_y + int(4 * self._fs)
        name = self._label_font.render("HIGH CMDR. VASQUEZ", True, (0, 220, 100))
        screen.blit(name, (name_x, name_y))
        rank = self._label_font.render("United Earth Army", True, (0, 180, 80))
        screen.blit(rank, (name_x, name_y + self._label_font.get_height() + 2))

        # Separator line
        img_h = self._cmd_img.get_height()
        sep_y = portrait_y + img_h + int(8 * self._fs)
        pygame.draw.line(
            screen,
            (0, 100, 60),
            (sa.left + int(10 * self._fs), sep_y),
            (sa.right - int(10 * self._fs), sep_y),
            1,
        )

        # Previously completed lines
        text_y = sep_y + int(8 * self._fs)
        line_h = self._font.get_height() + int(4 * self._fs)
        for surf in self._dial_lines_shown:
            screen.blit(surf, (sa.left + int(14 * self._fs), text_y))
            text_y += line_h

        # Current line being typed (typewriter)
        if not self._waiting_for_input and self._dial_index < len(_DIALOGUE):
            tag, text = _DIALOGUE[self._dial_index]
            if tag == "CMD" and text:
                visible = text[: int(self._dial_char)]
                if visible:
                    typing = self._font.render(visible, True, (200, 220, 200))
                    screen.blit(typing, (sa.left + int(14 * self._fs), text_y))
                    # Blinking cursor
                    if (self._frame // 8) % 2 == 0:
                        cx = sa.left + int(14 * self._fs) + typing.get_width()
                        cursor = self._font.render("_", True, (0, 255, 100))
                        screen.blit(cursor, (cx, text_y))

    def _draw_lizard_screen(self, screen, sa):
        """Show the robotic lizard on the comm screen."""
        # Title
        title = self._title_font.render("THREAT ANALYSIS", True, (255, 60, 60))
        tr = title.get_rect(centerx=sa.centerx, top=sa.top + int(12 * self._fs))
        screen.blit(title, tr)

        # Separator
        sep_y = tr.bottom + int(6 * self._fs)
        pygame.draw.line(
            screen,
            (150, 40, 40),
            (sa.left + int(10 * self._fs), sep_y),
            (sa.right - int(10 * self._fs), sep_y),
            1,
        )

        # Lizard image centered
        liz_rect = self._liz_img.get_rect(
            centerx=sa.centerx,
            centery=sa.centery - int(10 * self._fs),
        )
        screen.blit(self._liz_img, liz_rect)

        # Animated scanning effect around lizard
        scan_phase = self._frame * 0.05
        scan_alpha = int(80 + 40 * math.sin(scan_phase))
        scan_rect = liz_rect.inflate(int(16 * self._fs), int(16 * self._fs))
        scan_surf = pygame.Surface((scan_rect.width, scan_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(scan_surf, (255, 50, 50, scan_alpha), scan_surf.get_rect(), 2)
        screen.blit(scan_surf, scan_rect.topleft)

        # Classification label
        info_y = liz_rect.bottom + int(16 * self._fs)
        cls_text = self._label_font.render(
            "CLASS: MECHA-SAURIAN  |  THREAT: EXTREME", True, (255, 80, 80)
        )
        cr = cls_text.get_rect(centerx=sa.centerx, top=info_y)
        screen.blit(cls_text, cr)

        loc_text = self._label_font.render(
            "LOCATION: NOVA KEPLER-7  |  STATUS: ACTIVE", True, (255, 120, 80)
        )
        lr = loc_text.get_rect(centerx=sa.centerx, top=cr.bottom + int(4 * self._fs))
        screen.blit(loc_text, lr)
