"""Tests for RTS tile map generation."""

import pytest
from rts.tile_map import TileMap
from rts.rts_settings import RTSSettings as S


class TestTileMapGeneration:
    def test_map_dimensions(self):
        tm = TileMap(seed=42)
        assert len(tm.tiles) == S.MAP_HEIGHT
        assert len(tm.tiles[0]) == S.MAP_WIDTH

    def test_starting_areas_clear(self):
        tm = TileMap(seed=42)
        # Player area (top-left)
        for dy in range(5):
            for dx in range(5):
                assert tm.tiles[2 + dy][2 + dx] == S.GRASS
        # Enemy area (bottom-right)
        for dy in range(5):
            for dx in range(5):
                assert tm.tiles[S.MAP_HEIGHT - 6 + dy][S.MAP_WIDTH - 6 + dx] == S.GRASS

    def test_has_crystals(self):
        tm = TileMap(seed=42)
        crystal_count = sum(1 for row in tm.tiles for t in row if t == S.CRYSTAL)
        assert crystal_count > 0

    def test_has_rock(self):
        tm = TileMap(seed=42)
        rock_count = sum(1 for row in tm.tiles for t in row if t == S.ROCK)
        assert rock_count > 0

    def test_has_water(self):
        tm = TileMap(seed=42)
        water_count = sum(1 for row in tm.tiles for t in row if t == S.WATER)
        assert water_count > 0

    def test_is_passable(self):
        tm = TileMap(seed=42)
        # Starting area should be passable
        assert tm.is_passable(3, 3)
        # Out of bounds not passable
        assert not tm.is_passable(-1, 0)
        assert not tm.is_passable(0, S.MAP_HEIGHT)

    def test_seed_reproducibility(self):
        tm1 = TileMap(seed=123)
        tm2 = TileMap(seed=123)
        assert tm1.tiles == tm2.tiles

    def test_crystal_amounts(self):
        tm = TileMap(seed=42)
        for y in range(tm.height):
            for x in range(tm.width):
                if tm.tiles[y][x] == S.CRYSTAL:
                    assert tm.crystal[y][x] == S.CRYSTAL_PER_TILE
                else:
                    assert tm.crystal[y][x] == 0
