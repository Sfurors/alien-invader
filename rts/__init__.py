"""RTS Mode — Chapter 2 controller.

Manages the full RTS game loop: landing cutscene, base building,
resource gathering, combat, and AI.
"""

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

    def __init__(self, screen, sounds, font_scale=1.0):
        self.screen = screen
        self.sounds = sounds
        self.screen_w = screen.get_width()
        self.screen_h = screen.get_height()
        self.font_scale = font_scale

        # Phase: "landing" -> "playing" -> "done"
        self.phase = "landing"
        self.landing = LandingCutscene(self.screen_w, self.screen_h, font_scale)

        self._rts_initialized = False
        self.rts_ctx = None
        self.state = None
        self.fog = None
        self.minimap = None
        self.ai = None

    def _init_rts(self):
        """Initialize RTS game state."""
        settings = RTSSettings()
        tile_map = TileMap()
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
        self._setup_player()
        self._setup_enemy()

        # Center camera on player base
        camera.center_on(
            3 * RTSSettings.TILE_SIZE * 32 // 32, 3 * RTSSettings.TILE_SIZE * 32 // 32
        )

        self._rts_initialized = True

    def _setup_player(self):
        """Place initial player entities."""
        # Main base at top-left area
        base = BaseBuilding("main_base", 3, 3, "human")
        base.tile_map = self.rts_ctx.tile_map
        self.rts_ctx.player_buildings.add(base)
        self.rts_ctx.all_entities.add(base)

        # Starting engineer
        eng = BaseUnit("engineer", 6, 5, "human")
        self.rts_ctx.player_units.add(eng)
        self.rts_ctx.all_entities.add(eng)

    def _setup_enemy(self):
        """Place initial enemy entities."""
        mw = RTSSettings.MAP_WIDTH
        mh = RTSSettings.MAP_HEIGHT
        # Hive at bottom-right area
        hive = BaseBuilding("hive", mw - 6, mh - 6, "lizard")
        hive.tile_map = self.rts_ctx.tile_map
        self.rts_ctx.enemy_buildings.add(hive)
        self.rts_ctx.all_entities.add(hive)

        # Starting units
        scout = BaseUnit("scout", mw - 5, mh - 4, "lizard")
        self.rts_ctx.enemy_units.add(scout)
        self.rts_ctx.all_entities.add(scout)

        drone = BaseUnit("drone", mw - 4, mh - 4, "lizard")
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
        result = rts_events.handle_events(self.rts_ctx, self.state, self.fog)
        if result == "quit":
            return "quit"

        # Check for ENTER on game over
        if self.state.game_over:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.phase = "done"
                        return "done"
                    elif event.key == pygame.K_q:
                        sys.exit()

        if not self.state.game_over:
            rts_logic.update(self.rts_ctx, self.state, self.fog, self.ai)

        rts_renderer.draw_frame(
            self.screen, self.rts_ctx, self.state, self.fog, self.minimap
        )
        return None
