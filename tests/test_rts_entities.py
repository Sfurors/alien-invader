"""Tests for RTS entity base classes and registry."""

import pytest
import pygame
from rts.entity_base import BaseUnit, BaseBuilding
from rts.entity_registry import UNIT_DEFS, BUILDING_DEFS, PRODUCED_BY
from rts.rts_settings import RTSSettings as S


@pytest.fixture(autouse=True)
def init_pygame():
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


class TestEntityRegistry:
    def test_all_units_have_required_fields(self):
        required = {"faction", "hp", "speed", "attack", "attack_range", "cost"}
        for name, data in UNIT_DEFS.items():
            for field in required:
                assert field in data, f"{name} missing {field}"

    def test_all_buildings_have_required_fields(self):
        required = {"faction", "hp", "cost", "size", "produces"}
        for name, data in BUILDING_DEFS.items():
            for field in required:
                assert field in data, f"{name} missing {field}"

    def test_produced_by_mapping(self):
        assert PRODUCED_BY["engineer"] == "main_base"
        assert PRODUCED_BY["marine"] == "barracks"
        assert PRODUCED_BY["scout"] == "hive"

    def test_human_units_exist(self):
        assert "engineer" in UNIT_DEFS
        assert "miner" in UNIT_DEFS
        assert "marine" in UNIT_DEFS

    def test_lizard_units_exist(self):
        assert "scout" in UNIT_DEFS
        assert "warrior" in UNIT_DEFS
        assert "spitter" in UNIT_DEFS


class TestBaseUnit:
    def test_create_unit(self):
        u = BaseUnit("engineer", 5, 5, "human")
        assert u.hp == UNIT_DEFS["engineer"]["hp"]
        assert u.tile_x == 5
        assert u.tile_y == 5
        assert u.faction == "human"

    def test_take_damage(self):
        u = BaseUnit("marine", 5, 5, "human")
        initial_hp = u.hp
        u.take_damage(10)
        assert u.hp == initial_hp - 10

    def test_kill_on_zero_hp(self):
        u = BaseUnit("scout", 5, 5, "lizard")
        group = pygame.sprite.Group(u)
        u.take_damage(u.hp)
        assert len(group) == 0

    def test_set_move_target(self):
        u = BaseUnit("engineer", 5, 5, "human")
        u.set_move_target([(6, 5), (7, 5)])
        assert u.moving
        assert len(u.path) == 2

    def test_update_moves_along_path(self):
        u = BaseUnit("marine", 5, 5, "human")
        u.set_move_target([(6, 5)])
        initial_px = u.px
        for _ in range(100):
            u.update()
        assert u.px > initial_px


class TestBaseBuilding:
    def test_create_building(self):
        b = BaseBuilding("main_base", 3, 3, "human")
        assert b.hp == BUILDING_DEFS["main_base"]["hp"]
        assert b.size == (3, 3)

    def test_production_queue(self):
        b = BaseBuilding("main_base", 3, 3, "human")
        b.start_production("engineer")
        assert len(b.production_queue) == 1

    def test_production_completes(self):
        b = BaseBuilding("main_base", 3, 3, "human")
        b.start_production("miner")
        # Tick until done
        for _ in range(S.PRODUCTION_TIME + 1):
            b.update()
        result = b.pop_produced()
        assert result == "miner"

    def test_occupies_tile(self):
        b = BaseBuilding("main_base", 3, 3, "human")
        assert b.occupies_tile(3, 3)
        assert b.occupies_tile(5, 5)
        assert not b.occupies_tile(6, 6)

    def test_under_construction(self):
        b = BaseBuilding("barracks", 5, 5, "human")
        b.under_construction = True
        b.build_progress = 0
        for _ in range(b.build_time):
            b.update()
        assert not b.under_construction
