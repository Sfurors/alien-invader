"""Tile map with procedural generation."""

import random
from .rts_settings import RTSSettings as S


class TileMap:
    def __init__(self, width=S.MAP_WIDTH, height=S.MAP_HEIGHT, seed=None):
        self.width = width
        self.height = height
        # terrain type per tile
        self.tiles = [[S.GRASS] * width for _ in range(height)]
        # crystal amounts per tile
        self.crystal = [[0] * width for _ in range(height)]
        # isotope amounts per tile
        self.isotope = [[0] * width for _ in range(height)]
        if seed is not None:
            random.seed(seed)
        self._generate()

    def _generate(self):
        self._place_rock_clusters(100)
        self._place_water_bodies(32)
        self._place_sand_edges()
        self._place_crystals(60)
        self._place_isotope_vents(20)
        self._clear_starting_area(2, 2)  # player corner
        self._clear_starting_area(
            self.width - 6,
            self.height - 6,  # enemy corner
        )

    def _place_rock_clusters(self, count):
        for _ in range(count):
            cx = random.randint(4, self.width - 5)
            cy = random.randint(4, self.height - 5)
            x, y = cx, cy
            for _ in range(random.randint(8, 20)):
                if 1 <= x < self.width - 1 and 1 <= y < self.height - 1:
                    self.tiles[y][x] = S.ROCK
                x += random.choice([-1, 0, 1])
                y += random.choice([-1, 0, 1])

    def _place_water_bodies(self, count):
        for _ in range(count):
            cx = random.randint(8, self.width - 9)
            cy = random.randint(8, self.height - 9)
            rx = random.randint(3, 5)
            ry = random.randint(3, 5)
            for dy in range(-ry, ry + 1):
                for dx in range(-rx, rx + 1):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        dist = (dx * dx) / max(1, rx * rx) + (dy * dy) / max(1, ry * ry)
                        if dist <= 1.0:
                            self.tiles[ny][nx] = S.WATER

    def _place_sand_edges(self):
        """Place sand around water tiles."""
        sand_tiles = []
        for y in range(self.height):
            for x in range(self.width):
                if self.tiles[y][x] == S.WATER:
                    for dy in range(-1, 2):
                        for dx in range(-1, 2):
                            nx, ny = x + dx, y + dy
                            if (
                                0 <= nx < self.width
                                and 0 <= ny < self.height
                                and self.tiles[ny][nx] == S.GRASS
                            ):
                                sand_tiles.append((nx, ny))
        for x, y in sand_tiles:
            self.tiles[y][x] = S.SAND

    def _place_crystals(self, count):
        for _ in range(count):
            x = random.randint(4, self.width - 5)
            y = random.randint(4, self.height - 5)
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < self.width
                        and 0 <= ny < self.height
                        and self.tiles[ny][nx] == S.GRASS
                    ):
                        if random.random() < 0.6:
                            self.tiles[ny][nx] = S.CRYSTAL
                            self.crystal[ny][nx] = S.CRYSTAL_PER_TILE

    def _place_isotope_vents(self, count):
        """Place isotope deposits: 2x2 clusters, mid-map bias."""
        for _ in range(count):
            x = random.randint(30, self.width - 31)
            y = random.randint(30, self.height - 31)
            for dy in range(2):
                for dx in range(2):
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < self.width
                        and 0 <= ny < self.height
                        and self.tiles[ny][nx] == S.GRASS
                    ):
                        if random.random() < 0.6:
                            self.tiles[ny][nx] = S.ISOTOPE
                            self.isotope[ny][nx] = S.ISOTOPE_PER_TILE

    def _clear_starting_area(self, sx, sy):
        """Clear a 5x5 area for base placement."""
        for dy in range(5):
            for dx in range(5):
                nx, ny = sx + dx, sy + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    self.tiles[ny][nx] = S.GRASS
                    self.crystal[ny][nx] = 0
                    self.isotope[ny][nx] = 0

    def is_passable(self, tx, ty):
        if 0 <= tx < self.width and 0 <= ty < self.height:
            return self.tiles[ty][tx] not in (S.ROCK, S.WATER, S.RUINS)
        return False

    def in_bounds(self, tx, ty):
        return 0 <= tx < self.width and 0 <= ty < self.height
