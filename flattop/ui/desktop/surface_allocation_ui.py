import pygame
import sys
from dataclasses import dataclass, field

from flattop.operations_chart_models import Ship
from flattop.surface_combat_engine import (
    POSITION_GUNNERY, POSITION_TORPEDO, POSITION_SCREEN,
    assign_default_positions,
)

# ── Colour palette ────────────────────────────────────────────────────────────
_BG          = (28, 28, 32)
_PANEL       = (40, 40, 52)
_ROW_ALT     = (46, 46, 58)
_HEADER      = (180, 180, 220)
_TEXT        = (240, 240, 200)
_DIM         = (160, 160, 170)
_BTN_GREEN   = (40, 130, 70)
_BTN_RED     = (110, 55, 55)
_BTN_BLUE    = (50, 90, 160)
_BTN_HOVER   = (80, 160, 100)
_WHITE       = (255, 255, 255)
_GOLD        = (255, 210, 60)
_SEL_GUNNERY = (60, 100, 60)
_SEL_TORPEDO = (60, 80, 130)
_SEL_SCREEN  = (90, 70, 40)

_POSITIONS = [POSITION_GUNNERY, POSITION_TORPEDO, POSITION_SCREEN]
_POS_LABELS = {POSITION_GUNNERY: "Gunnery", POSITION_TORPEDO: "Torpedo", POSITION_SCREEN: "Screen"}
_POS_COLORS = {POSITION_GUNNERY: _SEL_GUNNERY, POSITION_TORPEDO: _SEL_TORPEDO, POSITION_SCREEN: _SEL_SCREEN}


@dataclass
class SurfaceCombatInputs:
    """All player choices collected by the multi-step wizard."""
    attacker_positions: dict = field(default_factory=dict)
    defender_positions: dict = field(default_factory=dict)
    attacker_die: int = 3
    defender_die: int = 3
    attacker_gunnery_targets: dict = field(default_factory=dict)
    defender_gunnery_targets: dict = field(default_factory=dict)
    attacker_torpedo_targets: dict = field(default_factory=dict)
    defender_torpedo_targets: dict = field(default_factory=dict)


