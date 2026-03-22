"""RTS Mode — Chapter 2 controller.

Manages the full RTS game loop: landing cutscene, base building,
resource gathering, combat, and AI.
"""

import random
import sys
import pygame
from .rts_settings import RTSSettings
from .rts_context import RTSContext
from .rts_state import RTSState
from .tile_map import TileMap
from .camera import Camera
from .fog import FogOfWar
from .minimap import Minimap
from .entity_base import BaseUnit, BaseBuilding
from .ai import LizardAI
from .hud_manager import HudManager
from .landing_cutscene import LandingCutscene
from . import rts_events
from . import rts_logic
from . import rts_renderer


class RTSMode:
    """Top-level controller for the RTS chapter."""

    def __init__(self, screen, sounds, font_scale=1.0, load_save=False):
        self.screen = screen
        self.sounds = sounds
        self.screen_w = screen.get_width()
        self.screen_h = screen.get_height()
        self.font_scale = font_scale

        self._rts_initialized = False
        self.rts_ctx = None
        self.state = None
        self.fog = None
        self.minimap = None
        self.ai = None

        # If a save exists, skip the landing cutscene and load it
        if load_save:
            self.phase = "playing"
            self.landing = None
            self._init_rts()
            self._load_saved_game()
        else:
            # Phase: "landing" -> "playing" -> "done"
            self.phase = "landing"
            self.landing = LandingCutscene(self.screen_w, self.screen_h, font_scale)

    def _init_rts(self):
        """Initialize RTS game state."""
        settings = RTSSettings()

        # Pick random spawn points
        spawns = list(RTSSettings.SPAWN_POINTS)
        self.player_spawn = random.choice(spawns)
        valid_enemy = [
            s
            for s in spawns
            if (
                abs(s[0] - self.player_spawn[0]) + abs(s[1] - self.player_spawn[1])
                >= RTSSettings.MIN_SPAWN_DISTANCE
            )
        ]
        self.enemy_spawn = random.choice(valid_enemy)

        tile_map = TileMap(spawns=[self.player_spawn, self.enemy_spawn])
        camera = Camera(self.screen_w, self.screen_h)

        self.rts_ctx = RTSContext(
            settings=settings,
            screen=self.screen,
            sounds=self.sounds,
            tile_map=tile_map,
            camera=camera,
            screen_w=self.screen_w,
            screen_h=self.screen_h,
            font_scale=self.font_scale,
        )

        self.state = RTSState(
            RTSSettings.STARTING_CRYSTALS, RTSSettings.STARTING_ISOTOPE
        )
        self.fog = FogOfWar()
        self.rts_ctx.fog = self.fog
        self.minimap = Minimap()
        self.rts_ctx.minimap = self.minimap
        self.ai = LizardAI()
        self.rts_ctx.ai = self.ai
        self.rts_ctx.hud_manager = HudManager()

        # Place player starting units and base
        self._setup_player(self.player_spawn)
        self._setup_enemy(self.enemy_spawn)

        # Center camera on player base
        bx, by = self.player_spawn
        camera.center_on(
            (bx + 2) * RTSSettings.TILE_SIZE,
            (by + 2) * RTSSettings.TILE_SIZE,
        )

        self._rts_initialized = True

    def _load_saved_game(self):
        """Load a Ch2 save file, replacing the fresh game state."""
        import save_manager

        save_data = save_manager.load_chapter2()
        if save_data:
            save_manager.reconstruct_rts(self, save_data)
            self.state.save_message = "Game Loaded"
            self.state.save_message_timer = 120

    def _setup_player(self, spawn):
        """Place initial player entities at spawn (sx, sy)."""
        sx, sy = spawn
        base = BaseBuilding("main_base", sx + 1, sy + 1, "human")
        base.tile_map = self.rts_ctx.tile_map
        self.rts_ctx.player_buildings.add(base)
        self.rts_ctx.all_entities.add(base)

        # Starting engineer
        eng = BaseUnit("engineer", sx + 4, sy + 3, "human")
        self.rts_ctx.player_units.add(eng)
        self.rts_ctx.all_entities.add(eng)

        # Starting miner
        miner = BaseUnit("miner", sx + 5, sy + 3, "human")
        self.rts_ctx.player_units.add(miner)
        self.rts_ctx.all_entities.add(miner)

    def _setup_enemy(self, spawn):
        """Place initial enemy entities at spawn (sx, sy)."""
        sx, sy = spawn
        hive = BaseBuilding("hive", sx + 1, sy + 1, "lizard")
        hive.tile_map = self.rts_ctx.tile_map
        self.rts_ctx.enemy_buildings.add(hive)
        self.rts_ctx.all_entities.add(hive)

        # Starting units – two offensive scouts and one economic drone
        scout1 = BaseUnit("scout", sx + 3, sy + 2, "lizard")
        self.rts_ctx.enemy_units.add(scout1)
        self.rts_ctx.all_entities.add(scout1)

        scout2 = BaseUnit("scout", sx + 5, sy + 2, "lizard")
        self.rts_ctx.enemy_units.add(scout2)
        self.rts_ctx.all_entities.add(scout2)

        drone = BaseUnit("drone", sx + 4, sy + 2, "lizard")
        self.rts_ctx.enemy_units.add(drone)
        self.rts_ctx.all_entities.add(drone)

    def update(self):
        """Called once per frame from the main game loop.

        Returns:
            "done" when RTS mode is complete (player won/lost and pressed ENTER).
            None otherwise.
        """
        if self.phase == "landing":
            return self._update_landing()
        elif self.phase == "playing":
            return self._update_playing()
        elif self.phase == "done":
            return "done"
        return None

    def _update_landing(self):
        """Handle landing cutscene phase."""
        self.landing.update()
        self.landing.draw(self.screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    sys.exit()
                elif event.key == pygame.K_RETURN:
                    self.landing._finished = True

        if self.landing.finished:
            if not self._rts_initialized:
                self._init_rts()
            self.phase = "playing"
        return None

    def _update_playing(self):
        """Handle main RTS gameplay phase."""
        # ── Pause menu ──
        if self.state.paused:
            result = self._handle_pause_events()
            if result == "menu":
                self.phase = "done"
                return "menu"
            rts_renderer.draw_pause_overlay(self.screen, self.rts_ctx)
            return None

        result = rts_events.handle_events(self.rts_ctx, self.state, self.fog)
        if result == "quit":
            return "quit"
        if result == "pause":
            # First frame of pause — just draw overlay, don't process further
            rts_renderer.draw_pause_overlay(self.screen, self.rts_ctx)
            return None
        if result == "save":
            import save_manager

            save_manager.save_chapter2(self)
            self.state.save_message = "Game Saved"
            self.state.save_message_timer = 120
        elif result == "load":
            import save_manager

            save_data = save_manager.load_chapter2()
            if save_data:
                save_manager.reconstruct_rts(self, save_data)
                self.state.save_message = "Game Loaded"
                self.state.save_message_timer = 120

        # Tick save message timer
        if self.state.save_message_timer > 0:
            self.state.save_message_timer -= 1
            if self.state.save_message_timer <= 0:
                self.state.save_message = None

        # Check for ENTER on game over — return to main menu
        if self.state.game_over:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.phase = "done"
                        return "menu"
                    elif event.key == pygame.K_q:
                        sys.exit()

        if not self.state.game_over:
            rts_logic.update(self.rts_ctx, self.state, self.fog, self.ai)

        rts_renderer.draw_frame(
            self.screen, self.rts_ctx, self.state, self.fog, self.minimap
        )
        return None

    def _handle_pause_events(self):
        """Handle events while RTS is paused. Returns 'menu' or None."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state.paused = False
                elif event.key == pygame.K_F5:
                    import save_manager

                    save_manager.save_chapter2(self)
                    self.state.save_message = "Game Saved"
                    self.state.save_message_timer = 120
                    self.state.paused = False
                elif event.key == pygame.K_F9:
                    import save_manager

                    save_data = save_manager.load_chapter2()
                    if save_data:
                        save_manager.reconstruct_rts(self, save_data)
                        self.state.save_message = "Game Loaded"
                        self.state.save_message_timer = 120
                    self.state.paused = False
                elif event.key == pygame.K_m:
                    self.state.paused = False
                    return "menu"
                elif event.key == pygame.K_q:
                    sys.exit()
        return None
