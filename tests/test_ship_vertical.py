"""Tests for vertical movement of the Ship class."""

import pygame
import pytest


# ── Vertical movement flags ──────────────────────────────────────────────────


class TestVerticalMovementFlags:
    def test_moving_up_initially_false(self, ship):
        assert not ship.moving_up

    def test_moving_down_initially_false(self, ship):
        assert not ship.moving_down

    def test_center_resets_moving_up(self, ship):
        ship.moving_up = True
        ship.center()
        assert not ship.moving_up

    def test_center_resets_moving_down(self, ship):
        ship.moving_down = True
        ship.center()
        assert not ship.moving_down


# ── Vertical boundary: bottom 1/4 of screen ─────────────────────────────────


class TestVerticalBoundary:
    def test_y_min_is_bottom_quarter(self, ship, screen):
        screen_rect = screen.get_rect()
        expected_y_min = screen_rect.bottom - screen_rect.height // 4
        assert ship._y_min == expected_y_min

    def test_ship_cannot_move_above_y_min(self, ship):
        """Ship should not move above the vertical boundary."""
        ship.moving_up = True
        # Place ship exactly at the boundary (rect.top == _y_min)
        ship.rect.top = ship._y_min
        ship.y = float(ship.rect.bottom)
        ship.x = float(ship.rect.centerx)

        old_y = ship.y
        ship.update()
        # Ship should not have moved up (rect.top is already at _y_min)
        assert ship.y >= old_y or ship.rect.top >= ship._y_min

    def test_ship_cannot_move_below_screen_bottom(self, ship, screen):
        """Ship should not move below the screen bottom."""
        screen_rect = screen.get_rect()
        ship.moving_down = True
        ship.rect.bottom = screen_rect.bottom
        ship.y = float(ship.rect.bottom)
        ship.x = float(ship.rect.centerx)

        old_y = ship.y
        ship.update()
        assert ship.y <= float(screen_rect.bottom)


# ── Vertical position updates ────────────────────────────────────────────────


class TestVerticalPositionUpdate:
    def test_moving_up_decreases_y(self, ship):
        """When moving up and within bounds, y should decrease."""
        # Position ship well within the allowed zone
        ship.rect.bottom = ship.screen_rect.bottom - 10
        ship.rect.top = ship._y_min + 50  # ensure there's room to move up
        ship.y = float(ship.rect.bottom)
        ship.x = float(ship.rect.centerx)

        ship.moving_up = True
        old_y = ship.y
        ship.update()
        assert ship.y < old_y

    def test_moving_down_increases_y(self, ship):
        """When moving down and within bounds, y should increase."""
        # Position ship above the bottom boundary
        ship.rect.bottom = ship.screen_rect.bottom - 50
        ship.y = float(ship.rect.bottom)
        ship.x = float(ship.rect.centerx)

        ship.moving_down = True
        old_y = ship.y
        ship.update()
        assert ship.y > old_y

    def test_not_moving_vertically_keeps_y(self, ship):
        """When not moving, y stays the same."""
        ship.moving_up = False
        ship.moving_down = False
        old_y = ship.y
        ship.update()
        assert ship.y == old_y

    def test_vertical_speed_equals_ship_speed(self, ship, ai_settings):
        """Vertical movement uses the same speed as horizontal."""
        ship.rect.bottom = ship.screen_rect.bottom - 50
        ship.rect.top = ship._y_min + 50
        ship.y = float(ship.rect.bottom)
        ship.x = float(ship.rect.centerx)

        ship.moving_up = True
        old_y = ship.y
        ship.update()
        assert old_y - ship.y == pytest.approx(ai_settings.ship_speed)

    def test_rect_bottom_updated_after_vertical_move(self, ship):
        """rect.bottom should reflect the new y position after update."""
        ship.rect.bottom = ship.screen_rect.bottom - 50
        ship.rect.top = ship._y_min + 50
        ship.y = float(ship.rect.bottom)
        ship.x = float(ship.rect.centerx)

        ship.moving_up = True
        ship.update()
        assert ship.rect.bottom == int(ship.y)


# ── Center method resets vertical position ───────────────────────────────────


class TestCenterResetsVertical:
    def test_center_resets_y_to_screen_bottom(self, ship, screen):
        """center() should put the ship back at the bottom of the screen."""
        ship.y -= 100
        ship.rect.bottom -= 100
        ship.center()
        assert ship.y == float(ship.screen_rect.bottom)
        assert ship.rect.bottom == ship.screen_rect.bottom


# ── Thrust animation tied to vertical movement ──────────────────────────────


