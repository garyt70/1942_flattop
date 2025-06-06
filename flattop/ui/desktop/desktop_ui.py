import pygame
import sys
import math

from flattop.hex_board_game_model import HexBoardModel, Hex, Piece  # Adjust import as needed

# Hexagon settings
HEX_SIZE = 20  # Radius of hex
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

        # Determine the maximum screen size
        info = pygame.display.Info()
        max_width, max_height = info.current_w, info.current_h

        # Calculate required window size for the board
        req_width = int(HEX_WIDTH * (cols + 0.5) + 2 * HEX_SPACING)
        req_height = int(HEX_HEIGHT * (rows + 0.5) + 2 * HEX_SPACING)

        # Estimate window caption (title bar) height
        CAPTION_HEIGHT = 40  # Approximate, may vary by OS/theme

        # Set window size to fit within the screen if needed, accounting for caption
        win_width = min(req_width, max_width)
        win_height = min(req_height, max_height - CAPTION_HEIGHT)

        # If the board is larger than the window, enable panning 
        self.can_pan = req_width > win_width or req_height > win_height

        # Set the display mode with the calculated size
        self.screen = pygame.display.set_mode((win_width, win_height))
        


        pygame.display.set_caption("Flattop 1942 - Hexagonal Board Game")
        
        

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

    
    def get_piece_at_pixel(self, pos):
        # Convert pixel to hex coordinates
        x, y = pos
        x -= self.origin[0]
        y -= self.origin[1]
        q = int(round((2/3 * x) / HEX_SIZE))
        r = int(round((y / (math.sqrt(3) * HEX_SIZE)) - 0.5 * (q % 2)))
        for piece in self.board.pieces:
            if isinstance(piece, Piece) and piece.position.q == q and piece.position.r == r:
                return piece
        return None
    
    def render_screen(self):
        self.screen.fill(BG_COLOR)

        # Draw the hexes on the board
        for q in range(self.board.width):
            for r in range(self.board.height):
                center = self.hex_to_pixel(q, r)
                self.draw_hex(center, HEX_COLOR, HEX_BORDER)

        # Draw the pieces on the board
        for piece in self.board.pieces:
            if isinstance(piece, Piece):
                center = self.hex_to_pixel(piece.position.q, piece.position.r)
                pygame.draw.circle(self.screen, (255, 0, 0), center, HEX_SIZE // 3)

        pygame.display.flip()

    def run_with_click_return(self):
        running = True
        dragging = False
        last_mouse_pos = None

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Start dragging for panning
                    dragging = True
                    last_mouse_pos = event.pos
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    # Stop dragging
                    dragging = False
                    last_mouse_pos = None
                elif event.type == pygame.MOUSEMOTION and dragging:
                    # Calculate mouse movement and update origin for panning
                    mouse_x, mouse_y = event.pos
                    last_x, last_y = last_mouse_pos
                    dx = mouse_x - last_x
                    dy = mouse_y - last_y
                    self.origin = (self.origin[0] + dx, self.origin[1] + dy)
                    last_mouse_pos = event.pos

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                    # Optional: right-click to print piece info
                    piece = self.get_piece_at_pixel(event.pos)
                    if piece:
                        print(f"Piece at hex ({piece.position.q}, {piece.position.r}): {piece}")
                    else:
                        print("No piece at clicked hex.")

            self.screen.fill(BG_COLOR)

            self.render_screen()

            pygame.display.flip()

        pygame.quit()
        sys.exit()

    def run(self):
        """
        Start the UI event loop.
        """
        self.run_with_click_return()