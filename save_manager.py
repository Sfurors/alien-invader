"""Save/Load manager for both Chapter 1 (Space Invaders) and Chapter 2 (RTS)."""

import json
import os
import tempfile

_SAVE_DIR = os.path.dirname(os.path.abspath(__file__))
_CH1_FILE = os.path.join(_SAVE_DIR, "save_chapter1.json")
_CH2_FILE = os.path.join(_SAVE_DIR, "save_chapter2.json")
_DUNGEON_FILE = os.path.join(_SAVE_DIR, "save_dungeon.json")
_PROGRESS_FILE = os.path.join(_SAVE_DIR, "progress.json")

SAVE_VERSION = 1

_DEFAULT_PROGRESS = {"max_unlocked_level": 1, "rts_unlocked": False, "dungeon_unlocked": False}


# ── Progress (level unlock) ──────────────────────────────────


def load_progress():
    """Load progress.json, migrating from old Ch1 save if needed."""
    data = _read_json(_PROGRESS_FILE)
    if data is not None:
        return data
    # Migrate from old Ch1 save if it exists
    old = _read_json(_CH1_FILE)
    if old and "level" in old:
        progress = {
            "version": SAVE_VERSION,
            "max_unlocked_level": max(1, old["level"]),
            "rts_unlocked": False,
        }
        _write_json(_PROGRESS_FILE, progress)
        return progress
    return dict(_DEFAULT_PROGRESS)


def save_progress(max_unlocked_level, rts_unlocked, dungeon_unlocked=None):
    if dungeon_unlocked is None:
        dungeon_unlocked = load_progress().get("dungeon_unlocked", False)
    data = {
        "version": SAVE_VERSION,
        "max_unlocked_level": max_unlocked_level,
        "rts_unlocked": rts_unlocked,
        "dungeon_unlocked": dungeon_unlocked,
    }
    _write_json(_PROGRESS_FILE, data)


def unlock_next_level(level):
    """Ensure `level` is unlocked in progress. Called after beating a level."""
    progress = load_progress()
    if level > progress.get("max_unlocked_level", 1):
        progress["max_unlocked_level"] = level
        save_progress(
            progress["max_unlocked_level"], progress.get("rts_unlocked", False)
        )


def unlock_rts():
    """Mark RTS mode as unlocked. Called after beating the boss."""
    progress = load_progress()
    progress["rts_unlocked"] = True
    progress["max_unlocked_level"] = max(progress.get("max_unlocked_level", 1), 4)
    save_progress(progress["max_unlocked_level"], True)


def unlock_dungeon():
    """Mark Dungeon mode as unlocked. Called after beating RTS."""
    progress = load_progress()
    progress["dungeon_unlocked"] = True
    save_progress(
        progress["max_unlocked_level"],
        progress.get("rts_unlocked", False),
        dungeon_unlocked=True,
    )


# ── Chapter 3 (Dungeon) ─────────────────────────────────────


def has_dungeon_save():
    return os.path.isfile(_DUNGEON_FILE)


def get_dungeon_unlocked_floors():
    """Return sorted list of floor numbers the player has unlocked."""
    data = _read_json(_DUNGEON_FILE)
    if not data or "unlocked_floors" not in data:
        return []
    return sorted(data["unlocked_floors"])


def unlock_dungeon_floor(floor_num):
    """Mark a floor as unlocked. Called after completing the previous floor."""
    data = _read_json(_DUNGEON_FILE) or {"version": SAVE_VERSION, "unlocked_floors": []}
    floors = set(data.get("unlocked_floors", []))
    floors.add(floor_num)
    data["unlocked_floors"] = sorted(floors)
    _write_json(_DUNGEON_FILE, data)


def delete_dungeon_saves():
    if os.path.isfile(_DUNGEON_FILE):
        os.remove(_DUNGEON_FILE)


# ── Chapter 2 ────────────────────────────────────────────────


def has_chapter2_save():
    return os.path.isfile(_CH2_FILE)


