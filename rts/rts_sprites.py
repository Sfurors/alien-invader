"""Pixel art maps for all RTS entities.

Each sprite is defined as (pixel_map, palette, pixel_size).
Uses the same format as pixel_art.draw_pixel_art().
"""

# ── Human faction ──────────────────────────────────────────────────

ENGINEER_PS = 3
ENGINEER_PALETTE = {
    1: (200, 160, 120),  # skin
    2: (60, 100, 180),  # blue suit
    3: (40, 70, 140),  # suit dark
    4: (220, 200, 50),  # helmet yellow
    5: (50, 50, 60),  # tool
}
ENGINEER_MAP = [
    [0, 4, 4, 4, 0],
    [0, 4, 1, 4, 0],
    [0, 0, 1, 0, 0],
    [5, 2, 2, 2, 0],
    [0, 2, 2, 2, 0],
    [0, 3, 0, 3, 0],
]

MINER_PS = 3
MINER_PALETTE = {
    1: (200, 160, 120),  # skin
    2: (180, 140, 50),  # orange suit
    3: (140, 100, 30),  # suit dark
    4: (220, 200, 50),  # helmet
    5: (160, 160, 170),  # pickaxe
}
MINER_MAP = [
    [0, 4, 4, 4, 0],
    [0, 4, 1, 4, 0],
    [0, 0, 1, 0, 0],
    [5, 2, 2, 2, 0],
    [5, 2, 2, 2, 0],
    [0, 3, 0, 3, 0],
]

MARINE_PS = 3
MARINE_PALETTE = {
    1: (200, 160, 120),  # skin
    2: (60, 80, 50),  # camo green
    3: (80, 110, 65),  # camo light
    4: (50, 60, 50),  # helmet
    5: (120, 120, 130),  # gun
}
MARINE_MAP = [
    [0, 4, 4, 4, 0],
    [0, 4, 1, 4, 0],
    [0, 0, 1, 0, 0],
    [0, 2, 3, 2, 5],
    [0, 2, 3, 2, 5],
    [0, 2, 0, 2, 0],
]

MAIN_BASE_PS = 3
MAIN_BASE_PALETTE = {
    1: (160, 160, 170),  # metal
    2: (120, 120, 130),  # metal dark
    3: (200, 200, 210),  # metal light
    4: (0, 180, 80),  # green light
    5: (60, 60, 70),  # door
}
MAIN_BASE_MAP = [
    [0, 0, 3, 3, 3, 3, 3, 3, 0, 0],
    [0, 3, 1, 1, 1, 1, 1, 1, 3, 0],
    [3, 1, 1, 4, 1, 1, 4, 1, 1, 3],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 2, 1, 1, 5, 5, 1, 1, 2, 1],
    [1, 2, 1, 1, 5, 5, 1, 1, 2, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
]

BARRACKS_PS = 3
BARRACKS_PALETTE = {
    1: (100, 100, 110),  # metal dark
    2: (140, 140, 150),  # metal
    3: (180, 60, 40),  # red stripe
    4: (60, 60, 70),  # door
    5: (220, 220, 50),  # light
}
BARRACKS_MAP = [
    [0, 2, 2, 2, 2, 2, 2, 0],
    [2, 2, 3, 3, 3, 3, 2, 2],
    [2, 1, 2, 5, 5, 2, 1, 2],
    [2, 1, 2, 2, 2, 2, 1, 2],
    [2, 1, 2, 4, 4, 2, 1, 2],
    [1, 1, 1, 4, 4, 1, 1, 1],
]

TURRET_PS = 3
TURRET_PALETTE = {
    1: (120, 120, 130),  # base
    2: (80, 80, 90),  # base dark
    3: (160, 160, 170),  # barrel
    4: (255, 100, 30),  # muzzle flash
}
TURRET_MAP = [
    [0, 0, 3, 3, 0, 0],
    [0, 0, 3, 3, 0, 0],
    [0, 1, 1, 1, 1, 0],
    [1, 1, 1, 1, 1, 1],
    [2, 1, 1, 1, 1, 2],
    [2, 2, 2, 2, 2, 2],
]

MINING_CAMP_PS = 3
MINING_CAMP_PALETTE = {
    1: (140, 120, 80),  # wood
    2: (110, 90, 60),  # wood dark
    3: (170, 150, 100),  # wood light
    4: (80, 200, 220),  # crystal accent
    5: (60, 60, 70),  # metal
}
MINING_CAMP_MAP = [
    [0, 3, 3, 3, 3, 3, 3, 0],
    [3, 1, 1, 4, 4, 1, 1, 3],
    [1, 1, 5, 1, 1, 5, 1, 1],
    [1, 2, 1, 1, 1, 1, 2, 1],
    [1, 2, 1, 4, 4, 1, 2, 1],
    [2, 2, 2, 2, 2, 2, 2, 2],
]

