"""Dungeon FPS Mode — Chapter 3 controller.

After the RTS chapter, aliens have dug into the planet surface.
The player descends into dungeons to destroy the alien hive.
"""

import sys
import pygame
from .dungeon_settings import DungeonSettings
from .dungeon_player import DungeonPlayer
from .dungeon_enemy import DungeonEnemy
from . import dungeon_map
from . import dungeon_events
from . import dungeon_logic
from . import dungeon_renderer


class DungeonMode:
    """Top-level controller for the Dungeon FPS chapter."""

    def __init__(self, screen, sounds, font_scale=1.0):
        self.screen = screen
        self.sounds = sounds
        self.screen_w = screen.get_width()
        self.screen_h = screen.get_height()
        self.font_scale = font_scale

        # Phase: "intro" -> "playing" -> "dead" -> "done"
        self.phase = "intro"
        self.intro_timer = 120  # 2 seconds at 60fps

        self._init_floor(1)

        # Capture mouse for FPS controls
        self.mouse_captured = False

    def _init_floor(self, floor_num):
        """Initialize or reset dungeon state for a given floor."""
        grid, spawn, enemies_data, pickups_data = dungeon_map.get_floor(floor_num)

        if not hasattr(self, "ctx") or self.ctx is None:
            player = DungeonPlayer(spawn[0], spawn[1])
        else:
            # Keep player state across floors
            player = self.ctx.player
            player.x = spawn[0] + 0.5
            player.y = spawn[1] + 0.5
            player.angle = 0.0

        enemies = []
        for etype, row, col in enemies_data:
            enemies.append(DungeonEnemy(etype, col, row))

        pickups = []
        for ptype, row, col in pickups_data:
            cfg = DungeonSettings.PICKUP_TYPES.get(ptype, {})
            pickups.append(
                {
                    "type": ptype,
                    "x": col + 0.5,
                    "y": row + 0.5,
                    "color": cfg.get("color", (200, 200, 200)),
                }
            )

        # Render surface at low resolution
        render_surface = pygame.Surface(
            (DungeonSettings.RENDER_WIDTH, DungeonSettings.RENDER_HEIGHT)
        )

        # Small font for HUD on the low-res surface
        hud_font = pygame.font.SysFont("consolas", 10)

        self.ctx = _DungeonContext(
            player=player,
            grid=grid,
            enemies=enemies,
            pickups=pickups,
            floor_num=floor_num,
            render_surface=render_surface,
            screen_w=self.screen_w,
            screen_h=self.screen_h,
            sounds=self.sounds,
            hud_font=hud_font,
            projectiles=[],
            fire_flash=0,
            floor_complete=False,
            mouse_captured=False,
        )

    def update(self):
        """Called once per frame. Returns 'done' when dungeon complete, None otherwise."""
        if self.phase == "intro":
            return self._update_intro()
        elif self.phase == "playing":
            return self._update_playing()
        elif self.phase == "dead":
            return self._update_dead()
        elif self.phase == "floor_complete":
            return self._update_floor_complete()
        elif self.phase == "done":
            return "menu"
        return None

    def _update_intro(self):
        """Show brief intro text."""
        self.intro_timer -= 1

        self.screen.fill((0, 0, 0))
        fs = self.font_scale
        font = pygame.font.SysFont("consolas", max(20, int(36 * fs)), bold=True)
        small = pygame.font.SysFont("consolas", max(12, int(22 * fs)))

        lines = [
            "CHAPTER 3: THE HIVE",
            "",
            "Aliens have dug deep into the planet.",
            "Descend into the dungeons. Destroy the hive.",
            "",
            f"Floor {self.ctx.floor_num}",
            "",
            "WASD - Move    Mouse - Look",
            "LMB - Fire     TAB - Switch Weapon",
            "",
        ]
        if self.intro_timer < 60:
            lines.append("Press ENTER to begin")

        cy = self.screen_h // 2 - len(lines) * 16
        for i, line in enumerate(lines):
            f = font if i == 0 else small
            color = (200, 50, 50) if i == 0 else (180, 180, 200)
            text = f.render(line, True, color)
            rect = text.get_rect(center=(self.screen_w // 2, cy + i * 32))
            self.screen.blit(text, rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    sys.exit()
                elif event.key == pygame.K_RETURN and self.intro_timer < 60:
                    self._capture_mouse()
                    self.phase = "playing"
                elif event.key == pygame.K_ESCAPE:
                    return "menu"
        return None

    def _update_playing(self):
        """Main gameplay loop."""
        self.ctx.mouse_captured = self.mouse_captured
        result = dungeon_events.handle_events(self.ctx)

        if result == "quit":
            self._release_mouse()
            return "menu"
        elif result == "dead":
            self._release_mouse()
            self.phase = "dead"
            return None
        elif result == "next_floor":
            self._next_floor()
            return None

        dungeon_logic.update(self.ctx)

        if not self.ctx.player.alive:
            self._release_mouse()
            self.phase = "dead"

        if self.ctx.floor_complete:
            self._release_mouse()
            self.phase = "floor_complete"
            self.intro_timer = 90

        dungeon_renderer.draw_frame(self.screen, self.ctx)
        return None

    def _update_dead(self):
        """Game over screen."""
        self.screen.fill((40, 0, 0))
        fs = self.font_scale
        font = pygame.font.SysFont("consolas", max(24, int(48 * fs)), bold=True)
        small = pygame.font.SysFont("consolas", max(12, int(22 * fs)))

        texts = [
            (font, "YOU DIED", (255, 50, 50)),
            (small, f"Score: {self.ctx.player.score}", (255, 220, 50)),
            (small, f"Kills: {self.ctx.player.kills}", (180, 180, 200)),
            (small, f"Floor: {self.ctx.floor_num}", (180, 180, 200)),
            (small, "", (0, 0, 0)),
            (small, "Press ENTER to return", (120, 120, 140)),
        ]
        cy = self.screen_h // 2 - len(texts) * 18
        for i, (f, text, color) in enumerate(texts):
            surf = f.render(text, True, color)
            rect = surf.get_rect(center=(self.screen_w // 2, cy + i * 36))
            self.screen.blit(surf, rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    self.phase = "done"
                    return "menu"
                elif event.key == pygame.K_q:
                    sys.exit()
        return None

    def _update_floor_complete(self):
        """Brief transition between floors."""
        self.intro_timer -= 1

        self.screen.fill((0, 0, 0))
        fs = self.font_scale
        font = pygame.font.SysFont("consolas", max(20, int(36 * fs)), bold=True)
        small = pygame.font.SysFont("consolas", max(12, int(22 * fs)))

        texts = [
            (font, f"FLOOR {self.ctx.floor_num} CLEARED", (50, 255, 50)),
            (small, "Descending deeper...", (180, 180, 200)),
        ]
        if self.intro_timer < 30:
            texts.append((small, "Press ENTER to continue", (120, 120, 140)))

        cy = self.screen_h // 2 - 40
        for i, (f, text, color) in enumerate(texts):
            surf = f.render(text, True, color)
            rect = surf.get_rect(center=(self.screen_w // 2, cy + i * 36))
            self.screen.blit(surf, rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and self.intro_timer < 30:
                    self._next_floor()
                elif event.key == pygame.K_q:
                    sys.exit()
                elif event.key == pygame.K_ESCAPE:
                    self.phase = "done"
                    return "menu"
        return None

    def _next_floor(self):
        """Advance to the next dungeon floor."""
        next_num = self.ctx.floor_num + 1
        self._init_floor(next_num)
        self._capture_mouse()
        self.phase = "playing"

    def _capture_mouse(self):
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)
        pygame.mouse.get_rel()  # clear accumulated delta
        self.mouse_captured = True

    def _release_mouse(self):
        pygame.mouse.set_visible(True)
        pygame.event.set_grab(False)
        self.mouse_captured = False


class _DungeonContext:
    """Holds all dungeon state for passing between modules."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
