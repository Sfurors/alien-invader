class GameStats:
    def __init__(self):
        self.score = 0
        self.rockets = 0
        self.level = 1
        self.boss_active = False
        self.game_won = False
        self.victory_cutscene_active = False
        self.chapter2_active = False
        self.chapter3_active = False
        self.level_transition_timer = 0
        self.game_active = False
        self.game_started = (
            False  # False = show menu, True = show game-over after death
        )
        self.game_over_sound_played = False
        self.paused = False

        # Menu navigation
        self.menu_cursor = 0
        self.rts_submenu_active = False
        self.rts_submenu_cursor = 0
        self.rts_load_save = False

    def reset_stats(self):
        self.score = 0
        self.rockets = 0
        self.level = 1
        self.boss_active = False
        self.game_won = False
        self.victory_cutscene_active = False
        self.chapter2_active = False
        self.chapter3_active = False
        self.level_transition_timer = 0
        self.game_over_sound_played = False
