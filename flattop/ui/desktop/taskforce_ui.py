import sys
import os
import pygame

# Ensure the parent directory is in sys.path for module discovery
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..','..')))

# Import necessary classes from the operations chart models
from flattop.operations_chart_models import AirOperationsChart, TaskForce, Carrier, Base, Ship, AircraftType, AircraftOperationsStatus, AirOperationsConfiguration, AircraftFactory
from flattop.ui.desktop.base_ui import BaseUIDisplay  # <-- Use BaseUIDisplay instead of BaseDialog
from flattop.ui.desktop.ui_theme import (
    LINE_EXTRA,
    MARGIN,
    PADDING,
    SCROLLBAR_WIDTH,
    THEME_BG,
    THEME_BORDER,
    THEME_PANEL,
    THEME_SEPARATOR,
    THEME_TEXT,
    THEME_TEXT_HEADER,
    ScrollBar,
    get_font,
)

pygame.init()
FONT = get_font(32, bold=True)
SMALL_FONT = get_font(24)
CARRIER_SYMBOL = "🛩️"

class TaskForceScreen:
    def __init__(self, taskforce: TaskForce):
        self.taskforce = taskforce
        self.carrier_buttons = []
        self.base_dialog = None  # This will now be a BaseUIDisplay
        self.screen = None
        self.air_ops_chart : AirOperationsChart = None
        self.scroll_y = 0
        self.max_scroll = 0
        self.scrollbar = None
        self.list_rect = None

    def draw(self, surface):
        self.surface = surface

        win_width, win_height = self.surface.get_size()
        margin = MARGIN
        row_height = SMALL_FONT.get_height() + LINE_EXTRA + 4

        # Draw a popup background for the takforce details
        popup_width = int(win_width * 0.9)
        popup_height = int(win_height * 0.9)
        popup_rect = pygame.Rect(
            20,
            20,
            popup_width,
            popup_height
        )
        pygame.draw.rect(self.surface, THEME_BG, popup_rect)
        pygame.draw.rect(self.surface, THEME_BORDER, popup_rect, 2)

        y = popup_rect.top + margin
        title = FONT.render(f"TaskForce: {self.taskforce.name}", True, THEME_TEXT_HEADER)
        surface.blit(title, (popup_rect.left + margin, y))
        y += title.get_height() + PADDING
        ships_label = SMALL_FONT.render(f"Ships: {len(self.taskforce.ships)}", True, THEME_TEXT)
        surface.blit(ships_label, (popup_rect.left + margin, y))
        y += ships_label.get_height() + margin

        # Table headers
        headers = ["Name", "Type", "Attack", "AA", "Move", "Damage", "Air Ops"]
        col_widths = [140, 80, 60, 60, 60, 60, 120]
        x_positions = [popup_rect.left + margin + PADDING]
        for w in col_widths[:-1]:
            x_positions.append(x_positions[-1] + w)
        header_y = y
        for i, header in enumerate(headers):
            txt = SMALL_FONT.render(header, True, THEME_TEXT_HEADER)
            surface.blit(txt, (x_positions[i], header_y))
        y += SMALL_FONT.get_height() + PADDING
        pygame.draw.line(surface, THEME_SEPARATOR, (popup_rect.left + margin, y), (popup_rect.right - margin, y), 2)
        y += PADDING

        list_height = popup_rect.bottom - y - margin
        list_width = popup_rect.width - (2 * margin) - SCROLLBAR_WIDTH - PADDING
        self.list_rect = pygame.Rect(popup_rect.left + margin, y, list_width, list_height)
        pygame.draw.rect(surface, THEME_PANEL, self.list_rect)
        pygame.draw.rect(surface, THEME_SEPARATOR, self.list_rect, 1)

        rows_height = len(self.taskforce.ships) * row_height
        self.max_scroll = max(0, rows_height - self.list_rect.height)
        self.scroll_y = max(0, min(self.scroll_y, self.max_scroll))
        
        scrollbar_x = self.list_rect.right + PADDING  
        scrollbar_y = self.list_rect.top  
        scrollbar_height = self.list_rect.height  
        scrollbar_geometry = (scrollbar_x, scrollbar_y, scrollbar_height)  
        if (  
            not hasattr(self, "scrollbar")  
            or getattr(self, "_scrollbar_geometry", None) != scrollbar_geometry  
        ):
            self.scrollbar = ScrollBar(scrollbar_x, scrollbar_y, scrollbar_height)
            self._scrollbar_geometry = scrollbar_geometry
            list_surface = pygame.Surface((self.list_rect.width, max(self.list_rect.height, rows_height)))
        list_surface.fill(THEME_PANEL)

        self.carrier_buttons.clear()
        ship:Ship
        for row_index, ship in enumerate(self.taskforce.ships):
            # Get ship properties, fallback to "N/A" if not present
            name = ship.name
            ship_type = ship.type
            attack = ship.attack_factor
            defense = ship.anti_air_factor  # Changed from defense_factor to anti_air_factor
            move = ship.move_factor
            damage = ship.damage
            air_ops = ""
            is_carrier = isinstance(ship, Carrier)
            
            row = [name, ship_type, str(attack), str(defense), str(move), str(damage), air_ops]
            row_y = row_index * row_height
            for i, value in enumerate(row):
                txt = SMALL_FONT.render(value, True, THEME_TEXT)
                local_x = x_positions[i] - self.list_rect.left
                list_surface.blit(txt, (local_x, row_y))
            # Draw base symbol as clickable if carrier has base
            if is_carrier and ship.base:
                # Use a font that supports Unicode for the carrier symbol
                unicode_font = pygame.font.SysFont("Segoe UI Emoji", 24)  # Common font for emoji support
                symbol = unicode_font.render(CARRIER_SYMBOL, True, THEME_TEXT)
                local_x = x_positions[6] - self.list_rect.left
                rect = symbol.get_rect(topleft=(local_x, row_y))
                list_surface.blit(symbol, rect.topleft)
                self.carrier_buttons.append((rect, ship.base))
        surface.blit(
            list_surface,
            self.list_rect.topleft,
            pygame.Rect(0, self.scroll_y, self.list_rect.width, self.list_rect.height),
        )
        self.scrollbar.draw(surface, self.scroll_y, max(self.list_rect.height, rows_height), self.list_rect.height)

       

    def handle_event(self, event):
        if self.scrollbar:
            self.scroll_y = self.scrollbar.handle_event(event, self.scroll_y, self.max_scroll)
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            for rect, base in self.carrier_buttons:
                absolute_rect = rect.move(self.list_rect.left, self.list_rect.top - self.scroll_y)
                if absolute_rect.collidepoint(pos):
                    self.base_dialog = BaseUIDisplay(base, self.surface)  
                    self.base_dialog.air_op_chart = self.air_ops_chart
                    self.base_dialog.draw()  # Show the base dialog
                    self.base_dialog.handle_events()  # Handle any events for the dialog
                    pygame.display.flip()  # Update the display
                    break