class SurfaceAllocationUI:
    """
    Multi-step interactive wizard for Surface Attack Combat setup.

    Steps
    -----
    1. Attacker ship-position assignment  (Gunnery / Torpedo / Screen)
    2. Attacker secret die selection      (1-6)
    3. Defender ship-position assignment
    4. Defender secret die selection
    5. Attacker gunnery target assignment
    6. Defender gunnery target assignment
    7. (optional) Attacker torpedo target
    8. (optional) Defender torpedo target

    Returns a SurfaceCombatInputs or None on Cancel.
    """

    MARGIN    = 18
    ROW_H     = 44
    BTN_W     = 120
    BTN_H     = 38

    def __init__(
        self,
        screen: pygame.Surface,
        attacker_ships: list[Ship],
        defender_ships: list[Ship],
        attacker_side: str = "Attacker",
        defender_side: str = "Defender",
    ):
        self.screen       = screen
        self.att_ships    = [s for s in attacker_ships if s.status != "Sunk"]
        self.def_ships    = [s for s in defender_ships  if s.status != "Sunk"]
        self.att_label    = attacker_side
        self.def_label    = defender_side

        self.font_sm  = pygame.font.SysFont(None, 22)
        self.font_md  = pygame.font.SysFont(None, 26)
        self.font_hd  = pygame.font.SysFont(None, 30, bold=True)

        self._step         = 1
        self._result       = SurfaceCombatInputs()
        self._running      = True
        # Per-step working state
        self._positions    = {}   # ship → position (current step's assignment)
        self._die_choice   = 3    # 1-6
        self._tgt_by_idx   = {}   # ship-idx → target-ship-idx

    # ── Public API ────────────────────────────────────────────────────────────

    def handle_events(self) -> SurfaceCombatInputs | None:
        """Run the wizard and return collected inputs or None if cancelled."""
        self._enter_step(1)
        clock = pygame.time.Clock()
        while self._running:
            self._draw()
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return None
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_click(event.pos)
            clock.tick(30)
        return self._result

    # ── Step initialisation ──────────────────────────────────────────────────

    def _enter_step(self, step: int):
        self._step = step
        self._click_rects = []   # [(tag, rect), …]

        if step == 1:   # Attacker position assignment
            self._positions = assign_default_positions(self.att_ships, self.att_label)
        elif step == 2:  # Attacker die
            self._die_choice = 3
        elif step == 3:  # Defender position assignment
            self._positions = assign_default_positions(self.def_ships, self.def_label)
        elif step == 4:  # Defender die
            self._die_choice = 3
        elif step in (5, 6):  # Gunnery target assignment
            ships = self.att_ships if step == 5 else self.def_ships
            targets = self.def_ships if step == 5 else self.att_ships
            pos_map = (self._result.attacker_positions if step == 5
                       else self._result.defender_positions)
            self._tgt_by_idx = {}
            for i, ship in enumerate(ships):
                if pos_map.get(ship) == POSITION_GUNNERY and targets:
                    self._tgt_by_idx[i] = 0
        elif step in (7, 8):  # Torpedo target assignment
            ships = self.att_ships if step == 7 else self.def_ships
            targets = self.def_ships if step == 7 else self.att_ships
            pos_map = (self._result.attacker_positions if step == 7
                       else self._result.defender_positions)
            self._tgt_by_idx = {}
            for i, ship in enumerate(ships):
                if (pos_map.get(ship) == POSITION_TORPEDO
                        and ship.torpedo_factor > 0
                        and not getattr(ship, "torpedo_factor_used", False)
                        and targets):
                    self._tgt_by_idx[i] = 0

    def _max_step(self) -> int:
        """Determine last step depending on torpedo availability."""
        att_has_torp = any(
            self._result.attacker_positions.get(s) == POSITION_TORPEDO
            and s.torpedo_factor > 0
            and not getattr(s, "torpedo_factor_used", False)
            for s in self.att_ships
        )
        def_has_torp = any(
            self._result.defender_positions.get(s) == POSITION_TORPEDO
            and s.torpedo_factor > 0
            and not getattr(s, "torpedo_factor_used", False)
            for s in self.def_ships
        )
        if def_has_torp:
            return 8
        if att_has_torp:
            return 7
        return 6
    # ── Drawing ───────────────────────────────────────────────────────────────

    def _draw(self):
        self.screen.fill(_BG)
        w, h = self.screen.get_size()
        self._click_rects = []

        step_titles = {
            1: f"{self.att_label} — Assign Ship Positions",
            2: f"{self.att_label} — Choose Secret Die",
            3: f"{self.def_label} — Assign Ship Positions",
            4: f"{self.def_label} — Choose Secret Die",
            5: f"{self.att_label} — Assign Gunnery Targets",
            6: f"{self.def_label} — Assign Gunnery Targets",
            7: f"{self.att_label} — Assign Torpedo Targets",
            8: f"{self.def_label} — Assign Torpedo Targets",
        }
        title = self.font_hd.render(step_titles.get(self._step, ""), True, _GOLD)
        self.screen.blit(title, (self.MARGIN, self.MARGIN))
        step_info = self.font_sm.render(f"Step {self._step} of {self._max_step()}", True, _DIM)
        self.screen.blit(step_info, (self.MARGIN, self.MARGIN + 32))

        y = self.MARGIN + 70
        if self._step in (1, 3):
            y = self._draw_position_step(y, w)
        elif self._step in (2, 4):
            y = self._draw_die_step(y, w)
        elif self._step in (5, 6):
            y = self._draw_gunnery_target_step(y, w)
        elif self._step in (7, 8):
            y = self._draw_torpedo_target_step(y, w)

        self._draw_nav_buttons(h, w)

    def _draw_position_step(self, y: int, w: int) -> int:
        ships = self.att_ships if self._step == 1 else self.def_ships
        self.screen.blit(
            self.font_sm.render(
                "Click a position button to assign each ship. Crippled/Anchored ships are forced to Screen.",
                True, _DIM
            ),
            (self.MARGIN, y),
        )
        y += 28

        for i, ship in enumerate(ships):
            row_color = _PANEL if i % 2 == 0 else _ROW_ALT
            pygame.draw.rect(self.screen, row_color, (self.MARGIN, y, w - 2 * self.MARGIN, self.ROW_H - 2))
            forced = ship.status in ("Crippled", "Anchored", "Sunk")
            cur_pos = self._positions.get(ship, POSITION_GUNNERY)

            ship_label = f"{ship.name}  ({ship.type})"
            if ship.torpedo_factor > 0:
                ship_label += f"  TF:{ship.torpedo_factor}"
            if getattr(ship, "torpedo_factor_used", False):
                ship_label += "  [torps used]"
            if forced:
                ship_label += "  [forced Screen]"

            self.screen.blit(self.font_md.render(ship_label, True, _TEXT), (self.MARGIN + 8, y + 10))

            # Position buttons
            btn_x = w - self.MARGIN - 3 * (80 + 6)
            for pos in _POSITIONS:
                color = _POS_COLORS[pos] if cur_pos == pos else (60, 60, 70)
                if forced and pos != POSITION_SCREEN:
                    color = (40, 40, 45)
                brect = pygame.Rect(btn_x, y + 4, 80, 34)
                pygame.draw.rect(self.screen, color, brect, border_radius=4)
                lbl = self.font_sm.render(_POS_LABELS[pos], True, _WHITE)
                self.screen.blit(lbl, (brect.x + (80 - lbl.get_width()) // 2, brect.y + 8))
                if not forced:
                    self._click_rects.append((("pos", i, pos), brect))
                btn_x += 86

            y += self.ROW_H
        return y + 10

    def _draw_die_step(self, y: int, w: int) -> int:
        label_text = (
            f"{self.att_label}, secretly pick your die value (1–6)."
            if self._step == 2 else
            f"{self.def_label}, secretly pick your die value (1–6)."
        )
        self.screen.blit(self.font_md.render(label_text, True, _DIM), (self.MARGIN, y))
        y += 40

        die_w, die_h, gap = 70, 70, 14
        total_w = 6 * die_w + 5 * gap
        start_x = (w - total_w) // 2
        for face in range(1, 7):
            r = pygame.Rect(start_x + (face - 1) * (die_w + gap), y, die_w, die_h)
            color = _BTN_BLUE if face == self._die_choice else _PANEL
            pygame.draw.rect(self.screen, color, r, border_radius=8)
            pygame.draw.rect(self.screen, _HEADER, r, 2, border_radius=8)
            num = self.font_hd.render(str(face), True, _WHITE)
            self.screen.blit(num, (r.x + (die_w - num.get_width()) // 2, r.y + (die_h - num.get_height()) // 2))
            self._click_rects.append((("die", face), r))
        y += die_h + 16

        chosen = self.font_md.render(f"Your die: {self._die_choice}", True, _GOLD)
        self.screen.blit(chosen, ((w - chosen.get_width()) // 2, y))
        return y + 40

    def _draw_gunnery_target_step(self, y: int, w: int) -> int:
        ships  = self.att_ships if self._step == 5 else self.def_ships
        targets = self.def_ships if self._step == 5 else self.att_ships
        pos_map = (self._result.attacker_positions if self._step == 5
                   else self._result.defender_positions)
        sub = "Choose a target for each Gunnery-position ship."
        self.screen.blit(self.font_sm.render(sub, True, _DIM), (self.MARGIN, y))
        y += 28
        col2 = w // 2 - 30

        for i, ship in enumerate(ships):
            if pos_map.get(ship) != POSITION_GUNNERY:
                continue
            row_color = _PANEL if i % 2 == 0 else _ROW_ALT
            pygame.draw.rect(self.screen, row_color, (self.MARGIN, y, w - 2 * self.MARGIN, self.ROW_H - 2))
            self.screen.blit(
                self.font_md.render(f"{ship.name} ({ship.type}), GF:{ship.attack_factor}", True, _TEXT),
                (self.MARGIN + 8, y + 10),
            )
            left_r  = pygame.Rect(col2 - 32, y + 6, 28, 30)
            right_r = pygame.Rect(col2 + 270, y + 6, 28, 30)
            pygame.draw.rect(self.screen, _BTN_BLUE, left_r, border_radius=3)
            pygame.draw.rect(self.screen, _BTN_BLUE, right_r, border_radius=3)
            self.screen.blit(self.font_md.render("<", True, _WHITE), (left_r.x + 7, left_r.y + 4))
            self.screen.blit(self.font_md.render(">", True, _WHITE), (right_r.x + 7, right_r.y + 4))
            self._click_rects.append((("tgt_prev", i), left_r))
            self._click_rects.append((("tgt_next", i), right_r))

            tgt_idx = self._tgt_by_idx.get(i, 0)
            tgt_name = "No target" if not targets else targets[tgt_idx % len(targets)].name
            self.screen.blit(
                self.font_md.render(tgt_name, True, _GOLD),
                (col2 + 2, y + 10),
            )
            y += self.ROW_H
        return y + 10

    def _draw_torpedo_target_step(self, y: int, w: int) -> int:
        ships   = self.att_ships if self._step == 7 else self.def_ships
        targets = self.def_ships if self._step == 7 else self.att_ships
        pos_map = (self._result.attacker_positions if self._step == 7
                   else self._result.defender_positions)
        sub = "Choose a target for each Torpedo-position ship."
        self.screen.blit(self.font_sm.render(sub, True, _DIM), (self.MARGIN, y))
        y += 28
        col2 = w // 2 - 30

        for i, ship in enumerate(ships):
            if (pos_map.get(ship) != POSITION_TORPEDO
                    or ship.torpedo_factor <= 0
                    or getattr(ship, "torpedo_factor_used", False)):
                continue
            row_color = _PANEL if i % 2 == 0 else _ROW_ALT
            pygame.draw.rect(self.screen, row_color, (self.MARGIN, y, w - 2 * self.MARGIN, self.ROW_H - 2))
            self.screen.blit(
                self.font_md.render(f"{ship.name} ({ship.type}), TF:{ship.torpedo_factor}", True, _TEXT),
                (self.MARGIN + 8, y + 10),
            )
            left_r  = pygame.Rect(col2 - 32, y + 6, 28, 30)
            right_r = pygame.Rect(col2 + 270, y + 6, 28, 30)
            pygame.draw.rect(self.screen, _BTN_BLUE, left_r, border_radius=3)
            pygame.draw.rect(self.screen, _BTN_BLUE, right_r, border_radius=3)
            self.screen.blit(self.font_md.render("<", True, _WHITE), (left_r.x + 7, left_r.y + 4))
            self.screen.blit(self.font_md.render(">", True, _WHITE), (right_r.x + 7, right_r.y + 4))
            self._click_rects.append((("tgt_prev", i), left_r))
            self._click_rects.append((("tgt_next", i), right_r))

            tgt_idx = self._tgt_by_idx.get(i, 0)
            tgt_name = "No target" if not targets else targets[tgt_idx % len(targets)].name
            self.screen.blit(
                self.font_md.render(tgt_name, True, _GOLD),
                (col2 + 2, y + 10),
            )
            y += self.ROW_H
        return y + 10

    def _draw_nav_buttons(self, h: int, w: int):
        y = h - self.MARGIN - self.BTN_H
        # Cancel (always)
        cancel_r = pygame.Rect(self.MARGIN, y, self.BTN_W, self.BTN_H)
        pygame.draw.rect(self.screen, _BTN_RED, cancel_r, border_radius=5)
        lbl = self.font_md.render("Cancel", True, _WHITE)
        self.screen.blit(lbl, (cancel_r.x + (self.BTN_W - lbl.get_width()) // 2, cancel_r.y + 8))
        self._click_rects.append((("cancel",), cancel_r))

        # Next / Done
        action_label = "Done" if self._step == self._max_step() else "Next ▶"
        action_r = pygame.Rect(w - self.MARGIN - self.BTN_W, y, self.BTN_W, self.BTN_H)
        pygame.draw.rect(self.screen, _BTN_GREEN, action_r, border_radius=5)
        lbl2 = self.font_md.render(action_label, True, _WHITE)
        self.screen.blit(lbl2, (action_r.x + (self.BTN_W - lbl2.get_width()) // 2, action_r.y + 8))
        self._click_rects.append((("next",), action_r))

    # ── Click handling ────────────────────────────────────────────────────────

    def _handle_click(self, pos: tuple[int, int]):
        mx, my = pos
        for tag, rect in self._click_rects:
            if not rect.collidepoint(mx, my):
                continue

            if tag[0] == "cancel":
                self._running = False
                self._result  = None
                return

            if tag[0] == "next":
                self._commit_step()
                nxt = self._step + 1
                if nxt > self._max_step():
                    self._running = False
                else:
                    self._enter_step(nxt)
                return

            if tag[0] == "pos":
                _, ship_idx, new_pos = tag
                ships = self.att_ships if self._step == 1 else self.def_ships
                ship  = ships[ship_idx]
                if ship.status not in ("Crippled", "Anchored", "Sunk"):
                    self._positions[ship] = new_pos
                return

            if tag[0] == "die":
                self._die_choice = tag[1]
                return

            if tag[0] in ("tgt_prev", "tgt_next"):
                _, ship_idx = tag
                targets = self.def_ships if self._step in (5, 7) else self.att_ships
                if not targets:
                    return
                current = self._tgt_by_idx.get(ship_idx, 0)
                step    = -1 if tag[0] == "tgt_prev" else 1
                self._tgt_by_idx[ship_idx] = (current + step) % len(targets)
                return

    # ── Commit step data into result ─────────────────────────────────────────

    def _commit_step(self):
        if self._step == 1:
            self._result.attacker_positions = dict(self._positions)
        elif self._step == 2:
            self._result.attacker_die = self._die_choice
        elif self._step == 3:
            self._result.defender_positions = dict(self._positions)
        elif self._step == 4:
            self._result.defender_die = self._die_choice
        elif self._step == 5:
            targets = self.def_ships
            self._result.attacker_gunnery_targets = {
                self.att_ships[i]: targets[tidx % len(targets)]
                for i, tidx in self._tgt_by_idx.items()
                if targets
            }
        elif self._step == 6:
            targets = self.att_ships
            self._result.defender_gunnery_targets = {
                self.def_ships[i]: targets[tidx % len(targets)]
                for i, tidx in self._tgt_by_idx.items()
                if targets
            }
        elif self._step == 7:
            targets = self.def_ships
            self._result.attacker_torpedo_targets = {
                self.att_ships[i]: targets[tidx % len(targets)]
                for i, tidx in self._tgt_by_idx.items()
                if targets
            }
        elif self._step == 8:
            targets = self.att_ships
            self._result.defender_torpedo_targets = {
                self.def_ships[i]: targets[tidx % len(targets)]
                for i, tidx in self._tgt_by_idx.items()
                if targets
            }

