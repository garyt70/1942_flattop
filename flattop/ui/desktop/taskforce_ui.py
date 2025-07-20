import sys
import os
import pygame

# Ensure the parent directory is in sys.path for module discovery
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..','..')))

# Import necessary classes from the operations chart models
from flattop.operations_chart_models import AirOperationsChart, TaskForce, Carrier, Base, Ship, AircraftType, AircraftOperationsStatus, AirOperationsConfiguration, AircraftFactory
from flattop.ui.desktop.base_ui import BaseUIDisplay  # <-- Use BaseUIDisplay instead of BaseDialog

pygame.init()
FONT = pygame.font.SysFont(None, 32)
SMALL_FONT = pygame.font.SysFont(None, 24)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (220, 220, 220)
CARRIER_SYMBOL = "🛩️"

class TaskForceScreen:
    def __init__(self, taskforce: TaskForce):
        self.taskforce = taskforce
        self.carrier_buttons = []
        self.base_dialog = None  # This will now be a BaseUIDisplay
        self.screen = None
        self.air_ops_chart : AirOperationsChart = None

    def draw(self, surface):
        self.surface = surface

        win_width, win_height = self.surface.get_size()
        margin = 10

        # Draw a popup background for the takforce details
        font = pygame.font.SysFont(None, 24)
        header_font = pygame.font.SysFont(None, 28, bold=True)
        popup_width = int(win_width * 0.9)
        popup_height = int(win_height * 0.9)
        popup_rect = pygame.Rect(
            20,
            20,
            popup_width,
            popup_height
        )
        pygame.draw.rect(self.surface, (50, 50, 50), popup_rect)
        pygame.draw.rect(self.surface, (200, 200, 200), popup_rect, 2)

        y = 20
        title = FONT.render(f"TaskForce: {self.taskforce.name}", True, WHITE)
        surface.blit(title, (20, y))
        y += 40
        ships_label = SMALL_FONT.render(f"Ships: {len(self.taskforce.ships)}", True, WHITE)
        surface.blit(ships_label, (20, y))
        y += 40

        # Table headers
        headers = ["Name", "Type", "Attack", "Defence", "Move", "Air Ops"]
        col_widths = [140, 80, 60, 60, 60, 120]
        x_positions = [40]
        for w in col_widths[:-1]:
            x_positions.append(x_positions[-1] + w)
        header_y = y
        for i, header in enumerate(headers):
            txt = SMALL_FONT.render(header, True, WHITE)
            surface.blit(txt, (x_positions[i], header_y))
        y += 30
        pygame.draw.line(surface, BLACK, (40, y), (40 + sum(col_widths), y), 2)
        y += 5

        self.carrier_buttons.clear()
        ship:Ship
        for ship in self.taskforce.ships:
            # Get ship properties, fallback to "N/A" if not present
            name = ship.name
            ship_type = ship.type
            attack = ship.attack_factor
            defense = ship.anti_air_factor  # Changed from defense_factor to anti_air_factor
            move = ship.move_factor
            air_ops = ""
            is_carrier = isinstance(ship, Carrier)
            
            row = [name, ship_type, str(attack), str(defense), str(move), air_ops]
            for i, value in enumerate(row):
                txt = SMALL_FONT.render(value, True, WHITE)
                surface.blit(txt, (x_positions[i], y))
            # Draw base symbol as clickable if carrier has base
            if is_carrier and ship.base:
                # Use a font that supports Unicode for the carrier symbol
                unicode_font = pygame.font.SysFont("Segoe UI Emoji", 24)  # Common font for emoji support
                symbol = unicode_font.render(CARRIER_SYMBOL, True, WHITE)
                rect = symbol.get_rect(topleft=(x_positions[5], y))
                surface.blit(symbol, rect.topleft)
                self.carrier_buttons.append((rect, ship.base))
            y += 32

       

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            for rect, base in self.carrier_buttons:
                if rect.collidepoint(pos):
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
    carrierLexington.base.air_operations_config = AirOperationsConfiguration(
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
