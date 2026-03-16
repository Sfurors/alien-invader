RESOLUTION_PRESETS = {
    "small": (512, 800),
    "medium": (640, 1000),
    "large": (768, 1200),
}


class Settings:
    def __init__(self):
        self.screen_width = 768
        self.screen_height = 1200
        self.bg_color = (10, 10, 30)

        self.ship_speed = 4

        self.bullet_speed = 10
        self.bullet_width = 4
        self.bullet_height = 18
        self.bullet_color = (255, 220, 0)
        self.bullets_allowed = 3

        self.alien_speed = 1.0
        self.fleet_drop_speed = 20
        self.fleet_direction = 1  # 1 = right, -1 = left
        self.alien_points = 50

        # Level progression
        self.level_alien_speeds = {1: 1.0, 2: 1.8, 3: 2.5}
        self.level_alien_points = {1: 50, 2: 100, 3: 150}
        self.alien_dodge = False
        self.alien_dodge_amplitude = 30
        self.alien_dodge_frequency = 0.02

        # Boss settings
        self.boss_hp = 30
        self.boss_speed = 1.5
        self.boss_shoot_interval = 300
        self.boss_spawn_interval = 600
        self.boss_projectile_speed = 4
        self.boss_projectile_count = 8
        self.boss_projectile_spread = 120
        self.boss_points = 1000
        self.boss_helper_count = 3

        self.drop_speed = 3
        self.drop_chance = 0.10
        self.rocket_speed = 10
        self.rocket_radius = 160
        self.rocket_detonate_fraction = 0.02

        self.resolution_scale = 1.0
        self.font_scale = 1.0

    def apply_resolution(self, preset_name):
        w, h = RESOLUTION_PRESETS[preset_name]
        self.screen_width = w
        self.screen_height = h
        scale = h / 1200
        self.resolution_scale = scale
        self.font_scale = w / 768

        # Speeds
        self.ship_speed = 4 * scale
        self.bullet_speed = 10 * scale
        self.fleet_drop_speed = 20 * scale
        self.boss_speed = 1.5 * scale
        self.boss_projectile_speed = 4 * scale
        self.drop_speed = 3 * scale
        self.rocket_speed = 10 * scale

        # Scale level alien speeds
        self.level_alien_speeds = {
            k: v * scale for k, v in {1: 1.0, 2: 1.8, 3: 2.5}.items()
        }
        self.alien_speed = self.level_alien_speeds[1]

        # Pixel sizes
        self.bullet_width = max(2, int(4 * scale))
        self.bullet_height = max(8, int(18 * scale))
        self.rocket_radius = int(160 * scale)
        self.alien_dodge_amplitude = 30 * scale

    def apply_level(self, level):
        self.alien_speed = self.level_alien_speeds.get(
            level, 2.5 * self.resolution_scale
        )
        self.alien_points = self.level_alien_points.get(level, 150)
        self.alien_dodge = level >= 2
