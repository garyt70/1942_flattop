import sys
import os
import pygame

# Ensure the parent directory is in sys.path for module discovery
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..','..')))

from flattop.operations_chart_models import AirOperationsTracker, AirOperationsConfiguration

class AirOperationsTrackerDisplay:
    def __init__(self, tracker: AirOperationsTracker, surface, pos=(10, 10)):
        self.tracker = tracker
        self.surface = surface
        self.pos = pos
        self.font = pygame.font.SysFont(None, 24)

    def draw(self):
        x, y = self.pos
        title = self.font.render("Air Operations Tracker", True, (255, 255, 255))
        self.surface.blit(title, (x, y))
        y += 30
        operations = getattr(self.tracker, 'operations', [])
        if operations:
            keys = list(operations[0].keys())
            # Draw headers
            for col, key in enumerate(keys):
                header = self.font.render(str(key), True, (200, 200, 0))
                self.surface.blit(header, (x + col * 120, y))
            y += 25
            # Draw rows
            for op in operations:
                for col, key in enumerate(keys):
                    cell = self.font.render(str(op[key]), True, (255, 255, 255))
                    self.surface.blit(cell, (x + col * 120, y))
                y += 25

class AirOperationsConfigurationDisplay:
    def __init__(self, config: AirOperationsConfiguration, surface, pos=(10, 200)):
        self.config = config
        self.surface = surface
        self.pos = pos
        self.font = pygame.font.SysFont(None, 24)

    def draw(self):
        x, y = self.pos
        title = self.font.render("Air Operations Configuration", True, (255, 255, 255))
        self.surface.blit(title, (x, y))
        y += 30
        for attr in dir(self.config):
            if not attr.startswith("_") and not callable(getattr(self.config, attr)):
                label = self.font.render(f"{attr}: {getattr(self.config, attr)}", True, (255, 255, 255))
                self.surface.blit(label, (x, y))
                y += 25

class BaseUIDisplay:
    def __init__(self, tracker: AirOperationsTracker, config: AirOperationsConfiguration, surface):
        self.tracker_display = AirOperationsTrackerDisplay(tracker, surface)
        self.config_display = AirOperationsConfigurationDisplay(config, surface)

    def draw(self):
        self.tracker_display.draw()
        self.config_display.draw()

# Example usage:
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Flattop Air Operations")
    clock = pygame.time.Clock()

    # Replace with actual tracker and config objects
    tracker = AirOperationsTracker("Test", "Test Description")
    config = AirOperationsConfiguration("Test Config", "Test description")

    ui = BaseUIDisplay(tracker, config, screen)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((0, 0, 40))
        ui.draw()
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()