def save_chapter2(rts_mode):
    from rts.entity_base import _get_next_entity_id

    rts_ctx = rts_mode.rts_ctx
    state = rts_mode.state
    ai = rts_mode.ai
    fog = rts_mode.fog
    camera = rts_ctx.camera
    tile_map = rts_ctx.tile_map

    data = {
        "version": SAVE_VERSION,
        "next_entity_id": _get_next_entity_id(),
        "rts_state": _serialize_rts_state(state),
        "camera": {"x": camera.x, "y": camera.y},
        "ai": _serialize_ai(ai),
        "tile_map": _serialize_tile_map(tile_map),
        "fog": fog.state,
        "player_spawn": getattr(rts_mode, "player_spawn", None),
        "enemy_spawn": getattr(rts_mode, "enemy_spawn", None),
        "player_units": [_serialize_unit(u) for u in rts_ctx.player_units],
        "player_buildings": [_serialize_building(b) for b in rts_ctx.player_buildings],
        "enemy_units": [_serialize_unit(u) for u in rts_ctx.enemy_units],
        "enemy_buildings": [_serialize_building(b) for b in rts_ctx.enemy_buildings],
    }
    _write_json(_CH2_FILE, data)


def load_chapter2():
    return _read_json(_CH2_FILE)


def delete_chapter2_save():
    if os.path.isfile(_CH2_FILE):
        os.remove(_CH2_FILE)


def reconstruct_rts(rts_mode, save_data):
    """Rebuild all RTS state from save_data dict."""
    from rts.entity_base import BaseUnit, BaseBuilding, _set_next_entity_id

    rts_ctx = rts_mode.rts_ctx
    state = rts_mode.state
    ai = rts_mode.ai
    fog = rts_mode.fog
    camera = rts_ctx.camera
    tile_map = rts_ctx.tile_map

    # 1. Clear all sprite groups
    rts_ctx.player_units.empty()
    rts_ctx.player_buildings.empty()
    rts_ctx.enemy_units.empty()
    rts_ctx.enemy_buildings.empty()
    rts_ctx.all_entities.empty()
    rts_ctx.projectiles.empty()

    # 2. Restore tile map
    tm = save_data["tile_map"]
    tile_map.tiles = tm["tiles"]
    tile_map.crystal = tm["crystal"]
    tile_map.isotope = tm["isotope"]

    # 3. Restore fog
    fog.state = save_data["fog"]

    # 4. Restore camera
    camera.x = save_data["camera"]["x"]
    camera.y = save_data["camera"]["y"]

    # 5. Restore RTSState scalars
    _restore_rts_state(state, save_data["rts_state"])

    # 6. Restore AI
    _restore_ai(ai, save_data["ai"])

    # 7. Reset entity ID counter
    _set_next_entity_id(save_data["next_entity_id"])

    # 8. Create all entities
    id_lookup = {}

    for ud in save_data["player_units"]:
        unit = _create_unit_from_save(ud)
        rts_ctx.player_units.add(unit)
        rts_ctx.all_entities.add(unit)
        id_lookup[ud["id"]] = unit

    for ud in save_data["enemy_units"]:
        unit = _create_unit_from_save(ud)
        rts_ctx.enemy_units.add(unit)
        rts_ctx.all_entities.add(unit)
        id_lookup[ud["id"]] = unit

    for bd in save_data["player_buildings"]:
        building = _create_building_from_save(bd, tile_map)
        rts_ctx.player_buildings.add(building)
        rts_ctx.all_entities.add(building)
        id_lookup[bd["id"]] = building

    for bd in save_data["enemy_buildings"]:
        building = _create_building_from_save(bd, tile_map)
        rts_ctx.enemy_buildings.add(building)
        rts_ctx.all_entities.add(building)
        id_lookup[bd["id"]] = building

    # 9. Resolve cross-references
    for ud in save_data["player_units"] + save_data["enemy_units"]:
        unit = id_lookup[ud["id"]]
        _resolve_unit_refs(unit, ud, id_lookup)

    for bd in save_data["player_buildings"] + save_data["enemy_buildings"]:
        building = id_lookup[bd["id"]]
        _resolve_building_refs(building, bd, id_lookup)

    # 10. Resolve AI attack_target
    ai_target_id = save_data["ai"].get("attack_target_id")
    if ai_target_id is not None:
        ai.attack_target = id_lookup.get(ai_target_id)

    # Restore spawn positions (migration: old saves may lack these)
    ps = save_data.get("player_spawn")
    rts_mode.player_spawn = tuple(ps) if ps else (2, 2)
    es = save_data.get("enemy_spawn")
    rts_mode.enemy_spawn = tuple(es) if es else (186, 186)

    # Clear selection state (not saved)
    state.clear_selection()


