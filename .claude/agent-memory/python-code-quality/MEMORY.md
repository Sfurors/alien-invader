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
  `draw_menu` still constructs an alien Surface per call (per-frame anti-pattern).
  The `victory` sound is loaded but never played — wire it or remove it.
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

## Details
See patterns.md for extended refactoring strategy notes.
