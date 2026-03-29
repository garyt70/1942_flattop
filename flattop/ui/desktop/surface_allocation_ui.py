import pygame
import sys

from flattop.operations_chart_models import Ship


class SurfaceAllocationUI:
    """Interactive attacker-to-target ship allocation for surface combat."""

    def __init__(self, screen, attacker_ships: list[Ship], defender_ships: list[Ship]):
        self.screen = screen
        self.attacker_ships = [s for s in attacker_ships if s.status != "Sunk" and s.attack_factor > 0]
        self.defender_ships = [s for s in defender_ships if s.status != "Sunk"]
        self.running = True
        self.font = pygame.font.SysFont(None, 24)
        self.header_font = pygame.font.SysFont(None, 28, bold=True)
        self.margin = 18
        self.row_height = 42
        self.target_rects = []
        self.done_rect = pygame.Rect(0, 0, 120, 42)
        self.cancel_rect = pygame.Rect(0, 0, 120, 42)

        self.assignment_by_attacker_idx = {}
        for idx in range(len(self.attacker_ships)):
            self.assignment_by_attacker_idx[idx] = 0 if self.defender_ships else -1

    def _target_name_for_index(self, idx: int) -> str:
        target_idx = self.assignment_by_attacker_idx.get(idx, -1)
        if target_idx < 0 or target_idx >= len(self.defender_ships):
            return "No target"
        target = self.defender_ships[target_idx]
        return f"{target.name} ({target.type})"

    def _cycle_target(self, attacker_idx: int, step: int):
        if not self.defender_ships:
            self.assignment_by_attacker_idx[attacker_idx] = -1
            return
        current = self.assignment_by_attacker_idx.get(attacker_idx, 0)
        self.assignment_by_attacker_idx[attacker_idx] = (current + step) % len(self.defender_ships)

    def draw(self):
        self.screen.fill((28, 28, 32))
        width, height = self.screen.get_size()

        title = self.header_font.render("Surface Combat Allocation", True, (240, 240, 240))
        self.screen.blit(title, (self.margin, self.margin))

        subtitle = self.font.render("Choose a target ship for each attacking ship.", True, (200, 200, 210))
        self.screen.blit(subtitle, (self.margin, self.margin + 28))

        y = self.margin + 70
        self.target_rects = []

        header_color = (180, 180, 220)
        self.screen.blit(self.font.render("Attacker", True, header_color), (self.margin, y))
        self.screen.blit(self.font.render("Target", True, header_color), (width // 2 - 40, y))
        y += 26

        for idx, attacker in enumerate(self.attacker_ships):
            row_top = y + idx * self.row_height
            pygame.draw.rect(self.screen, (40, 40, 50), pygame.Rect(self.margin, row_top, width - 2 * self.margin, self.row_height - 4))

            attacker_text = self.font.render(f"{attacker.name} ({attacker.type})", True, (240, 240, 200))
            self.screen.blit(attacker_text, (self.margin + 8, row_top + 10))

            left_rect = pygame.Rect(width // 2 - 78, row_top + 8, 28, 24)
            pygame.draw.rect(self.screen, (90, 90, 120), left_rect)
            self.screen.blit(self.font.render("<", True, (255, 255, 255)), (left_rect.x + 8, left_rect.y + 2))

            target_rect = pygame.Rect(width // 2 - 44, row_top + 8, 300, 24)
            pygame.draw.rect(self.screen, (62, 62, 74), target_rect)
            target_text = self.font.render(self._target_name_for_index(idx), True, (230, 230, 230))
            self.screen.blit(target_text, (target_rect.x + 6, target_rect.y + 2))

            right_rect = pygame.Rect(width // 2 + 262, row_top + 8, 28, 24)
            pygame.draw.rect(self.screen, (90, 90, 120), right_rect)
            self.screen.blit(self.font.render(">", True, (255, 255, 255)), (right_rect.x + 7, right_rect.y + 2))

            self.target_rects.append((idx, left_rect, right_rect))

        bottom_y = min(height - 60, y + len(self.attacker_ships) * self.row_height + 16)
        self.done_rect = pygame.Rect(width - self.margin - 120, bottom_y, 120, 40)
        self.cancel_rect = pygame.Rect(width - self.margin - 250, bottom_y, 120, 40)

        pygame.draw.rect(self.screen, (40, 120, 70), self.done_rect)
        pygame.draw.rect(self.screen, (110, 55, 55), self.cancel_rect)
        self.screen.blit(self.header_font.render("Done", True, (255, 255, 255)), (self.done_rect.x + 26, self.done_rect.y + 8))
        self.screen.blit(self.header_font.render("Cancel", True, (255, 255, 255)), (self.cancel_rect.x + 16, self.cancel_rect.y + 8))

        pygame.display.flip()

    def handle_events(self):
        while self.running:
            self.draw()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False
                    return None
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if self.done_rect.collidepoint(mx, my):
                        self.running = False
                        return self.get_allocation_result()
                    if self.cancel_rect.collidepoint(mx, my):
                        self.running = False
                        return None

                    for attacker_idx, left_rect, right_rect in self.target_rects:
                        if left_rect.collidepoint(mx, my):
                            self._cycle_target(attacker_idx, -1)
                            break
                        if right_rect.collidepoint(mx, my):
                            self._cycle_target(attacker_idx, 1)
                            break

    def get_allocation_result(self) -> dict[Ship, Ship]:
        allocation: dict[Ship, Ship] = {}
        if not self.defender_ships:
            return allocation
        for idx, attacker in enumerate(self.attacker_ships):
            target_idx = self.assignment_by_attacker_idx.get(idx, -1)
            if target_idx >= 0 and target_idx < len(self.defender_ships):
                allocation[attacker] = self.defender_ships[target_idx]
        return allocation