# ── Serialization helpers ─────────────────────────────────────


def _serialize_rts_state(state):
    return {
        "crystals": state.crystals,
        "isotope": state.isotope,
        "frame": state.frame,
        "game_over": state.game_over,
        "victory": state.victory,
        "minimap_alerts": state.minimap_alerts,
    }


def _restore_rts_state(state, d):
    state.crystals = d["crystals"]
    state.isotope = d["isotope"]
    state.frame = d["frame"]
    state.game_over = d["game_over"]
    state.victory = d["victory"]
    state.minimap_alerts = d["minimap_alerts"]


def _serialize_ai(ai):
    return {
        "state": ai.state,
        "frame": ai.frame,
        "crystals": ai.crystals,
        "isotope": ai.isotope,
        "last_produce_frame": ai.last_produce_frame,
        "last_attack_frame": ai.last_attack_frame,
        "attack_target_id": _get_entity_id(ai.attack_target),
        "defend_target": ai.defend_target,
        "has_war_pit": ai.has_war_pit,
        "has_isotope_siphon": ai.has_isotope_siphon,
        "last_supply_drop": ai.last_supply_drop,
        "supply_drop_count": ai.supply_drop_count,
        "desired_drones": ai.desired_drones,
        "memory": _serialize_ai_memory(ai.memory),
    }


def _serialize_ai_memory(memory):
    return {
        "fog": memory.fog,
        "sightings": memory.sightings,
        "last_known_base": memory.last_known_base,
        "scouted_sectors": [list(s) for s in memory.scouted_sectors],
    }


def _restore_ai(ai, d):
    ai.state = d["state"]
    ai.frame = d["frame"]
    ai.crystals = d["crystals"]
    ai.isotope = d["isotope"]
    ai.last_produce_frame = d["last_produce_frame"]
    ai.last_attack_frame = d["last_attack_frame"]
    # attack_target resolved later via id_lookup
    ai.defend_target = d["defend_target"]
    if ai.defend_target is not None:
        ai.defend_target = tuple(ai.defend_target)
    ai.has_war_pit = d["has_war_pit"]
    ai.has_isotope_siphon = d["has_isotope_siphon"]
    ai.last_supply_drop = d["last_supply_drop"]
    ai.supply_drop_count = d.get("supply_drop_count", 0)
    ai.desired_drones = d["desired_drones"]
    # Restore AI memory (migration: old saves won't have it)
    mem_data = d.get("memory")
    if mem_data:
        _restore_ai_memory(ai.memory, mem_data)


def _restore_ai_memory(memory, d):
    memory.fog = d["fog"]
    memory.sightings = d.get("sightings", {})
    lkb = d.get("last_known_base")
    memory.last_known_base = tuple(lkb) if lkb else None
    memory.scouted_sectors = {tuple(s) for s in d.get("scouted_sectors", [])}


def _serialize_tile_map(tile_map):
    return {
        "tiles": tile_map.tiles,
        "crystal": tile_map.crystal,
        "isotope": tile_map.isotope,
    }


def _get_entity_id(entity):
    if entity is None:
        return None
    return getattr(entity, "entity_id", None)


def _serialize_unit(unit):
    return {
        "id": unit.entity_id,
        "unit_type": unit.unit_type,
        "faction": unit.faction,
        "tile_x": unit.tile_x,
        "tile_y": unit.tile_y,
        "px": unit.px,
        "py": unit.py,
        "hp": unit.hp,
        "path": unit.path,
        "moving": unit.moving,
        "attack_target_id": _get_entity_id(unit.attack_target),
        "attack_cooldown": unit.attack_cooldown,
        "carrying": unit.carrying,
        "carrying_isotope": unit.carrying_isotope,
        "harvest_target": unit.harvest_target,
        "return_target_id": _get_entity_id(unit.return_target),
        "harvesting": unit.harvesting,
        "returning": unit.returning,
        "harvest_timer": unit.harvest_timer,
        "harvest_resource_type": unit.harvest_resource_type,
        "build_target_id": _get_entity_id(unit.build_target),
        "building": unit.building,
        "assigned_camp_id": _get_entity_id(unit.assigned_camp),
        "assigned_isotope_camp_id": _get_entity_id(unit.assigned_isotope_camp),
        "caravan_mode": unit.caravan_mode,
        "scout_mode": unit.scout_mode,
        "scout_timer": unit.scout_timer,
    }


