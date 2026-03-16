# Extended Pattern Notes — alien_invasion

## Per-Frame Asset Construction (Critical recurring issue)
Any call to `pygame.font.SysFont()`, `pygame.Surface()`, or a series of `pygame.draw.*`
calls that produces a static image inside a function called every frame is a performance bug.

Resolution hierarchy:
1. If the asset is global/stateless: module-level constant after pygame.init() via lazy init.
2. If the asset depends on constructor args: store on `self` in `__init__`.
3. If the asset must be passed in: create once in `alien_invasion.py` alongside `score_font`
   and pass as a parameter.

## Parameterised Explosion Pattern
Replace class hierarchies that differ only in constants with a single class + factory:

    class Explosion(pygame.sprite.Sprite):
        def __init__(self, screen, center, total_frames=15, max_radius=28): ...

    def RocketExplosion(screen, center):
        return Explosion(screen, center, total_frames=25, max_radius=80)

The factory function keeps existing import and call sites unchanged.

## Zero-Argument update() Convention
All sprites in this project call self.kill() and move based on data stored at __init__ time.
WeaponDrop broke this by accepting (ai_settings, screen) in update(). The fix:

    # In __init__:
    self._drop_speed = drop_speed        # passed from ai_settings.drop_speed at creation
    self._screen_bottom = screen.get_rect().bottom

    # In update():
    def update(self):  # zero args

This lets alien_invasion.py call drops.update() directly like every other group,
and eliminates the update_drops() wrapper in game_functions.py.

## Input Handler Purity
Key handlers should read input and call domain functions — they should not contain loops
or conditional business logic. When the B-key handler contains the detonation loop,
that loop is duplicated with check_rocket_detonations. Extract:

    def detonate_all_rockets(ai_settings, screen, stats, rockets, aliens, explosions, sounds):
        for rocket in list(rockets.sprites()):
            _detonate_rocket(ai_settings, screen, stats, rocket, aliens, explosions, sounds)

Both the key handler and check_rocket_detonations then call this single function.

## Pre-Baked Rotation Frames (Asteroid / spinning sprite pattern)
Never call `pygame.transform.rotate()` inside `update()` — it allocates a new Surface every
tick. Instead, pre-bake a frame strip at construction time and advance an index:

    _FRAME_COUNT = 36  # one frame every 10 degrees — smooth enough for small sprites

    class Asteroid(pygame.sprite.Sprite):
        def __init__(self, screen_w, screen_h):
            base = self._make_image(size)
            self._frames = [
                pygame.transform.rotate(base, 360 * i / _FRAME_COUNT)
                for i in range(_FRAME_COUNT)
            ]
            self._frame_index = 0
            self.image = self._frames[0]
            ...

        def update(self):
            self._frame_index = (self._frame_index + 1) % _FRAME_COUNT
            self.image = self._frames[self._frame_index]
            self.rect = self.image.get_rect(center=(int(self._x), int(self._y)))

For 10 asteroids at 60 fps this avoids ~600 Surface allocations/second.

## Passing Pre-Built Fonts to draw_menu / draw_game_over
Both screen-render functions construct fonts per-frame. Pattern to follow:
- Create fonts once in `alien_invasion.py` alongside `score_font`.
- Pass them as parameters: `draw_menu(screen, ai_settings, bg, title_font, sub_font)`.
- This is consistent with how `score_font` and `hint_font` are already handled.

## Future Extensibility: WeaponSystem
When a third weapon type is added, the key handler branching and HUD rendering in
game_functions.py will become unwieldy. At that point, consider a WeaponSystem class:
- Owns rocket count (currently stats.rockets)
- Provides fire() and detonate() methods
- Owns its own HUD draw method
- Decouples weapon logic from the event handler and from GameStats
