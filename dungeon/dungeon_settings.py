"""Dungeon mode constants and configuration."""


class DungeonSettings:
    # Raycaster rendering
    RENDER_WIDTH = 320
    RENDER_HEIGHT = 200
    FOV = 60  # degrees
    MAX_DEPTH = 16  # max raycast distance in tiles
    TILE_SIZE = 64  # logical tile size for calculations

    # Player
    PLAYER_SPEED = 0.05
    PLAYER_ROT_SPEED = 0.03  # radians per frame (keyboard)
    MOUSE_SENSITIVITY = 0.003
    MOUSE_SENSITIVITY_Y = 0.8  # pixels of pitch per pixel of mouse movement
    MAX_PITCH = 50  # max vertical look offset in render pixels
    PLAYER_MAX_HP = 100
    PLAYER_SIZE = 0.3  # collision radius in tile units

    # Projectile
    PROJECTILE_SPEED = 0.3  # tiles per frame
    ENEMY_PROJECTILE_SPEED = 0.15
    PROJECTILE_RADIUS = 0.15  # collision radius for hitting enemies

    # Weapons
    WEAPONS = {
        "blaster": {
            "damage": 15,
            "fire_rate": 10,  # frames between shots
            "ammo": -1,  # -1 = infinite
            "spread": 0.0,
            "projectiles": 1,
            "speed": 0.3,
            "color": (0, 200, 255),
            "name": "Blaster",
        },
        "shotgun": {
            "damage": 12,
            "fire_rate": 30,
            "ammo": 20,
            "spread": 0.15,
            "projectiles": 5,
            "speed": 0.3,
            "color": (255, 200, 50),
            "name": "Shotgun",
        },
        "plasma": {
            "damage": 25,
            "fire_rate": 15,
            "ammo": 40,
            "spread": 0.02,
            "projectiles": 1,
            "speed": 0.35,
            "color": (100, 255, 100),
            "name": "Plasma Rifle",
        },
        "rocket_launcher": {
            "damage": 80,
            "fire_rate": 50,
            "ammo": 5,
            "spread": 0.0,
            "projectiles": 1,
            "speed": 0.2,
            "color": (255, 80, 20),
            "name": "Rocket Launcher",
        },
    }

    # Enemies
    ENEMY_TYPES = {
        "lizard_grunt": {
            "hp": 30,
            "speed": 0.02,
            "damage": 10,
            "attack_range": 6.0,
            "attack_cooldown": 60,
            "detect_range": 8.0,
            "color": (40, 180, 40),
            "size": 0.4,
            "points": 100,
            "drop_chance": 0.2,
        },
        "lizard_soldier": {
            "hp": 60,
            "speed": 0.015,
            "damage": 20,
            "attack_range": 8.0,
            "attack_cooldown": 45,
            "detect_range": 10.0,
            "color": (180, 40, 40),
            "size": 0.5,
            "points": 250,
            "drop_chance": 0.35,
        },
        "lizard_brute": {
            "hp": 120,
            "speed": 0.01,
            "damage": 35,
            "attack_range": 4.0,
            "attack_cooldown": 80,
            "detect_range": 6.0,
            "color": (100, 40, 180),
            "size": 0.6,
            "points": 500,
            "drop_chance": 0.5,
        },
    }

    # Pickups
    PICKUP_TYPES = {
        "health": {"color": (255, 50, 50), "value": 25},
        "ammo": {"color": (255, 200, 50), "value": 10},
        "shotgun": {"color": (200, 150, 50), "weapon": "shotgun"},
        "plasma": {"color": (50, 255, 50), "weapon": "plasma"},
        "rocket_launcher": {"color": (255, 100, 30), "weapon": "rocket_launcher"},
    }

    # Wall colors per tile type
    WALL_COLORS = {
        1: (100, 100, 120),  # stone
        2: (80, 60, 50),  # dark rock
        3: (60, 100, 60),  # alien organic
        4: (120, 80, 80),  # metal
    }

    FLOOR_COLOR = (40, 35, 30)
    CEILING_COLOR = (20, 15, 15)

    # Exit portal color (bright green glow)
    EXIT_COLOR = (30, 255, 80)

    # HUD
    HUD_HEIGHT = 40  # pixels in render space
