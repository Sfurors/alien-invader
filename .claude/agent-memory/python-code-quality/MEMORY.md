# Code Quality Agent Memory — alien_invasion

## Architecture Constraints (must not be violated)
- All game state is passed explicitly between functions — no global game object.
- `Settings` is mutated at runtime: `fleet_direction` flips sign, must reset to 1 on restart.
- The monkey-patched `stats.ai_settings` noted in earlier sessions is GONE. The codebase now
  uses `GameContext` (a `@dataclass` in `game_context.py`) which holds all state. All modules
  receive `ctx` and access `ctx.settings`, `ctx.stats`, etc. explicitly. This is the correct pattern.
- Sprite groups are updated with `.update()` in `alien_invasion.py`; sprites that take
  arguments in `update()` break this convention and require wrapper functions in gf.
- Boss/level logic lives in `level.py`; `level.advance_level()` and `level.handle_boss_actions()`
  are called directly from the main loop in `alien_invasion.py`.
- The `victory` sound is registered in `sounds.load_sounds()` and in `conftest.py` mocks,
  but is never triggered in any game path — dead code that should be wired to `check_bullet_boss_collisions`
  or removed.

## Established Sprite Conventions
- Extend `pygame.sprite.Sprite`, call `super().__init__()`.
- Draw everything to `self.image` in `__init__` — never recreate the surface in `update()`.
- Use a float backing field (`_y`) for sub-pixel movement; assign `int(_y)` to `rect.y`.
- `update()` takes zero arguments — store all needed data at construction time.
- `self.kill()` for self-removal (off-screen or expired).

## Recurring Anti-Patterns Found
- Per-frame asset construction: `pygame.font.SysFont()` and `pygame.Surface` + draw calls
  inside draw/update functions that run every frame. Seen in `update_screen` (hint font),
  `draw_rocket_hud` (icon surface), `draw_menu`, and `draw_game_over` (both fonts).
  Fix: lift to module-level lazy cache or constructor; pass pre-built fonts as parameters.
- Per-frame `pygame.transform.rotate()` in `update()`: creates a new Surface every tick.
  Seen in `asteroid.py`. Fix: pre-bake a fixed rotation frame strip in `__init__` and
  advance an index in `update()`. Use `_FRAME_COUNT = 36` (every 10 degrees) as a baseline.
- Magic numeric literals in sprite constructors: e.g., `screen_rect.height * 0.25` in
  `rocket.py`, and speed/drift/spin ranges in `asteroid.py`. All tuning values belong in
  `Settings.__init__`.
- Class duplication instead of parameterisation: `RocketExplosion` is identical to
  `Explosion` except for two constants. Use a parameterised constructor + factory function.
- Business logic inside input handlers: B-key detonation loop duplicates the pattern in
  `check_rocket_detonations`. Extract a `detonate_all_rockets()` helper so both paths share
  one implementation.
- Redundant `collided` lambda in `spritecollideany`: passing `lambda s, a: s.rect.colliderect(a.rect)`
  replicates the default behaviour. Either remove it or use `pygame.sprite.collide_circle`
  when the sprite defines a `radius` attribute.

## File-Specific Notes
- `game_functions.py` has been split into `collision.py`, `renderer.py`, `events.py`,
  `fleet.py`, and `level.py`. This is a completed refactor — do not suggest merging them back.
- `level.py`: handles level progression and all boss logic (spawning, shooting, helpers).
  The `_boss_shoot` helper has a division-by-zero risk when `boss_projectile_count == 1`
  (divides by `count - 1`). Always guard this.
- `boss.py`: per-frame `draw_pixel_art()` call in `_update_color()` (every frame while alive).
  This is an O(pixels) surface redraw every tick and should be throttled or pre-baked.
  Flash effect correctly uses `_base_image` blit approach.
- `boss_projectile.py`: calls `self.screen.get_rect().width` every `update()` frame for the
  right-edge cull. Should cache `_screen_w` at construction time (same as `_screen_h`).
- `renderer.py`: `_BOSS_LABEL_FONT` lazy-init is inside a `for` loop body with `global`
  statement — works but is a code smell. Move lazy init to module level or to a helper.
  `draw_menu` constructs `item_font` and `small_font` with `pygame.font.SysFont` every frame
  (per-frame anti-pattern). Fix: pass them as parameters from `alien_invasion.py` alongside
  `title_font` and `menu_font`.
  The `victory` sound is now correctly wired in `collision.check_bullet_boss_collisions`.
- `settings1.py`: now complete for boss and level settings. Still missing:
  `asteroid_speed_min/max`, `asteroid_drift_max`, `asteroid_spin_max`.
- `explosion.py`: refactor target — parameterise `Explosion(total_frames, max_radius)` and
  replace `RocketExplosion` class with a factory function.
- `asteroid.py`: per-frame `pygame.transform.rotate()` in `update()` is still the critical fix.
- `game_stats.py`: `game_active` and `game_started` are not reset in `reset_stats()` by
  design — callers set them explicitly. This is intentional but should be documented.