CART_PS = 3
CART_PALETTE = {
    1: (140, 120, 80),  # wood
    2: (110, 90, 60),  # wood dark
    3: (80, 200, 220),  # crystal glow
    4: (80, 80, 90),  # wheel
}
CART_MAP = [
    [0, 3, 3, 3, 0],
    [1, 3, 3, 3, 1],
    [1, 1, 1, 1, 1],
    [2, 2, 2, 2, 2],
    [4, 0, 0, 0, 4],
]

# ── Cyber Lizard faction ──────────────────────────────────────────

DRONE_PS = 3
DRONE_PALETTE = {
    1: (100, 120, 110),  # metal body
    2: (140, 160, 150),  # highlight
    3: (80, 200, 220),  # crystal glow (carrying indicator)
    4: (60, 70, 65),  # dark
    5: (180, 200, 50),  # circuit glow
}
DRONE_MAP = [
    [0, 0, 2, 2, 0],
    [0, 1, 5, 1, 0],
    [4, 1, 1, 1, 0],
    [0, 1, 1, 1, 0],
    [0, 4, 0, 4, 0],
    [4, 4, 0, 4, 4],
]

SCOUT_PS = 3
SCOUT_PALETTE = {
    1: (100, 120, 130),  # metal body
    2: (140, 160, 170),  # highlight
    3: (255, 30, 30),  # red eye
    4: (60, 70, 80),  # dark
    5: (180, 200, 50),  # circuit glow
}
SCOUT_MAP = [
    [0, 0, 0, 2, 1, 0],
    [0, 0, 1, 3, 2, 0],
    [4, 1, 1, 5, 1, 0],
    [0, 1, 1, 1, 1, 0],
    [0, 4, 0, 0, 4, 0],
    [4, 4, 0, 4, 4, 0],
]

WARRIOR_PS = 3
WARRIOR_PALETTE = {
    1: (80, 100, 110),  # heavy armor
    2: (120, 140, 150),  # highlight
    3: (255, 30, 30),  # eye
    4: (50, 60, 70),  # dark armor
    5: (180, 200, 50),  # circuit
    6: (200, 60, 40),  # claw
}
WARRIOR_MAP = [
    [0, 0, 0, 2, 1, 0, 0],
    [0, 0, 1, 3, 2, 1, 0],
    [4, 1, 1, 5, 1, 1, 0],
    [6, 1, 4, 1, 4, 1, 6],
    [0, 1, 1, 1, 1, 1, 0],
    [0, 4, 0, 0, 0, 4, 0],
    [4, 4, 0, 0, 4, 4, 0],
]

SPITTER_PS = 3
SPITTER_PALETTE = {
    1: (90, 110, 100),  # body
    2: (130, 150, 140),  # highlight
    3: (255, 30, 30),  # eye
    4: (50, 60, 55),  # dark
    5: (100, 220, 50),  # acid green
}
SPITTER_MAP = [
    [0, 0, 0, 2, 1, 0],
    [0, 0, 1, 3, 2, 5],
    [4, 1, 1, 1, 1, 5],
    [0, 1, 1, 1, 1, 0],
    [0, 4, 0, 0, 4, 0],
    [4, 4, 0, 4, 4, 0],
]

