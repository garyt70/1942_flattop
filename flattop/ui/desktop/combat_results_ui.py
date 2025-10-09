"""
Requirements

- Air to Air Combat Results
- Base Combat Results
- Anti Aircraft Results
- Ship Combat Results

Display a summary at the top of the screen of the combat results for each category.

Then display the details for each category below all the summaries.

                Combat results array

                Air to Air combat result return
                result = {
                "interceptor_hits_on_escorts": AirCombatResult(),
                "escort_hits_on_interceptors": AirCombatResult(),
                "interceptor_hits_on_bombers": AirCombatResult(),
                "bomber_hits_on_interceptors": AirCombatResult(),
                "eliminated": {"interceptors": [], "escorts": [], "bombers": []}
        }

        Anti aircradt results
        result = {"anti_aircraft": AirCombatResult(),
                        "eliminated": {"interceptors": [], "escorts": [], "bombers": []}
                        }

        Base combat results
        results = {"bomber_hits": AirCombatResult(),
                   "eliminated": {"aircraft": []}
                        }
    
        Ship combat results
        result = {"bomber_hits": AirCombatResult(),
                        "eliminated": {"ships": []}
                        }

"""

import os
import pygame
import sys

from flattop.aircombat_engine import AirCombatResult

class CombatResultsList:
    """Displays a scrollable list of combat results that can be clicked to show details"""
    
    BG_COLOR = (30, 30, 30)
    TEXT_COLOR = (230, 230, 230)
    HOVER_COLOR = (60, 60, 80)
    SELECTED_COLOR = (80, 80, 100)
    PADDING = 12
    ITEM_HEIGHT = 40
    FONT_SIZE = 22
    FONT_NAME = None
    CLOSE_BUTTON_SIZE = (80, 30)

    def __init__(self, turn_results, screen=None, width=500, height=700):
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

        self.font = pygame.font.Font(self.FONT_NAME, self.FONT_SIZE)
        self.turn_results = turn_results
        self.width = width
        self.height = height
        self.scroll_y = 0
        self.max_scroll = max(0, len(turn_results) * self.ITEM_HEIGHT - height)
        self.content_surface = pygame.Surface((width, max(height, len(turn_results) * self.ITEM_HEIGHT)))
        self.close_button = pygame.Rect(
            width - self.CLOSE_BUTTON_SIZE[0] - self.PADDING,
            self.PADDING,
            self.CLOSE_BUTTON_SIZE[0],
            self.CLOSE_BUTTON_SIZE[1]
        )
        self.hover_index = -1

    def draw_text(self, text, x, y, color=None, surface=None):
        color = color or self.TEXT_COLOR
        text_surface = self.font.render(text, True, color)
        if surface is None:
            surface = self.content_surface
        surface.blit(text_surface, (x, y))

    def draw_close_button(self):
        mouse_pos = pygame.mouse.get_pos()
        button_color = self.HOVER_COLOR if self.close_button.collidepoint(mouse_pos) else self.BG_COLOR
        pygame.draw.rect(self.screen, button_color, self.close_button)
        close_text = self.font.render("Close", True, self.TEXT_COLOR)
        text_rect = close_text.get_rect(center=self.close_button.center)
        self.screen.blit(close_text, text_rect)

    def draw_list(self):
        self.content_surface.fill(self.BG_COLOR)
        
        # Draw each combat result as a list item
        for i, result in enumerate(self.turn_results):
            item_rect = pygame.Rect(0, i * self.ITEM_HEIGHT, self.width, self.ITEM_HEIGHT)
            
            # Highlight if mouse is hovering
            if i == self.hover_index:
                pygame.draw.rect(self.content_surface, self.HOVER_COLOR, item_rect)
            else:
                pygame.draw.rect(self.content_surface, self.BG_COLOR, item_rect)
                
            # Draw border
            pygame.draw.rect(self.content_surface, self.TEXT_COLOR, item_rect, 1)
            
            # Create summary text
            summary = f"Combat #{i+1}"
            if "air_to_air" in result:
                summary += " - Air Combat"
            if "anti_aircraft" in result:
                summary += " - AA Combat"
            if "base" in result:
                summary += " - Base Combat"
            if "ship" in result:
                summary += " - Ship Combat"
                
            self.draw_text(summary, self.PADDING, i * self.ITEM_HEIGHT + 10)

        # Draw the visible portion to the screen
        self.screen.fill(self.BG_COLOR)
        visible_region = pygame.Rect(0, self.scroll_y, self.width, self.height)
        self.screen.blit(self.content_surface, (0, 0), visible_region)
        
        # Draw close button on top
        self.draw_close_button()

    def handle_scroll(self, event):
        if event.type == pygame.MOUSEWHEEL:
            self.scroll_y = max(0, min(self.scroll_y - event.y * 20, self.max_scroll))

    def get_clicked_index(self, mouse_pos):
        """Convert mouse position to list item index"""
        y = mouse_pos[1] + self.scroll_y
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
                    if event.button == 1:  # Left click
                        if self.close_button.collidepoint(event.pos):
                            running = False
                        else:
                            clicked_index = self.get_clicked_index(event.pos)
                            if clicked_index >= 0:
                                # Show detailed view for clicked combat result.  Combat result history is a list of tuples.
                                combat_result = self.turn_results[clicked_index][1]
                                
                                a2a = combat_result.get("result_attacker_a2a")
                                aa = []
                                aa.append(combat_result.get("result_tf_anti_aircraft"))
                                aa.append(combat_result.get("result_base_anti_aircraft"))
                                ship = combat_result.get("result_attacker_ship_air_attack")
                                base = combat_result.get("result_attacker_base_air_attack")

                                result_data = {"air_to_air": a2a, "anti_aircraft": aa, "base": base, "ship": ship}
                                detail_view = CombatResultsScreen(
                                    result_data,
                                    self.screen,
                                    self.width,
                                    self.height
                                )
                                detail_view.run()
                                
                self.handle_scroll(event)
                
            # Update hover state
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
        BG_COLOR = (30, 30, 30)
        TEXT_COLOR = (230, 230, 230)
        SUMMARY_BG = (50, 50, 80)
        DETAIL_BG = (40, 40, 40)
        BUTTON_BG = (180, 30, 30)
        BUTTON_HOVER = (220, 40, 40)
        PADDING = 12
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
                self.font = pygame.font.Font(self.FONT_NAME, self.FONT_SIZE)
                self.combat_results = combat_results_dict
                self.width = width
                self.height = height
                self.scroll_y = 0
                self.max_scroll = 0
                self.content_surface = pygame.Surface((width, height * 2))  # Larger surface for scrolling
                self.close_button = pygame.Rect(
                    width - self.CLOSE_BUTTON_SIZE[0] - self.PADDING,
                    self.PADDING,
                    self.CLOSE_BUTTON_SIZE[0],
                    self.CLOSE_BUTTON_SIZE[1]
                )

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
                close_text = self.font.render("Close", True, self.TEXT_COLOR)
                text_rect = close_text.get_rect(center=self.close_button.center)
                self.screen.blit(close_text, text_rect)

        def draw_summary(self, y, label, summary):
                pygame.draw.rect(self.content_surface, self.SUMMARY_BG, (0, y, self.width, self.SUMMARY_HEIGHT))
                self.draw_text(f"{label}: {summary}", self.PADDING, y + 7)

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
                y += self.SUMMARY_HEIGHT + self.PADDING

                # --- Details ---
                y = self._draw_a2a_details(y, a2a)
                y += self.PADDING
                y = self._draw_aa_details(y, aa_list)
                y += self.PADDING
                y = self._draw_base_details(y, base)
                y += self.PADDING
                y = self._draw_ship_details(y, ship)

                # Update max scroll based on final y position
                self.max_scroll = max(0, y - self.height + self.SUMMARY_HEIGHT)

                # Draw the visible portion to the screen
                self.screen.fill(self.BG_COLOR)
                visible_region = pygame.Rect(0, self.scroll_y, self.width, self.height)
                self.screen.blit(self.content_surface, (0, 0), visible_region)
                
                # Draw close button on top
                self.draw_close_button()

        def handle_scroll(self, event):
                if event.type == pygame.MOUSEWHEEL:
                        self.scroll_y = max(0, min(self.scroll_y - event.y * 20, self.max_scroll))

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



