import pygame
from pixel_art import draw_pixel_art

_PIXEL_SIZE = 4

# 38 cols x 25 rows x 4 = 152 x 100 px
BOSS_WIDTH = 152
BOSS_HEIGHT = 100

_PALETTE = {
    1: (200, 0, 40),  # dark red body
    2: (255, 40, 40),  # bright red
    3: (0, 0, 0),  # eyes
    4: (255, 200, 0),  # yellow accents
    5: (160, 0, 30),  # darker red detail
}

# fmt: off
_BOSS_MAP = [
    #0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 0  horns
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 1
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 1, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4, 1, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 2
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 3
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 4  head top
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 5
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 6  eyes
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 2, 1, 1, 1, 1, 1, 1, 2, 2, 3, 3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 7
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 3, 3, 2, 1, 1, 1, 1, 1, 1, 2, 3, 3, 3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 8
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 9
    [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 4, 4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],  # 10 face
    [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 4, 4, 4, 4, 4, 4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0],  # 11 mouth
    [0, 0, 0, 0, 0, 0, 1, 1, 1, 5, 1, 1, 1, 1, 1, 4, 4, 5, 5, 5, 5, 4, 4, 1, 1, 1, 1, 1, 5, 1, 1, 1, 0, 0, 0, 0, 0, 0],  # 12
    [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0],  # 13 body
    [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0],  # 14
    [0, 0, 0, 1, 1, 1, 1, 1, 5, 5, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 5, 5, 1, 1, 1, 1, 1, 0, 0, 0],  # 15
    [0, 0, 1, 1, 1, 1, 1, 5, 5, 5, 5, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 5, 5, 5, 5, 1, 1, 1, 1, 1, 0, 0],  # 16 arms
    [0, 1, 1, 1, 1, 1, 1, 5, 5, 5, 5, 1, 1, 1, 1, 5, 5, 5, 5, 5, 5, 5, 5, 1, 1, 1, 1, 5, 5, 5, 5, 1, 1, 1, 1, 1, 1, 0],  # 17
    [1, 1, 1, 1, 1, 1, 1, 1, 5, 5, 1, 1, 1, 1, 5, 5, 1, 1, 1, 1, 1, 1, 5, 5, 1, 1, 1, 1, 5, 5, 1, 1, 1, 1, 1, 1, 1, 1],  # 18
    [0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 5, 1, 1, 1, 1, 1, 1, 1, 1, 5, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0],  # 19
    [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0],  # 20
    [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],  # 21 legs
    [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0],  # 22
    [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],  # 23
    [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0],  # 24 feet
]
# fmt: on


class Boss(pygame.sprite.Sprite):
    def __init__(self, ai_settings, screen):
        super().__init__()
        self.ai_settings = ai_settings
        self.screen = screen
        screen_rect = screen.get_rect()

        self.max_hp = ai_settings.boss_hp
        self.hp = self.max_hp

        scale = getattr(ai_settings, "resolution_scale", 1.0)
        self._boss_w = max(38, int(BOSS_WIDTH * scale))
        self._boss_h = max(25, int(BOSS_HEIGHT * scale))

        base = pygame.Surface((BOSS_WIDTH, BOSS_HEIGHT), pygame.SRCALPHA)
        draw_pixel_art(base, _BOSS_MAP, _PIXEL_SIZE, _PALETTE)
        if scale != 1.0:
            self.image = pygame.transform.smoothscale(
                base, (self._boss_w, self._boss_h)
            )
        else:
            self.image = base
        self._current_image = self.image.copy()

        self.rect = self.image.get_rect()
        self.rect.centerx = screen_rect.centerx
        self.rect.top = int(40 * scale)

        self._x = float(self.rect.x)
        self._speed = ai_settings.boss_speed
        self._direction = 1
        self._screen_w = screen_rect.width

        self.shoot_timer = ai_settings.boss_shoot_interval
        self.spawn_timer = ai_settings.boss_spawn_interval
        self.should_shoot = False
        self.should_spawn = False

        self._flash_timer = 0

    def update(self):
        self._x += self._speed * self._direction
        self.rect.x = int(self._x)
        if self.rect.right >= self._screen_w or self.rect.left <= 0:
            self._direction *= -1
            self._x += self._speed * self._direction
            self.rect.x = int(self._x)

        self.shoot_timer -= 1
        self.spawn_timer -= 1

        if self.shoot_timer <= 0:
            self.should_shoot = True
            self.shoot_timer = self.ai_settings.boss_shoot_interval
        if self.spawn_timer <= 0:
            self.should_spawn = True
            self.spawn_timer = self.ai_settings.boss_spawn_interval

        if self._flash_timer > 0:
            self._flash_timer -= 1
            flash_img = self._current_image.copy()
            flash_img.fill((180, 180, 180), special_flags=pygame.BLEND_RGB_ADD)
            self.image.fill((0, 0, 0, 0))
            self.image.blit(flash_img, (0, 0))
            if self._flash_timer == 0:
                self.image.fill((0, 0, 0, 0))
                self.image.blit(self._current_image, (0, 0))

    def take_damage(self, amount):
        self.hp -= amount
        self._flash_timer = 3
        self._update_color()
        return self.hp <= 0

    def _update_color(self):
        brightness = 0.4 + 0.6 * (self.hp / self.max_hp)
        new_palette = {
            1: (int(200 * brightness), int(0 * brightness), int(40 * brightness)),
            2: (int(255 * brightness), int(40 * brightness), int(40 * brightness)),
            3: (0, 0, 0),
            4: (255, 200, 0),
            5: (int(160 * brightness), int(0 * brightness), int(30 * brightness)),
        }
        full = pygame.Surface((BOSS_WIDTH, BOSS_HEIGHT), pygame.SRCALPHA)
        draw_pixel_art(full, _BOSS_MAP, _PIXEL_SIZE, new_palette)
        scale = getattr(self.ai_settings, "resolution_scale", 1.0)
        if scale != 1.0:
            scaled = pygame.transform.smoothscale(full, (self._boss_w, self._boss_h))
        else:
            scaled = full
        self._current_image = scaled
        self.image.fill((0, 0, 0, 0))
        self.image.blit(self._current_image, (0, 0))