HIVE_PS = 3
HIVE_PALETTE = {
    1: (80, 70, 60),  # organic base
    2: (110, 100, 80),  # organic light
    3: (60, 50, 40),  # dark
    4: (180, 200, 50),  # glow
    5: (255, 30, 30),  # eye
}
HIVE_MAP = [
    [0, 0, 0, 2, 2, 2, 2, 0, 0, 0],
    [0, 0, 2, 1, 1, 1, 1, 2, 0, 0],
    [0, 2, 1, 4, 1, 1, 4, 1, 2, 0],
    [2, 1, 1, 1, 5, 5, 1, 1, 1, 2],
    [2, 1, 3, 1, 1, 1, 1, 3, 1, 2],
    [2, 1, 3, 1, 1, 1, 1, 3, 1, 2],
    [2, 3, 3, 1, 4, 4, 1, 3, 3, 2],
    [3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
]

WAR_PIT_PS = 3
WAR_PIT_PALETTE = {
    1: (70, 60, 50),  # dark organic
    2: (100, 90, 70),  # organic
    3: (50, 40, 30),  # very dark
    4: (200, 50, 30),  # lava/energy
    5: (180, 200, 50),  # glow
}
WAR_PIT_MAP = [
    [0, 2, 2, 2, 2, 2, 2, 0],
    [2, 1, 1, 5, 5, 1, 1, 2],
    [2, 1, 4, 4, 4, 4, 1, 2],
    [2, 1, 4, 3, 3, 4, 1, 2],
    [2, 1, 4, 4, 4, 4, 1, 2],
    [3, 3, 1, 1, 1, 1, 3, 3],
]

SPINE_PS = 3
SPINE_PALETTE = {
    1: (80, 70, 60),  # organic base
    2: (120, 100, 80),  # spike
    3: (60, 50, 40),  # dark
    4: (200, 50, 30),  # tip glow
}
SPINE_MAP = [
    [0, 0, 4, 4, 0, 0],
    [0, 0, 2, 2, 0, 0],
    [0, 2, 2, 2, 2, 0],
    [0, 1, 1, 1, 1, 0],
    [1, 1, 1, 1, 1, 1],
    [3, 3, 3, 3, 3, 3],
]

# ── Isotope buildings ────────────────────────────────────────────

ISOTOPE_EXTRACTOR_PS = 3
ISOTOPE_EXTRACTOR_PALETTE = {
    1: (140, 140, 150),  # metal
    2: (110, 110, 120),  # metal dark
    3: (170, 170, 180),  # metal light
    4: (50, 220, 80),  # green glow
    5: (60, 60, 70),  # pipe
}
ISOTOPE_EXTRACTOR_MAP = [
    [0, 3, 3, 3, 3, 3, 3, 0],
    [3, 1, 4, 1, 1, 4, 1, 3],
    [1, 1, 5, 4, 4, 5, 1, 1],
    [1, 2, 5, 1, 1, 5, 2, 1],
    [1, 2, 1, 4, 4, 1, 2, 1],
    [2, 2, 2, 2, 2, 2, 2, 2],
]

ISOTOPE_SIPHON_PS = 3
ISOTOPE_SIPHON_PALETTE = {
    1: (70, 60, 50),  # organic base
    2: (100, 90, 70),  # organic light
    3: (50, 40, 30),  # dark
    4: (50, 220, 80),  # green bio-glow
    5: (30, 180, 60),  # darker green
}
ISOTOPE_SIPHON_MAP = [
    [0, 2, 2, 2, 2, 2, 2, 0],
    [2, 1, 4, 1, 1, 4, 1, 2],
    [2, 1, 5, 4, 4, 5, 1, 2],
    [2, 1, 1, 5, 5, 1, 1, 2],
    [2, 3, 1, 4, 4, 1, 3, 2],
    [3, 3, 3, 3, 3, 3, 3, 3],
]

# ── Crystal resource sprite ───────────────────────────────────────

CRYSTAL_PS = 3
CRYSTAL_PALETTE = {
    1: (60, 180, 220),  # crystal light
    2: (40, 140, 180),  # crystal mid
    3: (20, 100, 140),  # crystal dark
    4: (200, 240, 255),  # sparkle
}
CRYSTAL_MAP = [
    [0, 0, 4, 0, 0],
    [0, 1, 1, 1, 0],
    [1, 2, 1, 2, 1],
    [0, 2, 3, 2, 0],
    [0, 0, 3, 0, 0],
]

# ── Registry helpers ──────────────────────────────────────────────


def get_sprite_data(entity_type):
    """Return (pixel_map, palette, pixel_size) for a given entity type string."""
    _SPRITES = {
        "engineer": (ENGINEER_MAP, ENGINEER_PALETTE, ENGINEER_PS),
        "miner": (MINER_MAP, MINER_PALETTE, MINER_PS),
        "marine": (MARINE_MAP, MARINE_PALETTE, MARINE_PS),
        "main_base": (MAIN_BASE_MAP, MAIN_BASE_PALETTE, MAIN_BASE_PS),
        "barracks": (BARRACKS_MAP, BARRACKS_PALETTE, BARRACKS_PS),
        "turret": (TURRET_MAP, TURRET_PALETTE, TURRET_PS),
        "mining_camp": (MINING_CAMP_MAP, MINING_CAMP_PALETTE, MINING_CAMP_PS),
        "cart": (CART_MAP, CART_PALETTE, CART_PS),
        "drone": (DRONE_MAP, DRONE_PALETTE, DRONE_PS),
        "scout": (SCOUT_MAP, SCOUT_PALETTE, SCOUT_PS),
        "warrior": (WARRIOR_MAP, WARRIOR_PALETTE, WARRIOR_PS),
        "spitter": (SPITTER_MAP, SPITTER_PALETTE, SPITTER_PS),
        "hive": (HIVE_MAP, HIVE_PALETTE, HIVE_PS),
        "war_pit": (WAR_PIT_MAP, WAR_PIT_PALETTE, WAR_PIT_PS),
        "spine": (SPINE_MAP, SPINE_PALETTE, SPINE_PS),
        "isotope_extractor": (
            ISOTOPE_EXTRACTOR_MAP,
            ISOTOPE_EXTRACTOR_PALETTE,
            ISOTOPE_EXTRACTOR_PS,
        ),
        "isotope_siphon": (
            ISOTOPE_SIPHON_MAP,
            ISOTOPE_SIPHON_PALETTE,
            ISOTOPE_SIPHON_PS,
        ),
        "crystal": (CRYSTAL_MAP, CRYSTAL_PALETTE, CRYSTAL_PS),
    }
    return _SPRITES.get(entity_type)
