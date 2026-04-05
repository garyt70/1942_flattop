import pygame
import sys
from flattop.operations_chart_models import AirFormation, Aircraft
from flattop.ui.desktop.base_ui import AircraftDisplay
from flattop.ui.desktop.ui_theme import MARGIN, PADDING, THEME_BG, THEME_BORDER, THEME_SEPARATOR, THEME_TEXT_HEADER, get_font

class AirFormationUI:
    def __init__(self, air_formation:AirFormation, screen, x=10, y=10):
        self.air_formation = air_formation
        self.screen = screen
        self.x = x
        self.y = y
        self.height_btn_lst = []

    def draw(self):
        win_width, win_height = self.screen.get_size()
        margin = MARGIN

        
        header_font = get_font(28, bold=True)
        popup_width = int(win_width - (2 * margin))
        popup_height = int(win_height - (2 * margin))
        popup_rect = pygame.Rect(
            margin,
            margin,
            popup_width,
            popup_height
        )
        pygame.draw.rect(self.screen, THEME_BG, popup_rect)
        pygame.draw.rect(self.screen, THEME_BORDER, popup_rect, 2)

        # Draw header
        header = f"Air Formation: {self.air_formation.name}"
        header_surf = header_font.render(header, True, THEME_TEXT_HEADER)
        header_rect = header_surf.get_rect(centerx=popup_rect.centerx, top=popup_rect.top + margin)
        self.screen.blit(header_surf, header_rect)
        separator_y = header_rect.bottom + PADDING
        pygame.draw.line(self.screen, THEME_SEPARATOR, (popup_rect.left + margin, separator_y), (popup_rect.right - margin, separator_y), 1)

        # Draw aircraft list header and list
        y = separator_y + PADDING
        y = AircraftDisplay.draw_aircraft_list_header(self.screen, self.air_formation.aircraft, popup_rect.left + margin, y)
        y, btn_list = AircraftDisplay.draw_aircraft_list_with_height_btn(self.screen, self.air_formation.aircraft, popup_rect.left + margin, y + 5)
        self.height_btn_lst = btn_list
        pygame.display.flip()

        
    def handle_events(self):
         # Wait for user to close popup
        waiting = True
        while waiting:
            for popup_event in pygame.event.get():
                if popup_event.type == pygame.KEYDOWN or popup_event.type == pygame.QUIT:
                    waiting = False
                    if popup_event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                elif popup_event.type == pygame.MOUSEBUTTONDOWN:
                    waiting = False
                    mx, my = popup_event.pos
                    for btn in self.height_btn_lst:
                        if btn.collidepoint(mx, my):
                            waiting = True
                            btn.handle_click(popup_event)
                            pygame.display.flip()
