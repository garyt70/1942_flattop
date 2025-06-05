import pygame
import sys
import math

from flattop.hex_board_game_model import HexBoardModel, Hex, Piece  # Adjust import as needed

# Hexagon settings
HEX_SIZE = 40  # Radius of hex
HEX_HEIGHT = math.sqrt(3) * HEX_SIZE
HEX_WIDTH = 2 * HEX_SIZE
HEX_SPACING = 5  # Space between hexes

# Colors
BG_COLOR = (30, 30, 30)
HEX_COLOR = (200, 200, 200)
HEX_BORDER = (100, 100, 100)

class DesktopUI:
    def __init__(self, board):
        self.board = board
        self.screen = None
        self.origin = (HEX_WIDTH // 2 + HEX_SPACING, HEX_HEIGHT // 2 + HEX_SPACING)

    def initialize(self):
        pygame.init()
        cols, rows = self.board.width, self.board.height

        # Calculate window size
        win_width = int(HEX_WIDTH * (cols + 0.5) + 2 * HEX_SPACING)
        win_height = int(HEX_HEIGHT * (rows + 0.5) + 2 * HEX_SPACING)
        self.screen = pygame.display.set_mode((win_width, win_height))
        pygame.display.set_caption("Hex Board")

    def draw_hex(self, center, color, border_color):
        points = []
        for i in range(6):
            angle = math.pi / 3 * i
            x = center[0] + HEX_SIZE * math.cos(angle)
            y = center[1] + HEX_SIZE * math.sin(angle)
            points.append((x, y))
        pygame.draw.polygon(self.screen, color, points)
        pygame.draw.polygon(self.screen, border_color, points, 2)

    def hex_to_pixel(self, q, r):
        x = HEX_SIZE * (3/2 * q) + self.origin[0]
        y = HEX_SIZE * math.sqrt(3) * (r + 0.5 * (q % 2)) + self.origin[1]
        return (int(x), int(y))

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            self.screen.fill(BG_COLOR)

            # Draw hexes
            for q in range(self.board.width):
                for r in range(self.board.height):
                    center = self.hex_to_pixel(q, r)
                    self.draw_hex(center, HEX_COLOR, HEX_BORDER)

            pygame.display.flip()

        pygame.quit()
        sys.exit()

"""

def hex_to_pixel(q, r, origin):
    x = HEX_SIZE * (3/2 * q) + origin[0]
    y = HEX_SIZE * math.sqrt(3) * (r + 0.5 * (q % 2)) + origin[1]
    return (int(x), int(y))

def draw_hex(surface, center, color, border_color):
    points = []
    for i in range(6):
        angle = math.pi / 3 * i
        x = center[0] + HEX_SIZE * math.cos(angle)
        y = center[1] + HEX_SIZE * math.sin(angle)
        points.append((x, y))
    pygame.draw.polygon(surface, color, points)
    pygame.draw.polygon(surface, border_color, points, 2)

def main():
    pygame.init()
    board = HexBoard(10,10)
    cols, rows = board.width, board.height  # Adjust if your model uses different names

    # Calculate window size
    win_width = int(HEX_WIDTH * (cols + 0.5) + 2 * HEX_SPACING)
    win_height = int(HEX_HEIGHT * (rows + 0.5) + 2 * HEX_SPACING)
    screen = pygame.display.set_mode((win_width, win_height))
    pygame.display.set_caption("Hex Board")

    origin = (HEX_WIDTH // 2 + HEX_SPACING, HEX_HEIGHT // 2 + HEX_SPACING)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill(BG_COLOR)

        # Draw hexes
        for q in range(cols):
            for r in range(rows):
                center = hex_to_pixel(q, r, origin)
                draw_hex(screen, center, HEX_COLOR, HEX_BORDER)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

"""