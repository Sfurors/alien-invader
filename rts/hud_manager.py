"""HUD manager: builds context-sensitive buttons and dispatches click actions."""

from .hud_buttons import HudButtonPanel
from .entity_registry import BUILDING_DEFS, UNIT_DEFS

# Compact square button grid
BTN_SIZE = 36
BTN_MARGIN = 3
BTN_COLS = 5


# ── Building definitions: icon, type, hotkey, description ──

_BUILDINGS = [
    (
        "HQ",
        "main_base",
        "1",
        "Main Base — stores crystals & isotope, produces engineers, miners & scouts",
    ),
    ("BK", "barracks", "2", "Barracks — trains marines"),
    ("TU", "turret", "3", "Turret — automated defense tower"),
    ("MC", "mining_camp", "4", "Mining Camp — drop-off for crystal miners"),
    ("EX", "isotope_extractor", "5", "Extractor — harvests isotope vents"),
]


def _cost_str(cost):
    s = f"{cost['crystals']}c"
    if cost["isotope"] > 0:
        s += f" {cost['isotope']}i"
    return s


class HudManager:
    """Rebuilds HUD buttons each frame based on selection context."""

    def __init__(self):
        self.panel = HudButtonPanel()

    def rebuild(self, state, rts_ctx, screen_w, viewport_h):
        """Rebuild buttons based on current selection."""
        self.panel.clear()

        hud_y = viewport_h
        # Right-align button grid
        panel_x = screen_w - (BTN_COLS * (BTN_SIZE + BTN_MARGIN)) - 10
        panel_y = hud_y + 8

        if state.build_mode:
            self.panel.add(
                panel_x,
                panel_y,
                BTN_SIZE * 2 + BTN_MARGIN,
                BTN_SIZE,
                "X",
                "ESC",
                "cancel_build",
                tooltip_title="Cancel Placement",
                tooltip_detail="Press ESC or click to cancel",
            )
            return

        has_engineer = any(u.can_build for u in state.selected_units)
        if has_engineer:
            self._add_building_buttons(state, rts_ctx, panel_x, panel_y)
            return

        if state.selected_building and state.selected_building.produces:
            self._add_production_buttons(state, panel_x, panel_y)
            return

        if state.selected_units:
            self._add_unit_action_buttons(state, panel_x, panel_y)

    def _add_building_buttons(self, state, rts_ctx, px, py):
        for i, (icon, btype, hotkey, desc) in enumerate(_BUILDINGS):
            col = i % BTN_COLS
            row = i // BTN_COLS
            x = px + col * (BTN_SIZE + BTN_MARGIN)
            y = py + row * (BTN_SIZE + BTN_MARGIN)

            bdef = BUILDING_DEFS[btype]
            cost = bdef["cost"]
            cs = _cost_str(cost)
            can_afford = (
                bdef["faction"] == "human"
                and state.crystals >= cost["crystals"]
                and state.isotope >= cost["isotope"]
            )
            # Enforce max_count (e.g. 1 HQ per player)
            max_count = bdef.get("max_count", 0)
            if max_count > 0 and rts_ctx:
                existing = sum(
                    1 for b in rts_ctx.player_buildings if b.building_type == btype
                )
                if existing >= max_count:
                    can_afford = False

            name = btype.replace("_", " ").title()
            tip_detail = desc
            if max_count > 0 and rts_ctx:
                existing = sum(
                    1 for b in rts_ctx.player_buildings if b.building_type == btype
                )
                if existing >= max_count:
                    tip_detail = f"Limit: {max_count} per player (already built)"

            self.panel.add(
                x,
                y,
                BTN_SIZE,
                BTN_SIZE,
                icon,
                hotkey,
                f"build:{btype}",
                enabled=can_afford,
                tooltip_title=f"[{hotkey}] {name} ({cs})",
                tooltip_detail=tip_detail,
            )

    def _add_production_buttons(self, state, px, py):
        building = state.selected_building
        hotkeys = ["P", "O", "I"]
        _icons = {
            "engineer": "En",
            "miner": "Mi",
            "marine": "Ma",
            "scout_human": "Sc",
            "drone": "Dr",
            "scout": "Sc",
            "warrior": "Wa",
            "spitter": "Sp",
        }
        for i, utype in enumerate(building.produces):
            col = i % BTN_COLS
            row = i // BTN_COLS
            x = px + col * (BTN_SIZE + BTN_MARGIN)
            y = py + row * (BTN_SIZE + BTN_MARGIN)

            cost = UNIT_DEFS[utype]["cost"]
            cs = _cost_str(cost)
            hk = hotkeys[i] if i < len(hotkeys) else ""
            icon = _icons.get(utype, utype[:2].title())
            can_afford = (
                state.crystals >= cost["crystals"] and state.isotope >= cost["isotope"]
            )
            stats = UNIT_DEFS[utype]
            name = utype.replace("_", " ").title()
            detail = f"HP:{stats['hp']}  SPD:{stats['speed']}  ATK:{stats['attack']}  RNG:{stats['attack_range']}"
            self.panel.add(
                x,
                y,
                BTN_SIZE,
                BTN_SIZE,
                icon,
                hk,
                f"produce:{i}",
                enabled=can_afford,
                tooltip_title=f"[{hk}] {name} ({cs})",
                tooltip_detail=detail,
            )

    def _add_unit_action_buttons(self, state, px, py):
        col = 0
        self.panel.add(
            px + col * (BTN_SIZE + BTN_MARGIN),
            py,
            BTN_SIZE,
            BTN_SIZE,
            "ST",
            "S",
            "action:stop",
            tooltip_title="[S] Stop",
            tooltip_detail="Halt all selected units",
        )
        col += 1

        has_scout = any(u.unit_type == "scout_human" for u in state.selected_units)
        if has_scout:
            any_on = any(
                u.scout_mode
                for u in state.selected_units
                if u.unit_type == "scout_human"
            )
            icon = "S!" if any_on else "Sc"
            self.panel.add(
                px + col * (BTN_SIZE + BTN_MARGIN),
                py,
                BTN_SIZE,
                BTN_SIZE,
                icon,
                "T",
                "action:scout_toggle",
                tooltip_title="[T] Scout Mode" + (" (ON)" if any_on else ""),
                tooltip_detail="Auto-explore fog; seppuku on enemy contact",
            )

    def handle_click(self, mx, my, state, rts_ctx):
        """Handle a left-click on the HUD. Returns True if a button was clicked."""
        btn = self.panel.hit_test(mx, my)
        if btn is None:
            return False

        action = btn.action_id
        if action == "cancel_build":
            state.cancel_build()
        elif action.startswith("build:"):
            _do_enter_build_mode(action[6:], state, rts_ctx)
        elif action.startswith("produce:"):
            _do_produce(int(action[8:]), state)
        elif action == "action:stop":
            _do_stop(state)
        elif action == "action:scout_toggle":
            _do_scout_toggle(state)

        return True

    def update_hover(self, mx, my):
        self.panel.update_hover(mx, my)


