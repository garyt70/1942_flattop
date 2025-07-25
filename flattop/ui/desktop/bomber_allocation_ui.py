import pygame
import sys

from flattop.operations_chart_models import Aircraft, Ship

class BomberAllocationUI:
    """
    UI for allocating bombers to ships in a task force.
    Ships are rows, bombers are columns. User can increment/decrement allocation at intersections.
    """
    def __init__(self, screen, ships: list[Ship], bombers: list[Aircraft]):
        """
        ships: list of Ship objects
        bombers: list of Aircraft objects (each with .type and .count)
        """
        self.screen = screen
        self.ships = ships
        self.bombers = bombers
        # allocation[ship_idx][bomber_idx] = number of bombers assigned to this ship
        self.allocation = [
            [0 for _ in range(len(bombers))]
            for _ in range(len(ships))
        ]
        self.font = pygame.font.SysFont(None, 24)
        self.header_font = pygame.font.SysFont(None, 28, bold=True)
        self.margin = 16
        self.cell_size = 60
        self.button_size = 24
        self.running = True

    def draw(self):
        self.screen.fill((30, 30, 30))
        margin = self.margin
        cell = self.cell_size
        btn = self.button_size

        # Draw bomber headers (columns)
        for j, bomber in enumerate(self.bombers):
            label = f"{bomber.type.value} ({bomber.count})"
            surf = self.header_font.render(label, True, (200, 200, 255))
            x = margin + (j + 1) * cell
            y = margin
            self.screen.blit(surf, (x, y))

        # Draw ship names (rows)
        for i, ship in enumerate(self.ships):
            label = f"{ship.name} ({ship.status})"
            surf = self.header_font.render(label, True, (255, 255, 200))
            x = margin
            y = margin + (i + 1) * cell
            self.screen.blit(surf, (x, y))

        # Draw allocation grid
        for i, ship in enumerate(self.ships):
            for j, bomber in enumerate(self.bombers):
                x = margin + (j + 1) * cell
                y = margin + (i + 1) * cell
                # Draw allocation number
                alloc = self.allocation[i][j]
                alloc_surf = self.font.render(str(alloc), True, (255, 255, 255))
                self.screen.blit(alloc_surf, (x + cell // 2 - 8, y + cell // 2 - 8))
                # Draw + button
                plus_rect = pygame.Rect(x + cell - btn, y, btn, btn)
                pygame.draw.rect(self.screen, (0, 200, 0), plus_rect)
                plus_surf = self.font.render("+", True, (255, 255, 255))
                self.screen.blit(plus_surf, (plus_rect.x + 6, plus_rect.y + 2))
                # Draw - button
                minus_rect = pygame.Rect(x + cell - btn, y + btn + 2, btn, btn)
                pygame.draw.rect(self.screen, (200, 0, 0), minus_rect)
                minus_surf = self.font.render("-", True, (255, 255, 255))
                self.screen.blit(minus_surf, (minus_rect.x + 8, minus_rect.y + 2))
                # Store rects for click detection
                if not hasattr(self, "button_rects"):
                    self.button_rects = {}
                self.button_rects[(i, j, "plus")] = plus_rect
                self.button_rects[(i, j, "minus")] = minus_rect

        # Draw "Done" button
        done_rect = pygame.Rect(self.screen.get_width() - 120, self.screen.get_height() - 60, 100, 40)
        pygame.draw.rect(self.screen, (0, 120, 255), done_rect)
        done_surf = self.header_font.render("Done", True, (255, 255, 255))
        self.screen.blit(done_surf, (done_rect.x + 10, done_rect.y + 5))
        self.done_rect = done_rect

        pygame.display.flip()

    def handle_events(self):
        while self.running:
            self.draw()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    # Check grid buttons
                    for (i, j, btn_type), rect in self.button_rects.items():
                        if rect.collidepoint(mx, my):
                            if btn_type == "plus":
                                # Only allow allocation if bombers remain
                                if self.get_total_allocated(j) < self.bombers[j].count:
                                    self.allocation[i][j] += 1
                            elif btn_type == "minus":
                                if self.allocation[i][j] > 0:
                                    self.allocation[i][j] -= 1
                    # Check Done button
                    if self.done_rect.collidepoint(mx, my):
                        self.running = False
                        return self.get_allocation_result()

    def get_total_allocated(self, bomber_idx):
        # Total bombers of this type allocated across all ships
        return sum(self.allocation[i][bomber_idx] for i in range(len(self.ships)))

    def get_allocation_result(self):
        """
        Returns a dict: {ship: {bomber_type: count}}
        """
        result = {}
        for i, ship in enumerate(self.ships):
            result[ship] = {}
            for j, bomber in enumerate(self.bombers):
                if self.allocation[i][j] > 0:
                    result[ship][bomber.type] = self.allocation[i][j]
        return result

# Example usage:
# screen = pygame.display.set_mode((800, 600))
# ships = [Ship("Shokaku", ...), Ship("Zuikaku", ...)]
# bombers = [Aircraft(type="Val", count=6), Aircraft(type="Kate", count=4)]
# ui = BomberAllocationUI(screen, ships, bombers)
# allocation = ui.handle_events()
# print(allocation)