def _serialize_building(building):
    return {
        "id": building.entity_id,
        "building_type": building.building_type,
        "faction": building.faction,
        "tile_x": building.tile_x,
        "tile_y": building.tile_y,
        "px": building.px,
        "py": building.py,
        "hp": building.hp,
        "under_construction": building.under_construction,
        "build_progress": building.build_progress,
        "build_time": building.build_time,
        "production_queue": list(building.production_queue),
        "production_timer": building.production_timer,
        "stored_crystals": building.stored_crystals,
        "stored_isotope": building.stored_isotope,
        "attack_target_id": _get_entity_id(building.attack_target),
        "attack_cooldown": building.attack_cooldown,
        "rally_x": building.rally_x,
        "rally_y": building.rally_y,
    }


def _create_unit_from_save(ud):
    from rts.entity_base import BaseUnit

    unit = BaseUnit(
        ud["unit_type"],
        ud["tile_x"],
        ud["tile_y"],
        ud["faction"],
        _entity_id=ud["id"],
    )

    unit.px = ud["px"]
    unit.py = ud["py"]
    unit.hp = ud["hp"]
    unit.path = [tuple(p) if isinstance(p, list) else p for p in ud["path"]]
    unit.moving = ud["moving"]
    unit.attack_cooldown = ud["attack_cooldown"]
    unit.carrying = ud["carrying"]
    unit.carrying_isotope = ud["carrying_isotope"]
    if ud["harvest_target"] is not None:
        unit.harvest_target = tuple(ud["harvest_target"])
    else:
        unit.harvest_target = None
    unit.harvesting = ud["harvesting"]
    unit.returning = ud["returning"]
    unit.harvest_timer = ud["harvest_timer"]
    unit.harvest_resource_type = ud["harvest_resource_type"]
    unit.building = ud["building"]
    unit.caravan_mode = ud["caravan_mode"]
    unit.scout_mode = ud["scout_mode"]
    unit.scout_timer = ud["scout_timer"]
    # Update rect position
    unit.rect.center = (int(unit.px), int(unit.py))
    return unit


def _create_building_from_save(bd, tile_map):
    from rts.entity_base import BaseBuilding

    building = BaseBuilding(
        bd["building_type"],
        bd["tile_x"],
        bd["tile_y"],
        bd["faction"],
        _entity_id=bd["id"],
    )

    building.px = bd["px"]
    building.py = bd["py"]
    building.hp = bd["hp"]
    building.under_construction = bd["under_construction"]
    building.build_progress = bd["build_progress"]
    building.build_time = bd["build_time"]
    building.production_queue = list(bd["production_queue"])
    building.production_timer = bd["production_timer"]
    building.stored_crystals = bd["stored_crystals"]
    building.stored_isotope = bd["stored_isotope"]
    building.attack_cooldown = bd["attack_cooldown"]
    building.rally_x = bd["rally_x"]
    building.rally_y = bd["rally_y"]
    building.tile_map = tile_map
    # Update damage visuals
    if building.max_hp > 0:
        ratio = building.hp / building.max_hp
        if ratio < 0.33:
            building.image = building.image_damaged2
        elif ratio < 0.66:
            building.image = building.image_damaged1
    building.rect.topleft = (building.px, building.py)
    return building


def _resolve_unit_refs(unit, ud, id_lookup):
    unit.attack_target = id_lookup.get(ud["attack_target_id"])
    unit.return_target = id_lookup.get(ud["return_target_id"])
    unit.build_target = id_lookup.get(ud["build_target_id"])
    unit.assigned_camp = id_lookup.get(ud["assigned_camp_id"])
    unit.assigned_isotope_camp = id_lookup.get(ud["assigned_isotope_camp_id"])


def _resolve_building_refs(building, bd, id_lookup):
    building.attack_target = id_lookup.get(bd["attack_target_id"])


# ── File I/O ──────────────────────────────────────────────────


def _write_json(path, data):
    fd, tmp = tempfile.mkstemp(dir=_SAVE_DIR, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _read_json(path):
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None
