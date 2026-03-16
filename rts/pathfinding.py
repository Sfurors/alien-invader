"""A* pathfinding on tile grid."""

import heapq


def find_path(tile_map, start, goal, occupied=None):
    """Find path from start (tx,ty) to goal (tx,ty).

    Returns list of (tx,ty) waypoints excluding start, or empty list if
    no path found. `occupied` is an optional set of (tx,ty) tiles blocked
    by buildings (besides terrain).
    """
    if start == goal:
        return []

    sx, sy = start
    gx, gy = goal

    if not tile_map.in_bounds(gx, gy):
        return []

    # If goal is impassable, try to find closest passable neighbor
    if not tile_map.is_passable(gx, gy) or (occupied and goal in occupied):
        best = None
        best_dist = float("inf")
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                nx, ny = gx + dx, gy + dy
                if tile_map.is_passable(nx, ny) and (
                    not occupied or (nx, ny) not in occupied
                ):
                    d = abs(nx - sx) + abs(ny - sy)
                    if d < best_dist:
                        best_dist = d
                        best = (nx, ny)
        if best is None:
            return []
        gx, gy = best

    open_set = []
    heapq.heappush(open_set, (0, sx, sy))
    came_from = {}
    g_score = {(sx, sy): 0}
    closed = set()

    while open_set:
        _, cx, cy = heapq.heappop(open_set)

        if (cx, cy) in closed:
            continue
        closed.add((cx, cy))

        if cx == gx and cy == gy:
            # Reconstruct path
            path = []
            node = (gx, gy)
            while node != (sx, sy):
                path.append(node)
                node = came_from[node]
            path.reverse()
            return path

        for dx, dy in [
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
            (-1, -1),
            (-1, 1),
            (1, -1),
            (1, 1),
        ]:
            nx, ny = cx + dx, cy + dy
            if not tile_map.in_bounds(nx, ny):
                continue
            if not tile_map.is_passable(nx, ny):
                continue
            if occupied and (nx, ny) in occupied:
                continue

            # Diagonal movement costs more
            move_cost = 1.414 if dx != 0 and dy != 0 else 1.0
            # Block diagonal movement through corners
            if dx != 0 and dy != 0:
                if not tile_map.is_passable(cx + dx, cy) or not tile_map.is_passable(
                    cx, cy + dy
                ):
                    continue

            new_g = g_score[(cx, cy)] + move_cost
            if new_g < g_score.get((nx, ny), float("inf")):
                g_score[(nx, ny)] = new_g
                # Heuristic: Chebyshev distance
                h = max(abs(nx - gx), abs(ny - gy))
                came_from[(nx, ny)] = (cx, cy)
                heapq.heappush(open_set, (new_g + h, nx, ny))

    return []  # no path found
