"""Tests for fog of war."""

import pytest
from rts.fog import FogOfWar
from rts.rts_settings import RTSSettings as S


class TestFogOfWar:
    def test_initial_state_unexplored(self):
        fog = FogOfWar(10, 10)
        for y in range(10):
            for x in range(10):
                assert fog.state[y][x] == S.FOG_UNEXPLORED

    def test_reveal_makes_visible(self):
        fog = FogOfWar(10, 10)
        fog.reveal(5, 5, 2)
        assert fog.is_visible(5, 5)
        assert fog.is_visible(6, 5)
        assert fog.is_explored(5, 5)

    def test_reset_demotes_visible_to_explored(self):
        fog = FogOfWar(10, 10)
        fog.reveal(5, 5, 1)
        assert fog.is_visible(5, 5)
        fog.reset_visible()
        assert not fog.is_visible(5, 5)
        assert fog.is_explored(5, 5)

    def test_unexplored_stays_unexplored_after_reset(self):
        fog = FogOfWar(10, 10)
        fog.reset_visible()
        assert not fog.is_explored(5, 5)

    def test_out_of_bounds(self):
        fog = FogOfWar(10, 10)
        assert not fog.is_visible(-1, 0)
        assert not fog.is_visible(0, 10)
        assert not fog.is_explored(10, 0)

    def test_reveal_radius(self):
        fog = FogOfWar(20, 20)
        fog.reveal(10, 10, 3)
        # Center should be visible
        assert fog.is_visible(10, 10)
        # Within radius
        assert fog.is_visible(12, 10)
        # Outside radius
        assert not fog.is_visible(14, 10)
