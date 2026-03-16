# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Game

```bash
python alien_invasion.py
```

Requires Python 3 and pygame (`pip install pygame`).

## Controls

| Key | Action |
|-----|--------|
| Arrow Left/Right | Move ship horizontally |
| Arrow Up/Down | Move ship vertically (bottom 1/4 of screen) |
| Space | Fire (max 3 bullets on screen) |
| Enter | Start / Restart |
| Q | Quit |

## Architecture

Pygame game following the *Python Crash Course* structure. All game state is passed explicitly between functions — no global game object.

### Entry point: `alien_invasion.py`
Creates all objects and sprite groups, owns the main loop. Game states are driven by `stats.game_active` and `stats.game_started` (both bools). Calls `gf.*` functions each frame.

### Module responsibilities

| File | Purpose |
|------|---------|
| `settings1.py` | `Settings` — all tunable constants (speeds, colors, sizes) |
| `game_stats.py` | `GameStats` — score, game state bools, `reset_stats()` |
| `ship.py` | `Ship` — loads `images/ship.bmp`, moves with boundary clamping |
| `bullet.py` | `Bullet(Sprite)` — drawn rect, moves up, self-kills off-screen |
| `alien.py` | `Alien(Sprite)` — drawn with `pygame.draw`, fleet edge detection |
| `explosion.py` | `Explosion(Sprite)` — expanding circles over 15 frames, no image file |
| `sounds.py` | Generates shoot/explosion/game-over sounds at runtime via `array` module |
| `game_functions.py` | All game logic: event handling, fleet creation/movement, collision, rendering |

### Game loop flow (active game)
```
check_events → ship.update → update_bullets → check_bullet_alien_collisions
→ (respawn fleet if empty) → update_aliens → explosions.update → update_screen
```

### Adding new features
- New settings go in `Settings.__init__` (`settings1.py`)
- New game logic functions go in `game_functions.py`
- New sprite types follow the pattern in `bullet.py`/`alien.py`: extend `pygame.sprite.Sprite`, draw on `self.image` in `__init__`, update in `update()`
- `fleet_direction` in `Settings` is mutated at runtime by `_change_fleet_direction()` — reset to `1` on game restart

### Assets
- All visuals are drawn with `pygame.draw` — no image files except `images/ship.bmp`
- All sounds are generated at startup via `sounds.load_sounds()` — no audio files
