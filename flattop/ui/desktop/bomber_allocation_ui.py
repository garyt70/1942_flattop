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
        self.header_font = pygame.font.SysFont(None, 20, bold=True)
        self.margin = 16
        self.cell_size = 60
        self.button_size = 24
        self.running = True

    def draw(self):
        self.screen.fill((30, 30, 30))
        margin = self.margin
        cell_width = 120
        cell_height = 50
        header_height = 60
        btn = self.button_size

        # Calculate grid dimensions
        grid_start_x = margin
        grid_start_y = margin + header_height
        
        # Draw title
        title_surf = self.header_font.render("Bomber Allocation", True, (255, 255, 255))
        self.screen.blit(title_surf, (margin, margin // 2))

        # Draw column headers (aircraft types)
        # First column is for ship names (empty header)
        header_y = margin + 30
        
        # Draw "Ships" header
        ships_header = self.header_font.render("Ships", True, (255, 255, 200))
        self.screen.blit(ships_header, (grid_start_x + 10, header_y))
        
        # Draw aircraft type headers
        for j, bomber in enumerate(self.bombers):
            label = f"{bomber.type.value}"
            available = f"({bomber.count} avail)"
            allocated = f"({self.get_total_allocated(j)} used)"
            
            x = grid_start_x + (j + 1) * cell_width
            
            # Aircraft type name
            surf = self.header_font.render(label, True, (200, 200, 255))
            self.screen.blit(surf, (x + 10, header_y))
            
            # Available count
            avail_surf = self.font.render(available, True, (150, 255, 150))
            self.screen.blit(avail_surf, (x + 60, header_y))

            # Used count
            used_surf = self.font.render(allocated, True, (255, 150, 150))
            self.screen.blit(used_surf, (x + 10, header_y + 20))

        # Draw grid lines and content
        for i in range(len(self.ships) + 1):  # +1 for header row
            y = grid_start_y + i * cell_height
            # Horizontal lines
            pygame.draw.line(self.screen, (100, 100, 100), 
                           (grid_start_x, y), 
                           (grid_start_x + (len(self.bombers) + 1) * cell_width, y))

        for j in range(len(self.bombers) + 2):  # +1 for ship column, +1 for end line
            x = grid_start_x + j * cell_width
            # Vertical lines
            pygame.draw.line(self.screen, (100, 100, 100), 
                           (x, grid_start_y), 
                           (x, grid_start_y + len(self.ships) * cell_height))

        # Draw ship names and allocation data
        for i, ship in enumerate(self.ships):
            y = grid_start_y + i * cell_height
            
            # Ship name in first column
            ship_label = f"{ship.name}"
            status_label = f"({ship.status})"
            ship_surf = self.font.render(ship_label, True, (255, 255, 200))
            status_surf = self.font.render(status_label, True, (200, 200, 150))
            self.screen.blit(ship_surf, (grid_start_x + 10, y + 10))
            self.screen.blit(status_surf, (grid_start_x + 10, y + 25))

            # Allocation cells for each bomber type
            for j, bomber in enumerate(self.bombers):
                x = grid_start_x + (j + 1) * cell_width
                
                # Cell background
                cell_rect = pygame.Rect(x + 2, y + 2, cell_width - 4, cell_height - 4)
                pygame.draw.rect(self.screen, (50, 50, 50), cell_rect)
                
                # Allocation number (centered)
                alloc = self.allocation[i][j]
                alloc_surf = self.font.render(str(alloc), True, (255, 255, 255))
                alloc_rect = alloc_surf.get_rect()
                alloc_rect.center = (x + cell_width // 2, y + cell_height // 2 - 5)
                self.screen.blit(alloc_surf, alloc_rect)
                
                # + button (top right)
                plus_rect = pygame.Rect(x + cell_width - btn - 5, y + 5, btn, btn)
                color = (0, 200, 0) if self.get_total_allocated(j) < bomber.count else (100, 100, 100)
                pygame.draw.rect(self.screen, color, plus_rect)
                plus_surf = self.font.render("+", True, (255, 255, 255))
                plus_text_rect = plus_surf.get_rect()
                plus_text_rect.center = plus_rect.center
                self.screen.blit(plus_surf, plus_text_rect)
                
                # - button (bottom right)
                minus_rect = pygame.Rect(x + cell_width - btn - 5, y + cell_height - btn - 5, btn, btn)
                color = (200, 0, 0) if alloc > 0 else (100, 100, 100)
                pygame.draw.rect(self.screen, color, minus_rect)
                minus_surf = self.font.render("-", True, (255, 255, 255))
                minus_text_rect = minus_surf.get_rect()
                minus_text_rect.center = minus_rect.center
                self.screen.blit(minus_surf, minus_text_rect)
                
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