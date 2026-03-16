"""Pure functions — no pygame import, fully testable without a display."""

ALIEN_H_MARGIN = 20
ALIEN_V_MARGIN = 20
FLEET_TOP_MARGIN = 60


def compute_fleet_grid(
    screen_w,
    screen_h,
    alien_w,
    alien_h,
    h_margin=ALIEN_H_MARGIN,
    v_margin=ALIEN_V_MARGIN,
    top_margin=FLEET_TOP_MARGIN,
):
    """Return (cols, rows) for a fleet that fits in the upper half of the screen."""
    available_width = screen_w - 2 * h_margin
    available_height = (screen_h // 2) - top_margin

    cols = max(1, available_width // (alien_w + h_margin))
    rows = max(1, available_height // (alien_h + v_margin))
    return cols, rows


def compute_fleet_positions(
    screen_w,
    alien_w,
    alien_h,
    cols,
    rows,
    h_margin=ALIEN_H_MARGIN,
    v_margin=ALIEN_V_MARGIN,
    top_margin=FLEET_TOP_MARGIN,
):
    """Return list of (x, y) top-left positions for each alien in the fleet."""
    total_fleet_width = cols * alien_w + (cols - 1) * h_margin
    x_start = (screen_w - total_fleet_width) // 2

    positions = []
    for row in range(rows):
        for col in range(cols):
            x = x_start + col * (alien_w + h_margin)
            y = top_margin + row * (alien_h + v_margin)
            positions.append((x, y))
    return positions


def circle_distance(pos_a, pos_b):
    """Euclidean distance between two (x, y) points."""
    dx = pos_a[0] - pos_b[0]
    dy = pos_a[1] - pos_b[1]
    return (dx * dx + dy * dy) ** 0.5


def is_circle_collision(pos_a, pos_b, radius_a, radius_b):
    """True when two circles overlap."""
    return circle_distance(pos_a, pos_b) < radius_a + radius_b


def compute_score_for_kills(count, points):
    """Total score awarded for killing *count* aliens worth *points* each."""
    return count * points
