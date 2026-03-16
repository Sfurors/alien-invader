"""RTS mode constants and tunable values."""


class RTSSettings:
    # Map
    TILE_SIZE = 32
    MAP_WIDTH = 64
    MAP_HEIGHT = 64
    MAP_PIXEL_W = TILE_SIZE * MAP_WIDTH  # 2048
    MAP_PIXEL_H = TILE_SIZE * MAP_HEIGHT  # 2048

    # Terrain indices
    GRASS = 0
    ROCK = 1
    CRYSTAL = 2
    WATER = 3
    SAND = 4
    RUINS = 5

    CRYSTAL_PER_TILE = 350

    # Harvesting
    HARVEST_COOLDOWN = 60  # frames per mining round (1 sec at 60fps)
    BASE_CRYSTAL_CAPACITY = 1000

    # Camera
    CAMERA_SPEED = 12
    CAMERA_EDGE_MARGIN = 4  # pixels from edge to start scrolling

    # HUD
    HUD_HEIGHT = 160
    MINIMAP_SIZE = 120

    # Economy
    STARTING_CRYSTALS = 200

    # Combat
    ATTACK_COOLDOWN = 30  # frames between attacks
    TURRET_RANGE = 6  # tiles

    # AI timing (frames at 60fps)
    AI_BUILDUP_DURATION = 3600  # 60 seconds
    AI_SCOUT_INTERVAL = 600  # 10 seconds
    AI_ATTACK_INTERVAL = 5400  # 90 seconds
    AI_PRODUCE_INTERVAL = 180  # 3 seconds
    AI_SUPPLY_DROP_INTERVAL = 2700  # 45 seconds
    AI_SUPPLY_DROP_AMOUNT = 100  # crystals per drop

    # Production
    PRODUCTION_TIME = 180  # frames (3 seconds)

    # Selection
    SELECTION_COLOR = (0, 255, 0)
    ENEMY_COLOR = (255, 60, 60)

    # Fog of war
    FOG_UNEXPLORED = 0
    FOG_EXPLORED = 1
    FOG_VISIBLE = 2
    UNIT_VISION_RANGE = 5
    BUILDING_VISION_RANGE = 7

    # Terrain colors
    TERRAIN_COLORS = {
        0: (60, 120, 40),  # GRASS
        1: (100, 95, 85),  # ROCK
        2: (80, 200, 220),  # CRYSTAL
        3: (30, 60, 140),  # WATER
        4: (180, 170, 120),  # SAND
        5: (60, 55, 50),  # RUINS
    }