def main():
    screen = pygame.display.set_mode((700, 400))
    pygame.display.set_caption("TaskForce Screen")
    clock = pygame.time.Clock()
    


    taskForce = TaskForce(1, "Allied Task Force 1", "Allied")
    carrierLexington = Carrier("Lexington", "CV", "operational", 1, 4, 2)
    carrierLexington.base._air_operations_config = AirOperationsConfiguration(
        name="Lexington",
        description="Configuration for air operations on Lexington",
        maximum_capacity=20,
        launch_factor_min=6,
        launch_factor_normal=12,
        launch_factor_max=24,
        ready_factors=6,
        plane_handling_type="SP"
    )
    carrierLexington.air_operations.set_operations_status(AircraftFactory.create(AircraftType.WILDCAT, count=8),AircraftOperationsStatus.READY)
    carrierLexington.air_operations.set_operations_status(AircraftFactory.create(AircraftType.DAUNTLESS, count=12),AircraftOperationsStatus.READY)
    carrierLexington.air_operations.set_operations_status(AircraftFactory.create(AircraftType.DEVASTATOR, count=4),AircraftOperationsStatus.READY)

    taskForce.add_ship(carrierLexington)  # Add the carrier to the task force
    taskForce.add_ship(Ship("Pensecola", "CA", "operational",5,2,2))
    taskForce.add_ship(Ship("Minneapolis", "CA", "operational",4,2,2))
    taskForce.add_ship(Ship("San Francisco", "CA", "operational",4,2,2))
    taskForce.add_ship(Ship("Indianapolis", "CA", "operational",4,2,2))
    for i in range(10):
        taskForce.add_ship(Ship(f"Destroyer {i+1}", "DD", "operational",1,1,2))

    tf_screen = TaskForceScreen(taskForce)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            tf_screen.handle_event(event)

        tf_screen.draw(screen)
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