## Collision Function Conventions
- Collision functions return nothing; they handle sprite removal and scoring internally.
- They always play the relevant sound directly, not via a return value.

## RTS Save/Load System (save_manager.py + entity_base.py)
- `save_manager.py` owns all serialise/deserialise logic for Chapter 2; uses a two-phase
  reconstruct: create all entities first, resolve cross-references second via `id_lookup` dict.
- Entity IDs are module-level global counter in `entity_base.py` (`_next_entity_id`).
  The counter is never reset between sessions — harmless for save/load but semantically odd
  for new-game flows.
- ID-planting technique (save counter, set to desired ID, construct, restore counter) is
  used in `_create_unit_from_save` and `_create_building_from_save`. It works but is fragile.
  Preferred fix: add `_entity_id=None` optional param to `BaseUnit.__init__` and
  `BaseBuilding.__init__` so save reconstruction bypasses the counter entirely.
- `SAVE_VERSION` is written to saves but never validated on load — false safety. Any new
  field added to serialise functions will cause `KeyError` on old saves with no version guard.
- `_write_json` now correctly uses atomic-write (tempfile + `os.replace()`). Fixed.
- `fog.state` is a plain list-of-lists and is JSON-round-trip safe. But fog dimensions
  (`width`/`height`) are not saved — mismatched map sizes between versions will cause
  index errors in `FogOfWar.reveal()` / `draw_overlay()`.

## Progress / Menu Navigation System (events.py, save_manager.py, renderer.py)
- `progress.json` is the canonical unlock store: `max_unlocked_level` (int) + `rts_unlocked` (bool).
- `MENU_ITEMS` and `_is_item_unlocked` live in `events.py`. The unlock check uses index
  arithmetic (index < 4 → level unlock, index == 4 → rts_unlocked). Adding a new menu item
  requires changing `MENU_ITEMS`, `_is_item_unlocked`, `draw_menu`, and `save_manager.unlock_rts`
  (hardcoded `4`). Suggest migrating to a `MenuItem` dataclass with an `is_unlocked` predicate.
- `menu_cursor` (in `GameStats`) is never validated at startup or on return-to-menu.
  A `validate_menu_cursor(stats, progress)` helper should be called after `load_progress()`
  and after every `game_started = False` assignment.
- `_move_cursor` and `_move_rts_cursor` both use "move first, then check" — they never
  validate the starting position. If the cursor starts on a locked item, it is never corrected.
- `check_events` and `draw_menu` accept `progress=None` with a fallback `load_progress()`
  disk read — this is a silent per-frame I/O path if callers omit the argument. Should be
  made a required parameter.
- `unlock_next_level` is called with `ctx.stats.level` *after* increment, so the argument is
  the level the player advanced *to*, not the one they beat. The docstring says "after beating
  a level". This off-by-one is currently harmless but is a conceptual mismatch to watch.
- `progress` is reloaded from disk in five places in `alien_invasion.py`. These are all
  intentional transition points (return to menu, pause-to-menu, RTS exit). A `ProgressCache`
  wrapper with an explicit `refresh()` method would make this intent cleaner.
- `_DEFAULT_PROGRESS` dict in `save_manager.py` is missing `"version"` key — `load_progress()`
  can return a dict without a version field when no save file exists, which is harmless today
  because version is never validated on load, but inconsistent.

## RTS AI Memory System (ai_memory.py + ai.py)
- `AIMemory` is a clean, single-responsibility class: no side effects on game state.
- `last_hit_frame` in `entity_base.py` is a *counter starting at 0 and incrementing*,
  NOT an absolute frame number. The name is misleading. `_find_threat` checks `< 120`
  (2 seconds), which is correct, but any code that computes `current_frame - last_hit_frame`
  would be wrong. Track this naming debt.
- `_do_scout()` in `ai.py` has a `break` inside the unit-iteration loop that was intended
  to prevent double scout assignment but also skips enemy-engagement for all subsequent
  units. Fixed by replacing `break` with a `scout_assigned` flag.
- `AIMemory.update_sightings()` only adds sightings, never removes dead entities. Stale
  sightings for killed entities survive until `decay_knowledge` runs (5-min default window).
  `purge_dead(rts_ctx)` method needed — call it every frame or inside `update_sightings`.
- `AIMemory.reset_visible()` iterates the full 192×192 tile grid every frame (36,864 ops).
  Fix: track a `_visible_tiles: set` and only clear those tiles. 10-50× cheaper.
- `SECTOR_SIZE = 24` lives as a class constant on `AIMemory` but is a tuning param;
  should move to `RTSSettings` as `AI_SECTOR_SIZE`.
- `stale_threshold=3600` default in `decay_knowledge` should be `S.AI_SIGHTING_STALE_THRESHOLD`.
- In `_manage_drones`, `unit.harvesting`, `unit.harvest_target`, and
  `unit.harvest_resource_type` are assigned before `find_path` returns, then re-assigned
  inside `if path:`. The pre-path assignments are redundant and can leave the unit in a
  broken harvesting state with no path if no path is found.

## Details
See patterns.md for extended refactoring strategy notes.
