import pygame
import sys
from flattop.operations_chart_models import AirFormation, Aircraft
from flattop.ui.desktop.base_ui import AircraftDisplay

class AirFormationUI:
    def __init__(self, air_formation:AirFormation, screen, x=10, y=10):
        self.air_formation = air_formation
        self.screen = screen
        self.x = x
        self.y = y
        self.height_btn_lst = []

    def draw(self):
        win_width, win_height = self.screen.get_size()
        margin = 10

        
        font = pygame.font.SysFont(None, 24)
        header_font = pygame.font.SysFont(None, 28, bold=True)
        popup_width = int(win_width * 0.98)
        popup_height = int(win_height * 0.98)
        popup_rect = pygame.Rect(
            10,
            10,
            popup_width,
            popup_height
        )
        pygame.draw.rect(self.screen, (50, 50, 50), popup_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), popup_rect, 2)

        # Draw header
        header = f"Air Formation: {self.air_formation.name}"
        header_font = pygame.font.SysFont(None, 28, bold=True)
        header_surf = header_font.render(header, True, (255, 255, 0))
        self.screen.blit(header_surf, (popup_rect.left + margin, popup_rect.top + margin))

        # Draw aircraft list header and list
        y = popup_rect.top + margin + header_surf.get_height() + margin // 2
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
