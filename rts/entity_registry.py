"""Data-driven unit and building definitions.

Adding a new entity = one dict entry here + pixel art in rts_sprites.py.
"""

UNIT_DEFS = {
    # ── Human ──
    "engineer": {
        "faction": "human",
        "hp": 30,
        "speed": 1.5,
        "attack": 0,
        "attack_range": 0,
        "cost": 0,
        "can_build": True,
        "can_harvest": False,
        "vision": 5,
        "size": (1, 1),
    },
    "miner": {
        "faction": "human",
        "hp": 25,
        "speed": 1.2,
        "attack": 0,
        "attack_range": 0,
        "cost": 50,
        "can_build": False,
        "can_harvest": True,
        "harvest_rate": 10,
        "carry_capacity": 50,
        "vision": 4,
        "size": (1, 1),
    },
    "marine": {
        "faction": "human",
        "hp": 50,
        "speed": 1.8,
        "attack": 6,
        "attack_range": 5,
        "cost": 75,
        "can_build": False,
        "can_harvest": False,
        "vision": 6,
        "size": (1, 1),
    },
    "drone": {
        "faction": "lizard",
        "hp": 25,
        "speed": 1.2,
        "attack": 0,
        "attack_range": 0,
        "cost": 50,
        "can_build": False,
        "can_harvest": True,
        "harvest_rate": 10,
        "carry_capacity": 50,
        "vision": 4,
        "size": (1, 1),
    },
    # ── Cyber Lizard ──
    "scout": {
        "faction": "lizard",
        "hp": 35,
        "speed": 2.5,
        "attack": 6,
        "attack_range": 1,
        "cost": 60,
        "can_build": False,
        "can_harvest": False,
        "vision": 6,
        "size": (1, 1),
    },
    "warrior": {
        "faction": "lizard",
        "hp": 80,
        "speed": 1.2,
        "attack": 12,
        "attack_range": 1,
        "cost": 100,
        "can_build": False,
        "can_harvest": False,
        "vision": 4,
        "size": (1, 1),
    },
    "spitter": {
        "faction": "lizard",
        "hp": 40,
        "speed": 1.5,
        "attack": 7,
        "attack_range": 5,
        "cost": 80,
        "can_build": False,
        "can_harvest": False,
        "vision": 6,
        "size": (1, 1),
    },
}

BUILDING_DEFS = {
    # ── Human ──
    "main_base": {
        "faction": "human",
        "hp": 500,
        "cost": 0,
        "size": (3, 3),
        "produces": ["engineer", "miner"],
        "vision": 8,
        "crystal_capacity": 1000,
    },
    "barracks": {
        "faction": "human",
        "hp": 300,
        "cost": 200,
        "size": (2, 2),
        "produces": ["marine"],
        "vision": 6,
    },
    "turret": {
        "faction": "human",
        "hp": 150,
        "cost": 150,
        "size": (1, 1),
        "produces": [],
        "attack": 10,
        "attack_range": 6,
        "vision": 7,
    },
    "mining_camp": {
        "faction": "human",
        "hp": 150,
        "cost": 100,
        "size": (2, 2),
        "produces": [],
        "vision": 4,
        "crystal_capacity": 250,
        "is_mining_camp": True,
    },
    # ── Cyber Lizard ──
    "hive": {
        "faction": "lizard",
        "hp": 500,
        "cost": 0,
        "size": (3, 3),
        "produces": ["drone", "scout"],
        "vision": 8,
        "crystal_capacity": 1000,
    },
    "war_pit": {
        "faction": "lizard",
        "hp": 300,
        "cost": 200,
        "size": (2, 2),
        "produces": ["warrior", "spitter"],
        "vision": 6,
    },
    "spine": {
        "faction": "lizard",
        "hp": 150,
        "cost": 150,
        "size": (1, 1),
        "produces": [],
        "attack": 10,
        "attack_range": 6,
        "vision": 7,
    },
}

# Mapping: building type -> which building can produce it
PRODUCED_BY = {}
for btype, bdef in BUILDING_DEFS.items():
    for utype in bdef.get("produces", []):
        PRODUCED_BY[utype] = btype
