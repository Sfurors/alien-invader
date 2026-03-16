"""Pure math tests — no pygame, no display needed."""

import pytest
from game_logic import (
    compute_fleet_grid,
    compute_fleet_positions,
    circle_distance,
    is_circle_collision,
    compute_score_for_kills,
)


class TestComputeFleetGrid:
    def test_returns_positive_dims_for_normal_screen(self):
        cols, rows = compute_fleet_grid(768, 1200, 50, 35)
        assert cols > 0
        assert rows > 0

    def test_clamps_to_min_one_when_screen_too_small(self):
        cols, rows = compute_fleet_grid(10, 10, 50, 35)
        assert cols == 1
        assert rows == 1

    def test_wider_screen_gives_more_columns(self):
        cols_small, _ = compute_fleet_grid(400, 600, 50, 35)
        cols_large, _ = compute_fleet_grid(1200, 600, 50, 35)
        assert cols_large > cols_small

    def test_taller_screen_gives_more_rows(self):
        _, rows_short = compute_fleet_grid(768, 400, 50, 35)
        _, rows_tall = compute_fleet_grid(768, 1600, 50, 35)
        assert rows_tall > rows_short


class TestComputeFleetPositions:
    def test_count_matches_cols_times_rows(self):
        positions = compute_fleet_positions(768, 50, 35, 5, 3)
        assert len(positions) == 15

    def test_all_positions_within_screen_width(self):
        screen_w = 768
        positions = compute_fleet_positions(screen_w, 50, 35, 5, 3)
        for x, _ in positions:
            assert x >= 0
            assert x + 50 <= screen_w

    def test_first_row_starts_at_top_margin(self):
        from game_logic import FLEET_TOP_MARGIN

        positions = compute_fleet_positions(768, 50, 35, 5, 3)
        y_values = [y for _, y in positions]
        assert FLEET_TOP_MARGIN in y_values

    def test_single_cell_is_centered(self):
        screen_w = 100
        positions = compute_fleet_positions(screen_w, 50, 35, 1, 1)
        x, _ = positions[0]
        # x_start = (100 - 50) // 2 = 25
        assert x == 25


class TestCircleDistance:
    def test_pythagorean_triple(self):
        assert circle_distance((0, 0), (3, 4)) == pytest.approx(5.0)

    def test_same_point_is_zero(self):
        assert circle_distance((7, 7), (7, 7)) == pytest.approx(0.0)

    def test_horizontal(self):
        assert circle_distance((0, 0), (10, 0)) == pytest.approx(10.0)

    def test_symmetric(self):
        assert circle_distance((1, 2), (4, 6)) == pytest.approx(
            circle_distance((4, 6), (1, 2))
        )


class TestIsCircleCollision:
    def test_overlapping_circles_collide(self):
        # Distance = 5, combined radius = 6
        assert is_circle_collision((0, 0), (3, 4), 3, 3)

    def test_touching_circles_do_not_collide(self):
        # Distance = 10, combined radius = 10 — strictly less required
        assert not is_circle_collision((0, 0), (10, 0), 5, 5)

    def test_far_apart_circles_do_not_collide(self):
        assert not is_circle_collision((0, 0), (100, 0), 3, 3)

    def test_same_position_always_collides(self):
        assert is_circle_collision((5, 5), (5, 5), 1, 1)


class TestComputeScoreForKills:
    def test_five_kills(self):
        assert compute_score_for_kills(5, 50) == 250

    def test_zero_kills(self):
        assert compute_score_for_kills(0, 50) == 0

    def test_one_kill(self):
        assert compute_score_for_kills(1, 100) == 100

    def test_zero_points(self):
        assert compute_score_for_kills(10, 0) == 0
