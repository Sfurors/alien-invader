"""Dungeon level maps and generator."""

import random

# Tile types
EMPTY = 0
WALL_STONE = 1
WALL_ROCK = 2
WALL_ORGANIC = 3
WALL_METAL = 4
DOOR = 5
SPAWN = 6
EXIT_TILE = 7

WALL_TILES = {WALL_STONE, WALL_ROCK, WALL_ORGANIC, WALL_METAL}


def is_wall(tile):
    return tile in WALL_TILES


# Hand-crafted first floor for the intro experience
FLOOR_1 = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 6, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 1, 1, 0, 0, 3, 3, 0, 0, 1, 1, 0, 0, 1],
    [1, 0, 0, 1, 0, 0, 0, 3, 3, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 7, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]

# Enemy placement per floor: list of (type, row, col)
FLOOR_1_ENEMIES = [
    ("lizard_grunt", 2, 9),
    ("lizard_grunt", 6, 4),
    ("lizard_grunt", 10, 12),
    ("lizard_soldier", 10, 7),
]

# Pickup placement: list of (type, row, col)
FLOOR_1_PICKUPS = [
    ("health", 7, 1),
    ("shotgun", 13, 13),
    ("ammo", 6, 12),
]


def generate_floor(floor_num, width=24, height=24):
    """Generate a random dungeon floor. Returns (grid, spawn_pos, enemies, pickups)."""
    grid = [[WALL_STONE] * width for _ in range(height)]

    # Carve rooms
    rooms = []
    for _ in range(6 + floor_num):
        rw = random.randint(3, 6)
        rh = random.randint(3, 6)
        rx = random.randint(1, width - rw - 1)
        ry = random.randint(1, height - rh - 1)
        rooms.append((rx, ry, rw, rh))
        for y in range(ry, ry + rh):
            for x in range(rx, rx + rw):
                grid[y][x] = EMPTY

    # Connect rooms with corridors
    for i in range(len(rooms) - 1):
        x1 = rooms[i][0] + rooms[i][2] // 2
        y1 = rooms[i][1] + rooms[i][3] // 2
        x2 = rooms[i + 1][0] + rooms[i + 1][2] // 2
        y2 = rooms[i + 1][1] + rooms[i + 1][3] // 2
        # Horizontal then vertical
        cx = x1
        while cx != x2:
            grid[y1][cx] = EMPTY
            cx += 1 if x2 > cx else -1
        grid[y1][x2] = EMPTY
        cy = y1
        while cy != y2:
            grid[cy][x2] = EMPTY
            cy += 1 if y2 > cy else -1
        grid[y2][x2] = EMPTY

    # Add some organic walls on deeper floors (before placing entities)
    if floor_num >= 2:
        for y in range(height):
            for x in range(width):
                if grid[y][x] in WALL_TILES and random.random() < 0.3:
                    grid[y][x] = WALL_ORGANIC

    # Place spawn in first room, exit in the room farthest from spawn
    spawn = (rooms[0][0] + 1, rooms[0][1] + 1)
    spawn_cx = rooms[0][0] + rooms[0][2] // 2
    spawn_cy = rooms[0][1] + rooms[0][3] // 2

    best_dist = -1
    exit_room = rooms[-1]
    for room in rooms[1:]:
        rcx = room[0] + room[2] // 2
        rcy = room[1] + room[3] // 2
        d = (rcx - spawn_cx) ** 2 + (rcy - spawn_cy) ** 2
        if d > best_dist:
            best_dist = d
            exit_room = room

    exit_pos = (exit_room[0] + exit_room[2] // 2, exit_room[1] + exit_room[3] // 2)
    grid[exit_pos[1]][exit_pos[0]] = EXIT_TILE

    # Restyle existing walls near exit to metal for a distinctive frame
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if dy == 0 and dx == 0:
                continue
            ey = exit_pos[1] + dy
            ex = exit_pos[0] + dx
            if 0 <= ey < height and 0 <= ex < width and grid[ey][ex] in WALL_TILES:
                grid[ey][ex] = WALL_METAL

    # Place enemies
    enemies = []
    enemy_types = ["lizard_grunt", "lizard_soldier"]
    if floor_num >= 3:
        enemy_types.append("lizard_brute")
    num_enemies = 4 + floor_num * 2
    for _ in range(num_enemies):
        room = random.choice(rooms[1:])  # not in spawn room
        ex = room[0] + random.randint(1, room[2] - 2)
        ey = room[1] + random.randint(1, room[3] - 2)
        if grid[ey][ex] == EMPTY:
            etype = random.choice(enemy_types)
            enemies.append((etype, ey, ex))

    # Place pickups
    pickups = []
    pickup_options = ["health", "ammo"]
    if floor_num >= 2:
        pickup_options.append("plasma")
    if floor_num >= 3:
        pickup_options.append("rocket_launcher")
    num_pickups = 3 + floor_num
    for _ in range(num_pickups):
        room = random.choice(rooms)
        px = room[0] + random.randint(1, room[2] - 2)
        py = room[1] + random.randint(1, room[3] - 2)
        if grid[py][px] == EMPTY:
            ptype = random.choice(pickup_options)
            pickups.append((ptype, py, px))

    return grid, spawn, enemies, pickups


def get_floor(floor_num):
    """Get map data for a floor. Returns (grid, spawn_pos, enemies, pickups).

    Floor 1 is hand-crafted; subsequent floors are procedurally generated.
    """
    if floor_num == 1:
        return FLOOR_1, (1, 1), FLOOR_1_ENEMIES, FLOOR_1_PICKUPS
    return generate_floor(floor_num)
