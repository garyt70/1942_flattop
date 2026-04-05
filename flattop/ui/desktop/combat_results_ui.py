

import os
import pygame
import sys

from flattop.aircombat_engine import AirCombatResult
from flattop.ui.desktop.ui_theme import (
        PADDING,
        SCROLLBAR_WIDTH,
        THEME_BG,
        THEME_BORDER,
        THEME_BTN_DANGER,
        THEME_BTN_DANGER_HOVER,
        THEME_PANEL,
        THEME_SCROLLBAR_TRACK,
        THEME_SEPARATOR,
        THEME_TEXT,
        THEME_TEXT_HEADER,
        ScrollBar,
        get_font,
)

class CombatResultsList:
    """Displays a scrollable list of combat results that can be clicked to show details"""
    BG_COLOR = THEME_BG
    TEXT_COLOR = THEME_TEXT
    HOVER_COLOR = THEME_PANEL
    SELECTED_COLOR = THEME_PANEL
    PADDING = PADDING
    ITEM_HEIGHT = 40
    FONT_SIZE = 22
    FONT_NAME = None
    CLOSE_BUTTON_SIZE = (80, 30)

    def __init__(self, turn_results, screen=None, width=900, height=700):
            """
            Args:
                    turn_results: List of combat results from TurnManager
                    screen: Existing pygame screen or None to create new one
                    width: Screen width
                    height: Screen height
            """
            self.external_screen = screen is not None
            if screen is None:
                    pygame.init()
                    self.screen = pygame.display.set_mode((width, height))
                    pygame.display.set_caption("Combat Results List")
            else:
                    self.screen = screen

            self.font = get_font(self.FONT_SIZE)
            self.turn_results = turn_results
            self.width = width
            self.height = height
            self.header_height = self.CLOSE_BUTTON_SIZE[1] + (2 * self.PADDING)
            self.viewport_height = self.height - self.header_height
            self.scroll_y = 0
            self.viewport_width = width - SCROLLBAR_WIDTH - (2 * self.PADDING)
            self.content_height = max(self.viewport_height, len(turn_results) * self.ITEM_HEIGHT)
            self.max_scroll = max(0, self.content_height - self.viewport_height)
            self.content_surface = pygame.Surface((self.viewport_width, self.content_height))
            self.close_button = pygame.Rect(
                    width - self.CLOSE_BUTTON_SIZE[0] - self.PADDING,
                    (self.header_height - self.CLOSE_BUTTON_SIZE[1]) // 2,
                    self.CLOSE_BUTTON_SIZE[0],
                    self.CLOSE_BUTTON_SIZE[1],
            )
            self.hover_index = -1
            self.scrollbar = ScrollBar(width - SCROLLBAR_WIDTH - self.PADDING, self.header_height, self.viewport_height)

    def draw_text(self, text, x, y, color=None, surface=None):
            color = color or self.TEXT_COLOR
            text_surface = self.font.render(text, True, color)
            if surface is None:
                    surface = self.content_surface
            surface.blit(text_surface, (x, y))

    def draw_close_button(self):
            mouse_pos = pygame.mouse.get_pos()
            button_color = THEME_BTN_DANGER_HOVER if self.close_button.collidepoint(mouse_pos) else THEME_BTN_DANGER
            pygame.draw.rect(self.screen, button_color, self.close_button)
            pygame.draw.rect(self.screen, THEME_BORDER, self.close_button, 1)
            close_text = self.font.render("Close", True, self.TEXT_COLOR)
            text_rect = close_text.get_rect(center=self.close_button.center)
            self.screen.blit(close_text, text_rect)

    def draw_header(self, title):
            header_rect = pygame.Rect(0, 0, self.width, self.header_height)
            pygame.draw.rect(self.screen, THEME_PANEL, header_rect)
            pygame.draw.line(self.screen, THEME_SEPARATOR, (0, self.header_height - 1), (self.width, self.header_height - 1), 1)
            title_surf = get_font(self.FONT_SIZE + 2, bold=True).render(title, True, THEME_TEXT_HEADER)
            self.screen.blit(title_surf, (self.PADDING, self.PADDING))
            self.draw_close_button()

    def draw_list(self):
            self.content_surface.fill(self.BG_COLOR)

            for i, result in enumerate(self.turn_results):
                    item_rect = pygame.Rect(0, i * self.ITEM_HEIGHT, self.viewport_width, self.ITEM_HEIGHT)
                    if i == self.hover_index:
                            pygame.draw.rect(self.content_surface, self.HOVER_COLOR, item_rect)
                    else:
                            pygame.draw.rect(self.content_surface, self.BG_COLOR, item_rect)
                    pygame.draw.rect(self.content_surface, THEME_BORDER, item_rect, 1)

                    summary = f"Combat #{i+1}"
                    if "air_to_air" in result:
                            summary += " - Air Combat"
                    if "anti_aircraft" in result:
                            summary += " - AA Combat"
                    if "base" in result:
                            summary += " - Base Combat"
                    if "ship" in result:
                            summary += " - Ship Combat"
                    if "surface" in result:
                            summary += " - Surface Combat"

                    self.draw_text(summary, self.PADDING, i * self.ITEM_HEIGHT + 10)

            self.screen.fill(self.BG_COLOR)
            self.draw_header("Combat Results")
            visible_region = pygame.Rect(0, self.scroll_y, self.viewport_width, self.viewport_height)
            self.screen.blit(self.content_surface, (self.PADDING, self.header_height), visible_region)
            self.scrollbar.draw(self.screen, self.scroll_y, self.content_height, self.viewport_height)

    def handle_scroll(self, event):
            self.scroll_y = self.scrollbar.handle_event(event, self.scroll_y, self.max_scroll)

    def get_clicked_index(self, mouse_pos):
            """Convert mouse position to list item index"""
            if mouse_pos[0] >= self.viewport_width + self.PADDING or mouse_pos[1] < self.header_height:
                    return -1
            y = (mouse_pos[1] - self.header_height) + self.scroll_y
            index = y // self.ITEM_HEIGHT
            if 0 <= index < len(self.turn_results):
                    return index
            return -1

    def update_hover(self, mouse_pos):
            """Update hover highlighting based on mouse position"""
            self.hover_index = self.get_clicked_index(mouse_pos)

    def run(self):
            clock = pygame.time.Clock()
            running = True

            while running:
                    for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                    running = False

                            elif event.type == pygame.MOUSEBUTTONDOWN:
                                    if event.button == 1:
                                            if self.close_button.collidepoint(event.pos):
                                                    running = False
                                            else:
                                                    clicked_index = self.get_clicked_index(event.pos)
                                                    if clicked_index >= 0:
                                                            combat_result = self.turn_results[clicked_index][1]
                                                            a2a = combat_result.get("result_attacker_a2a")
                                                            aa = [
                                                                    combat_result.get("result_tf_anti_aircraft"),
                                                                    combat_result.get("result_base_anti_aircraft"),
                                                            ]
                                                            ship = combat_result.get("result_attacker_ship_air_attack")
                                                            base = combat_result.get("result_attacker_base_air_attack")
                                                            surface = combat_result.get("result_surface_combat")

                                                            result_data = {
                                                                    "air_to_air": a2a,
                                                                    "anti_aircraft": aa,
                                                                    "base": base,
                                                                    "ship": ship,
                                                                    "surface": surface,
                                                            }
                                                            detail_view = CombatResultsScreen(
                                                                    result_data,
                                                                    self.screen,
                                                                    self.width,
                                                                    self.height,
                                                            )
                                                            detail_view.run()

                            self.handle_scroll(event)

                    mouse_pos = pygame.mouse.get_pos()
                    self.update_hover(mouse_pos)
                    self.draw_list()
                    pygame.display.flip()
                    clock.tick(30)

            if not self.external_screen:
                    pygame.quit()
                    sys.exit()