# ── Shared action functions (used by both buttons and keyboard) ──


def _do_enter_build_mode(btype, state, rts_ctx=None):
    """Enter build placement mode for given building type."""
    bdef = BUILDING_DEFS[btype]
    cost = bdef["cost"]
    if not (
        bdef["faction"] == "human"
        and state.crystals >= cost["crystals"]
        and state.isotope >= cost["isotope"]
    ):
        return
    # Enforce max_count
    max_count = bdef.get("max_count", 0)
    if max_count > 0 and rts_ctx:
        existing = sum(1 for b in rts_ctx.player_buildings if b.building_type == btype)
        if existing >= max_count:
            return
    state.build_mode = btype


def _do_produce(slot, state):
    """Produce unit from selected building's production slot."""
    building = state.selected_building
    if not building or slot >= len(building.produces):
        return
    unit_type = building.produces[slot]
    cost = UNIT_DEFS[unit_type]["cost"]
    if state.crystals >= cost["crystals"] and state.isotope >= cost["isotope"]:
        state.crystals -= cost["crystals"]
        state.isotope -= cost["isotope"]
        building.start_production(unit_type)


def _do_stop(state):
    """Stop all selected units."""
    for u in state.selected_units:
        u.path = []
        u.moving = False
        u.attack_target = None
        u.harvesting = False
        u.returning = False
        u.build_target = None
        u.building = False
        u.scout_mode = False


def _do_scout_toggle(state):
    """Toggle scout mode for selected human scouts."""
    for u in state.selected_units:
        if u.unit_type == "scout_human":
            u.scout_mode = not u.scout_mode
            if not u.scout_mode:
                u.scout_timer = 0
