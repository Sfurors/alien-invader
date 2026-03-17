"""AI fog of war and sighting memory.

The AI only 'knows' about player entities that its units/buildings can
currently see, or that were previously spotted (with decaying confidence).
"""

from .rts_settings import RTSSettings as S


class AIMemory:
    """Tracks what the AI has seen and where it last saw player entities."""

    # Map divided into sectors for smart scouting
    SECTOR_SIZE = 24

    def __init__(self, width=S.MAP_WIDTH, height=S.MAP_HEIGHT):
        self.width = width
        self.height = height
        # Per-tile fog: 0=unexplored, 1=explored, 2=visible
        self.fog = [[0] * width for _ in range(height)]
        # Sightings: {entity_id: {type, tx, ty, frame}}
        self.sightings = {}
        # Last known player base location or None
        self.last_known_base = None
        # Set of (sector_x, sector_y) that have been explored
        self.scouted_sectors = set()

    def reset_visible(self):
        """Demote VISIBLE -> EXPLORED each frame."""
        for y in range(self.height):
            for x in range(self.width):
                if self.fog[y][x] == S.FOG_VISIBLE:
                    self.fog[y][x] = S.FOG_EXPLORED

    def reveal(self, cx, cy, radius):
        """Mark tiles visible around (cx, cy)."""
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx * dx + dy * dy <= radius * radius:
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        self.fog[ny][nx] = S.FOG_VISIBLE
        # Mark sector as scouted
        sx = cx // self.SECTOR_SIZE
        sy = cy // self.SECTOR_SIZE
        self.scouted_sectors.add((sx, sy))

    def is_visible(self, tx, ty):
        if 0 <= tx < self.width and 0 <= ty < self.height:
            return self.fog[ty][tx] == S.FOG_VISIBLE
        return False

    def update_sightings(self, rts_ctx, frame):
        """Check what player entities are currently visible to AI."""
        for pu in rts_ctx.player_units:
            if self.is_visible(pu.tile_x, pu.tile_y):
                self.sightings[pu.entity_id] = {
                    "type": pu.unit_type,
                    "tx": pu.tile_x,
                    "ty": pu.tile_y,
                    "frame": frame,
                }
        for pb in rts_ctx.player_buildings:
            cx, cy = pb.center_tile()
            if self.is_visible(cx, cy):
                self.sightings[pb.entity_id] = {
                    "type": pb.building_type,
                    "tx": cx,
                    "ty": cy,
                    "frame": frame,
                }
                if pb.building_type == "main_base":
                    self.last_known_base = (cx, cy)

    def purge_dead(self, rts_ctx):
        """Remove sightings of entities that no longer exist."""
        alive_ids = set()
        for pu in rts_ctx.player_units:
            alive_ids.add(pu.entity_id)
        for pb in rts_ctx.player_buildings:
            alive_ids.add(pb.entity_id)
        dead = [eid for eid in self.sightings if eid not in alive_ids]
        for eid in dead:
            del self.sightings[eid]

    def decay_knowledge(self, current_frame, stale_threshold=3600):
        """Remove sightings older than threshold (default 60s)."""
        stale = [
            eid
            for eid, s in self.sightings.items()
            if current_frame - s["frame"] > stale_threshold
        ]
        for eid in stale:
            del self.sightings[eid]

    def get_visible_enemies(self, rts_ctx):
        """Return player entities currently visible to any AI unit/building."""
        visible = []
        for pu in rts_ctx.player_units:
            if self.is_visible(pu.tile_x, pu.tile_y):
                visible.append(pu)
        for pb in rts_ctx.player_buildings:
            cx, cy = pb.center_tile()
            if self.is_visible(cx, cy):
                visible.append(pb)
        return visible

    def get_visible_player_units(self, rts_ctx):
        """Return only player units (not buildings) currently visible."""
        return [
            pu for pu in rts_ctx.player_units if self.is_visible(pu.tile_x, pu.tile_y)
        ]

    def get_visible_player_buildings(self, rts_ctx):
        """Return only player buildings currently visible."""
        return [
            pb for pb in rts_ctx.player_buildings if self.is_visible(*pb.center_tile())
        ]

    def get_unscouted_sectors(self):
        """Return list of sector centers that haven't been explored yet."""
        sectors_x = self.width // self.SECTOR_SIZE + 1
        sectors_y = self.height // self.SECTOR_SIZE + 1
        unscouted = []
        for sy in range(sectors_y):
            for sx in range(sectors_x):
                if (sx, sy) not in self.scouted_sectors:
                    cx = min(
                        sx * self.SECTOR_SIZE + self.SECTOR_SIZE // 2, self.width - 1
                    )
                    cy = min(
                        sy * self.SECTOR_SIZE + self.SECTOR_SIZE // 2, self.height - 1
                    )
                    unscouted.append((cx, cy))
        return unscouted

    def get_last_known_base(self):
        """Return last known player base location or None."""
        return self.last_known_base

    def get_most_recent_sighting(self):
        """Return (tx, ty) of the most recently spotted player entity, or None."""
        if not self.sightings:
            return None
        best = max(self.sightings.values(), key=lambda s: s["frame"])
        return (best["tx"], best["ty"])