# Keep existing CombatResultsScreen class
class CombatResultsScreen:

        BG_COLOR = THEME_BG
        TEXT_COLOR = THEME_TEXT
        SUMMARY_BG = THEME_PANEL
        DETAIL_BG = THEME_BG
        BUTTON_BG = THEME_BTN_DANGER
        BUTTON_HOVER = THEME_BTN_DANGER_HOVER
        PADDING = PADDING
        SUMMARY_HEIGHT = 38
        DETAIL_LINE_HEIGHT = 26
        FONT_SIZE = 22
        FONT_NAME = None
        CLOSE_BUTTON_SIZE = (80, 30)

        def __init__(self, combat_results_dict, screen=None, width=900, height=700):
                self.external_screen = screen is not None
                if screen is None:
                        pygame.init()
                        self.screen = pygame.display.set_mode((width, height))
                        pygame.display.set_caption("Combat Results")
                else:
                        self.screen = screen
                self.font = get_font(self.FONT_SIZE)
                self.combat_results = combat_results_dict
                self.width = width
                self.height = height
                self.header_height = self.CLOSE_BUTTON_SIZE[1] + (2 * self.PADDING)
                self.viewport_height = self.height - self.header_height
                self.scroll_y = 0
                self.max_scroll = 0
                self.viewport_width = width - SCROLLBAR_WIDTH - (2 * self.PADDING)
                self.content_surface = pygame.Surface((self.viewport_width, max(self.viewport_height * 2, self.viewport_height)))
                self.close_button = pygame.Rect(
                        width - self.CLOSE_BUTTON_SIZE[0] - self.PADDING,
                        (self.header_height - self.CLOSE_BUTTON_SIZE[1]) // 2,
                        self.CLOSE_BUTTON_SIZE[0],
                        self.CLOSE_BUTTON_SIZE[1]
                )
                self.scrollbar = ScrollBar(width - SCROLLBAR_WIDTH - self.PADDING, self.header_height, self.viewport_height)

        def draw_text(self, text, x, y, color=None, surface=None):
                color = color or self.TEXT_COLOR
                text_surface = self.font.render(text, True, color)
                if surface is None:
                        surface = self.content_surface
                surface.blit(text_surface, (x, y))

        def draw_close_button(self):
                mouse_pos = pygame.mouse.get_pos()
                button_color = self.BUTTON_HOVER if self.close_button.collidepoint(mouse_pos) else self.BUTTON_BG
                pygame.draw.rect(self.screen, button_color, self.close_button)
                pygame.draw.rect(self.screen, THEME_BORDER, self.close_button, 1)
                close_text = self.font.render("Close", True, self.TEXT_COLOR)
                text_rect = close_text.get_rect(center=self.close_button.center)
                self.screen.blit(close_text, text_rect)

        def draw_header(self, title):
                header_rect = pygame.Rect(0, 0, self.width, self.header_height)
                pygame.draw.rect(self.screen, THEME_PANEL, header_rect)
                pygame.draw.line(self.screen, THEME_SEPARATOR, (0, self.header_height - 1), (self.width, self.header_height - 1), 1)
                title_surf = get_font(self.FONT_SIZE + 2, bold=True).render(title, True, THEME_TEXT_HEADER)
                self.screen.blit(title_surf, (self.PADDING, self.PADDING))
                self.draw_close_button()

        def draw_summary(self, y, label, summary):
                pygame.draw.rect(self.content_surface, self.SUMMARY_BG, (0, y, self.viewport_width, self.SUMMARY_HEIGHT))
                pygame.draw.rect(self.content_surface, THEME_SEPARATOR, (0, y, self.viewport_width, self.SUMMARY_HEIGHT), 1)
                self.draw_text(f"{label}: {summary}", self.PADDING, y + 7, color=THEME_TEXT_HEADER)

        def draw_results(self):
                self.content_surface.fill(self.BG_COLOR)
                y = 0
                # --- Summaries ---
                a2a = self.combat_results.get("air_to_air", {})
                a2a_summary = self._make_a2a_summary(a2a)
                self.draw_summary(y, "Air-to-Air", a2a_summary)
                y += self.SUMMARY_HEIGHT
                aa_list = self.combat_results.get("anti_aircraft", [])
                aa_summary = self._make_aa_summary(aa_list)
                self.draw_summary(y, "Anti-Aircraft", aa_summary)
                y += self.SUMMARY_HEIGHT
                base = self.combat_results.get("base", {})
                base_summary = self._make_base_summary(base)
                self.draw_summary(y, "Base", base_summary)
                y += self.SUMMARY_HEIGHT
                ship = self.combat_results.get("ship", {})
                ship_summary = self._make_ship_summary(ship)
                self.draw_summary(y, "Ship", ship_summary)
                y += self.SUMMARY_HEIGHT
                surface = self.combat_results.get("surface", {})
                surface_summary = self._make_surface_summary(surface)
                self.draw_summary(y, "Surface", surface_summary)
                y += self.SUMMARY_HEIGHT + self.PADDING

                # --- Details ---
                y = self._draw_a2a_details(y, a2a)
                y += self.PADDING
                y = self._draw_aa_details(y, aa_list)
                y += self.PADDING
                y = self._draw_base_details(y, base)
                y += self.PADDING
                y = self._draw_ship_details(y, ship)
                y += self.PADDING
                y = self._draw_surface_details(y, surface)

                # Update max scroll based on final y position
                self.max_scroll = max(0, y - self.viewport_height)

                # Draw the visible portion to the screen
                self.screen.fill(self.BG_COLOR)
                self.draw_header("Combat Result Details")
                visible_region = pygame.Rect(0, self.scroll_y, self.viewport_width, self.viewport_height)
                self.screen.blit(self.content_surface, (self.PADDING, self.header_height), visible_region)
                self.scrollbar.draw(self.screen, self.scroll_y, max(self.content_surface.get_height(), y), self.viewport_height)

        def handle_scroll(self, event):
                self.scroll_y = self.scrollbar.handle_event(event, self.scroll_y, self.max_scroll)

        def _make_a2a_summary(self, a2a):
                if not a2a:
                        return "No air-to-air combat."
                hits = []
                for k in ["interceptor_hits_on_escorts", "escort_hits_on_interceptors", "interceptor_hits_on_bombers", "bomber_hits_on_interceptors"]:
                        v = a2a.get(k)
                        if v and hasattr(v, "hits") and v.hits:
                                total = sum(v.hits.values())
                                hits.append(f"{k.replace('_', ' ').title()}: {total}")
                elim = a2a.get("eliminated", {})
                elim_str = ", ".join(f"{k}: {len(v)}" for k, v in elim.items() if v)
                parts = hits
                if elim_str:
                        parts.append(f"Eliminated: {elim_str}")
                return ", ".join(parts) if parts else "No air-to-air combat."

        def _make_aa_summary(self, aa_list):
                if not aa_list:
                        return "No AA combat."
                hits = 0
                elim_parts = []
                for aa in aa_list:
                        if not aa:
                                continue
                        v = aa.get("anti_aircraft") if isinstance(aa, dict) else None
                        if v and hasattr(v, "hits") and v.hits:
                                hits += sum(v.hits.values())
                        elim = aa.get("eliminated", {}) if isinstance(aa, dict) else {}
                        for k, v in elim.items():
                                if v:
                                        elim_parts.append(f"{k}: {len(v)}")
                parts = []
                if hits:
                        parts.append(f"Hits: {hits}")
                if elim_parts:
                        parts.append(f"Eliminated: {', '.join(elim_parts)}")
                return ", ".join(parts) if parts else "No AA combat."

        def _make_base_summary(self, base):
                if not base:
                        return "No base combat."
                v = base.get("bomber_hits")
                elim = base.get("eliminated", {})
                hits = 0
                if v and hasattr(v, "hits") and v.hits:
                        hits = sum(v.hits.values())
                elim_str = ", ".join(f"{k}: {len(val)}" for k, val in elim.items() if val)
                parts = []
                if hits:
                        parts.append(f"Hits: {hits}")
                if elim_str:
                        parts.append(f"Eliminated: {elim_str}")
                return ", ".join(parts) if parts else "No base combat."

        def _make_ship_summary(self, ship_list):
                if not ship_list:
                        return "No ship combat."
                hits = 0
                elim_parts = []
                for ship in ship_list:
                        if not ship:
                                continue
                        v = ship.get("bomber_hits") if isinstance(ship, dict) else None
                        if v and hasattr(v, "hits") and v.hits:
                                hits += sum(v.hits.values())
                        elim = ship.get("eliminated", {}) if isinstance(ship, dict) else {}
                        for k, val in elim.items():
                                if val:
                                        elim_parts.append(f"{k}: {len(val)}")
                parts = []
                if hits:
                        parts.append(f"Hits: {hits}")
                if elim_parts:
                        parts.append(f"Eliminated: {', '.join(elim_parts)}")
                return ", ".join(parts) if parts else "No ship combat."

        def _draw_a2a_details(self, y, a2a):
                self.draw_text("Air-to-Air Details:", self.PADDING, y)
                y += self.DETAIL_LINE_HEIGHT
                for k in ["interceptor_hits_on_escorts", "escort_hits_on_interceptors", "interceptor_hits_on_bombers", "bomber_hits_on_interceptors"]:
                        v = a2a.get(k) if a2a else None
                        lines = self._aircombat_result_to_lines(v)
                        # Add story_line if present
                        if v and hasattr(v, "story_line") and v.story_line:
                                for story in v.story_line:
                                        self.draw_text(f"{k.replace('_', ' ').title()} Story: {story}", self.PADDING * 2, y)
                                        y += self.DETAIL_LINE_HEIGHT
                        for line in lines:
                                self.draw_text(f"{k.replace('_', ' ').title()}: {line}", self.PADDING * 2, y)
                                y += self.DETAIL_LINE_HEIGHT
                for line in self._eliminated_to_lines(a2a.get("eliminated", {}) if a2a else {}):
                        self.draw_text(line, self.PADDING * 2, y)
                        y += self.DETAIL_LINE_HEIGHT
                return y

        def _draw_aa_details(self, y, aa_list):
                self.draw_text("Anti-Aircraft Details:", self.PADDING, y)
                y += self.DETAIL_LINE_HEIGHT
                for aa in aa_list:
                        v = aa.get("anti_aircraft") if aa else None
                        # Add story_line if present
                        if v and hasattr(v, "story_line") and v.story_line:
                                for story in v.story_line:
                                        self.draw_text(f"AA Story: {story}", self.PADDING * 2, y)
                                        y += self.DETAIL_LINE_HEIGHT
                        for line in self._aircombat_result_to_lines(v):
                                self.draw_text(line, self.PADDING * 2, y)
                                y += self.DETAIL_LINE_HEIGHT
                        for line in self._eliminated_to_lines(aa.get("eliminated", {}) if aa else {}):
                                self.draw_text(line, self.PADDING * 2, y)
                                y += self.DETAIL_LINE_HEIGHT
                return y

        def _draw_base_details(self, y, base):
                self.draw_text("Base Details:", self.PADDING, y)
                y += self.DETAIL_LINE_HEIGHT
                v = base.get("bomber_hits") if base else None
                # Add story_line if present
                if v and hasattr(v, "story_line") and v.story_line:
                        for story in v.story_line:
                                self.draw_text(f"Base Story: {story}", self.PADDING * 2, y)
                                y += self.DETAIL_LINE_HEIGHT
                for line in self._aircombat_result_to_lines(v):
                        self.draw_text(line, self.PADDING * 2, y)
                        y += self.DETAIL_LINE_HEIGHT
                for line in self._eliminated_to_lines(base.get("eliminated", {}) if base else {}):
                        self.draw_text(line, self.PADDING * 2, y)
                        y += self.DETAIL_LINE_HEIGHT
                return y

        def _draw_ship_details(self, y, ship_list):
                self.draw_text("Ship Details:", self.PADDING, y)
                y += self.DETAIL_LINE_HEIGHT
                if not ship_list:
                        self.draw_text("No ship combat.", self.PADDING * 2, y)
                        y += self.DETAIL_LINE_HEIGHT
                        return y
                for ship in ship_list:
                        v = ship.get("bomber_hits") if ship else None
                        # Add story_line if present
                        if v and hasattr(v, "story_line") and v.story_line:
                                for story in v.story_line:
                                        self.draw_text(f"Ship Story: {story}", self.PADDING * 2, y)
                                        y += self.DETAIL_LINE_HEIGHT
                        for line in self._aircombat_result_to_lines(v):
                                self.draw_text(line, self.PADDING * 2, y)
                                y += self.DETAIL_LINE_HEIGHT
                        for line in self._eliminated_to_lines(ship.get("eliminated", {}) if ship else {}):
                                self.draw_text(line, self.PADDING * 2, y)
                                y += self.DETAIL_LINE_HEIGHT
                return y

        def _make_surface_summary(self, surface):
                if not surface:
                        return "No surface combat."
                bht = surface.get("bht", "?")
                att_destroyed = surface.get("attacker_destroyed", surface.get("attacker", {}).get("sunk_ships", []))
                def_destroyed = surface.get("defender_destroyed", surface.get("defender", {}).get("sunk_ships", []))

                if isinstance(att_destroyed, bool):
                        att_sunk = 1 if att_destroyed else 0
                elif isinstance(att_destroyed, (list, tuple, set, dict)):
                        att_sunk = len(att_destroyed)
                else:
                        att_sunk = 0

                if isinstance(def_destroyed, bool):
                        def_sunk = 1 if def_destroyed else 0
                elif isinstance(def_destroyed, (list, tuple, set, dict)):
                        def_sunk = len(def_destroyed)
                else:
                        def_sunk = 0

                return f"BHT {bht} | Att sunk: {att_sunk}, Def sunk: {def_sunk}"

        def _draw_surface_details(self, y, surface):
                def _as_entries(value):
                        if value is None:
                                return []
                        if isinstance(value, dict):
                                return [value]
                        if isinstance(value, (list, tuple)):
                                return [v for v in value if isinstance(v, dict)]
                        return []

                self.draw_text("Surface Combat Details:", self.PADDING, y)
                y += self.DETAIL_LINE_HEIGHT
                if not surface:
                        self.draw_text("No surface combat.", self.PADDING * 2, y)
                        y += self.DETAIL_LINE_HEIGHT
                        return y

                # Header line: BHT and dice
                bht = surface.get("bht")
                att_die = surface.get("attacker_die")
                def_die = surface.get("defender_die")
                if bht is not None:
                        dice_str = f"  (Att die {att_die} + Def die {def_die})" if att_die and def_die else ""
                        self.draw_text(f"BHT = {bht}{dice_str}", self.PADDING * 2, y)
                        y += self.DETAIL_LINE_HEIGHT

                # Gunnery phase
                self.draw_text("Gunnery Phase:", self.PADDING * 2, y)
                y += self.DETAIL_LINE_HEIGHT
                for side_key, gunnery_key in (("Attacker", "attacker_gunnery"), ("Defender", "defender_gunnery")):
                        phase_list = _as_entries(surface.get(gunnery_key))
                        if not phase_list:
                                # Fall back to legacy story_line
                                legacy = surface.get("attacker" if side_key == "Attacker" else "defender", {})
                                phase_list = [{"story_line": legacy.get("story_line", []),
                                               "sunk_ships": legacy.get("sunk_ships", [])}]
                        for entry in phase_list:
                                hits = entry.get("hits", 0)
                                if isinstance(hits, dict):
                                        hits = sum(hits.values())
                                target = entry.get("target_name", "")
                                story = entry.get("story_line", [])
                                sunk = entry.get("sunk", entry.get("sunk_ships", []))
                                label = f"{side_key}: {target} — {hits} hit(s)" if target else f"{side_key}: {hits} hit(s)"
                                self.draw_text(label, self.PADDING * 3, y)
                                y += self.DETAIL_LINE_HEIGHT
                                for line in story:
                                        self.draw_text(line, self.PADDING * 4, y, color=(200, 200, 180))
                                        y += self.DETAIL_LINE_HEIGHT
                                if sunk:
                                        self.draw_text(f"Sunk: {', '.join(sunk)}", self.PADDING * 4, y, color=(255, 100, 100))
                                        y += self.DETAIL_LINE_HEIGHT

                # Torpedo phase
                has_torpedo = surface.get("attacker_torpedo") or surface.get("defender_torpedo")
                if has_torpedo:
                        self.draw_text("Torpedo Phase:", self.PADDING * 2, y)
                        y += self.DETAIL_LINE_HEIGHT
                        for side_key, torp_key in (("Attacker", "attacker_torpedo"), ("Defender", "defender_torpedo")):
                                for entry in _as_entries(surface.get(torp_key)):
                                        hits = entry.get("hits", 0)
                                        if isinstance(hits, dict):
                                                hits = sum(hits.values())
                                        target = entry.get("target_name", "")
                                        sunk = entry.get("sunk", entry.get("sunk_ships", []))
                                        label = f"{side_key}: {target} — {hits} hit(s)" if target else f"{side_key}: {hits} hit(s)"
                                        self.draw_text(label, self.PADDING * 3, y)
                                        y += self.DETAIL_LINE_HEIGHT
                                        if sunk:
                                                self.draw_text(f"Sunk: {', '.join(sunk)}", self.PADDING * 4, y, color=(255, 100, 100))
                                                y += self.DETAIL_LINE_HEIGHT

                # Breakthrough phase
                bt = surface.get("breakthrough")
                if bt:
                        self.draw_text("Breakthrough:", self.PADDING * 2, y)
                        y += self.DETAIL_LINE_HEIGHT
                        bt_side = bt.get("side", "?")
                        bt_hits = bt.get("hits", 0)
                        bt_sunk = bt.get("sunk", [])
                        self.draw_text(f"{bt_side} breakthrough — {bt_hits} hit(s)", self.PADDING * 3, y)
                        y += self.DETAIL_LINE_HEIGHT
                        if bt_sunk:
                                self.draw_text(f"Sunk: {', '.join(bt_sunk)}", self.PADDING * 4, y, color=(255, 100, 100))
                                y += self.DETAIL_LINE_HEIGHT

                # Final totals
                att_destroyed = surface.get("attacker_destroyed", [])
                def_destroyed = surface.get("defender_destroyed", [])

                if isinstance(att_destroyed, bool):
                        att_lost_text = "all ships" if att_destroyed else "none"
                elif isinstance(att_destroyed, (list, tuple, set)):
                        att_lost_text = ", ".join(att_destroyed) or "none"
                else:
                        att_lost_text = "none"

                if isinstance(def_destroyed, bool):
                        def_lost_text = "all ships" if def_destroyed else "none"
                elif isinstance(def_destroyed, (list, tuple, set)):
                        def_lost_text = ", ".join(def_destroyed) or "none"
                else:
                        def_lost_text = "none"

                self.draw_text(f"Attacker lost: {att_lost_text}", self.PADDING * 2, y)
                y += self.DETAIL_LINE_HEIGHT
                self.draw_text(f"Defender lost: {def_lost_text}", self.PADDING * 2, y)
                y += self.DETAIL_LINE_HEIGHT
                return y

        def _aircombat_result_to_lines(self, result):
                if result is None:
                        return ["No result."]
                s = str(result)
                return s.strip().splitlines() if s.strip() else ["No hits."]

        def _eliminated_to_lines(self, elim_dict):
                lines = []
                if not elim_dict:
                        return lines
                for k, v in elim_dict.items():
                        if v:
                                lines.append(f"Eliminated {k}: {', '.join(str(x) for x in v)}")
                return lines

        def run(self):
                clock = pygame.time.Clock()
                running = True
                while running:
                        for event in pygame.event.get():
                                if event.type == pygame.QUIT:
                                        running = False
                                elif event.type == pygame.MOUSEBUTTONDOWN:
                                        if event.button == 1:  # Left click
                                                if self.close_button.collidepoint(event.pos):
                                                        running = False
                                self.handle_scroll(event)

                        self.draw_results()
                        pygame.display.flip()
                        clock.tick(30)

                if not self.external_screen:
                        pygame.quit()
                        sys.exit()



