"""Mutable RTS game state: resources, selection, build mode."""

import pygame


class RTSState:
    def __init__(self, starting_crystals=200, starting_isotope=0):
        self.crystals = starting_crystals
        self.isotope = starting_isotope
        self.selected_units = []
        self.selected_building = None
        self.build_mode = None  # None or building type string
        self.build_valid = False
        self.build_preview_pos = None  # (tx, ty)

        # Box select state
        self.box_selecting = False
        self.box_start = None  # (sx, sy)
        self.box_end = None

        # Game outcome
        self.game_over = False
        self.victory = False

        # Frame counter
        self.frame = 0

        # Minimap alerts (scout seppuku locations)
        self.minimap_alerts = []  # list of (tx, ty, start_frame)

        # Save/load feedback overlay
        self.save_message = None  # e.g. "Game Saved" or "Game Loaded"
        self.save_message_timer = 0

        # Pause menu
        self.paused = False

    def clear_selection(self):
        for u in self.selected_units:
            u.selected = False
        self.selected_units = []
        if self.selected_building is not None:
            self.selected_building.selected = False
            self.selected_building = None

    def cancel_build(self):
        self.build_mode = None
        self.build_valid = False
        self.build_preview_pos = None