class TestThrustAnimation:
    def test_thrust_increases_when_moving_up(self, ship):
        """_thrust should increase toward 1.0 when moving_up is True."""
        ship._thrust = 0.0
        ship.moving_up = True
        ship.rect.top = ship._y_min + 50
        ship.y = float(ship.rect.bottom)
        ship.x = float(ship.rect.centerx)
        ship.update()
        assert ship._thrust > 0.0

    def test_thrust_decreases_when_not_moving_up(self, ship):
        """_thrust should decrease toward 0.0 when moving_up is False."""
        ship._thrust = 1.0
        ship.moving_up = False
        ship.update()
        assert ship._thrust < 1.0

    def test_boost_image_when_thrust_high(self, ship):
        """Ship should use boost image when thrust > 0.5."""
        ship._thrust = 0.0
        ship.moving_up = True
        ship.rect.top = ship._y_min + 50
        ship.y = float(ship.rect.bottom)
        ship.x = float(ship.rect.centerx)
        # Run enough updates to get thrust above 0.5
        for _ in range(20):
            ship.update()
        assert ship.base_image is ship._img_boost

    def test_idle_image_when_thrust_low(self, ship):
        """Ship should use idle image when thrust <= 0.5."""
        ship._thrust = 0.0
        ship.moving_up = False
        ship.update()
        assert ship.base_image is ship._img_idle

    def test_center_resets_thrust(self, ship):
        """center() should reset thrust to 0."""
        ship._thrust = 1.0
        ship.center()
        assert ship._thrust == 0.0
        assert ship.base_image is ship._img_idle


# ── Combined horizontal and vertical movement ───────────────────────────────


class TestCombinedMovement:
    def test_diagonal_movement(self, ship):
        """Ship should be able to move both horizontally and vertically."""
        ship.rect.bottom = ship.screen_rect.bottom - 50
        ship.rect.top = ship._y_min + 50
        ship.y = float(ship.rect.bottom)
        ship.x = float(ship.rect.centerx)
        ship.rect.right = ship.screen_rect.right - 50  # room to move right

        ship.moving_right = True
        ship.moving_up = True
        old_x = ship.x
        old_y = ship.y
        ship.update()
        assert ship.x > old_x
        assert ship.y < old_y

    def test_diagonal_left_and_down(self, ship):
        """Ship should move left and down simultaneously."""
        ship.rect.bottom = ship.screen_rect.bottom - 50
        ship.y = float(ship.rect.bottom)
        ship.x = float(ship.rect.centerx)
        ship.rect.left = 50  # room to move left

        ship.moving_left = True
        ship.moving_down = True
        old_x = ship.x
        old_y = ship.y
        ship.update()
        assert ship.x < old_x
        assert ship.y > old_y


# ── Horizontal movement coverage (left movement + tilt) ─────────────────


class TestHorizontalAndTilt:
    def test_moving_left_decreases_x(self, ship):
        """Moving left within bounds should decrease x."""
        ship.rect.left = 50  # room to move left
        ship.x = float(ship.rect.centerx)
        ship.y = float(ship.rect.bottom)

        ship.moving_left = True
        old_x = ship.x
        ship.update()
        assert ship.x < old_x

    def test_tilt_left_when_moving_left(self, ship):
        """Ship should tilt left (positive angle) when moving left only."""
        ship.x = float(ship.rect.centerx)
        ship.y = float(ship.rect.bottom)
        ship.rect.left = 50
        ship.angle = 0.0

        ship.moving_left = True
        ship.moving_right = False
        ship.update()
        assert ship.angle > 0.0  # positive angle = tilt left

    def test_tilt_increases_toward_target(self, ship):
        """When angle is below the tilt target, it should increase."""
        ship.x = float(ship.rect.centerx)
        ship.y = float(ship.rect.bottom)
        ship.rect.left = 50
        ship.angle = 2.0  # below MAX_TILT (12)

        ship.moving_left = True
        ship.moving_right = False
        old_angle = ship.angle
        ship.update()
        assert ship.angle > old_angle


# ── Blitme flame glow rendering ─────────────────────────────────────────


class TestBlitmeFlameGlow:
    def test_blitme_draws_glow_when_thrust_active(self, ship, screen):
        """blitme should draw flame glow when thrust > 0.3."""
        ship._thrust = 0.8
        ship._flame_phase = 0.0
        # Should not raise; exercises the flame glow branch
        ship.blitme()
        assert ship._flame_phase > 0.0  # phase advances

    def test_blitme_no_glow_when_thrust_low(self, ship, screen):
        """blitme should skip glow when thrust <= 0.3."""
        ship._thrust = 0.0
        ship._flame_phase = 0.0
        ship.blitme()
        assert ship._flame_phase == 0.0  # phase unchanged


# ── Scaled ship surface ─────────────────────────────────────────────────


class TestScaledShipSurface:
    def test_build_ship_surface_with_scale(self):
        """_build_ship_surface should apply smoothscale when scale != 1.0."""
        from ship import (
            _build_ship_surface,
            _FLAME_IDLE,
            _COLS,
            _PIXEL_SIZE,
            _BODY_ROWS,
        )

        scale = 0.5
        surf = _build_ship_surface(_FLAME_IDLE, scale)
        total_rows = _BODY_ROWS + len(_FLAME_IDLE)
        expected_w = max(16, int(_COLS * _PIXEL_SIZE * scale))
        expected_h = max(20, int(total_rows * _PIXEL_SIZE * scale))
        assert surf.get_width() == expected_w
        assert surf.get_height() == expected_h

    def test_build_ship_surface_no_scale(self):
        """_build_ship_surface with scale=1.0 returns original size."""
        from ship import (
            _build_ship_surface,
            _FLAME_IDLE,
            _COLS,
            _PIXEL_SIZE,
            _BODY_ROWS,
        )

        surf = _build_ship_surface(_FLAME_IDLE, 1.0)
        total_rows = _BODY_ROWS + len(_FLAME_IDLE)
        assert surf.get_width() == _COLS * _PIXEL_SIZE
        assert surf.get_height() == total_rows * _PIXEL_SIZE
