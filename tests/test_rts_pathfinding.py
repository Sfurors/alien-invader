"""Tests for RTS A* pathfinding."""

import pytest
from rts.pathfinding import find_path
from rts.tile_map import TileMap
from rts.rts_settings import RTSSettings as S


class TestPathfinding:
    def setup_method(self):
        self.tm = TileMap(seed=42)

    def test_path_to_self(self):
        path = find_path(self.tm, (3, 3), (3, 3))
        assert path == []

    def test_path_to_neighbor(self):
        path = find_path(self.tm, (3, 3), (4, 3))
        assert len(path) == 1
        assert path[0] == (4, 3)

    def test_path_in_clear_area(self):
        # Starting area is cleared, so path should exist
        path = find_path(self.tm, (3, 3), (5, 5))
        assert len(path) > 0
        assert path[-1] == (5, 5)

    def test_path_avoids_obstacles(self):
        path = find_path(self.tm, (3, 3), (5, 5))
        if path:
            for tx, ty in path:
                assert self.tm.is_passable(tx, ty)

    def test_path_with_occupied(self):
        occupied = {(4, 3)}
        path = find_path(self.tm, (3, 3), (5, 3), occupied)
        if path:
            for tx, ty in path:
                assert (tx, ty) not in occupied

    def test_path_to_impassable_finds_neighbor(self):
        # Find a rock tile
        rock_pos = None
        for y in range(self.tm.height):
            for x in range(self.tm.width):
                if self.tm.tiles[y][x] == S.ROCK:
                    rock_pos = (x, y)
                    break
            if rock_pos:
                break
        if rock_pos:
            path = find_path(self.tm, (3, 3), rock_pos)
            # Should find path to neighbor of rock, not rock itself
            if path:
                last = path[-1]
                assert self.tm.is_passable(last[0], last[1])

    def test_out_of_bounds_returns_empty(self):
        path = find_path(self.tm, (3, 3), (-1, -1))
        assert path == []
