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
                # Draw the hex coordinate as a number for identification at the top of the hex
                """                # Uncomment this section if you want to display hex coordinates.
                                     # the code is very ineefficient, so it is commented out. it causes the sceen to render very slowly.
                font = pygame.font.SysFont(None, 16)
                hex_label = f"{q},{r}"
                text_surface = font.render(hex_label, True, (0, 0, 0))
                text_rect = text_surface.get_rect()
                # Position the text at the top of the hex
                text_rect.midbottom = (center[0], center[1] - HEX_SIZE + 4)
                self.screen.blit(text_surface, text_rect)
                """
                
        # Draw the pieces on the board
        for piece in self.board.pieces:
            if isinstance(piece, Piece):
                center = self.hex_to_pixel(piece.position.q, piece.position.r)
                pygame.draw.circle(self.screen, (255, 0, 0), center, HEX_SIZE // 3)

        pygame.display.flip()
    
    def render_popup(self, text, pos):
        #TODO: consider using pygame menu for popups and dialogs as well as menu option
        # Calculate maximum popup size (20% of display area, but allow up to 90% of height)
        win_width, win_height = self.screen.get_size()
        max_popup_width = int(win_width * 0.2)
        max_popup_height = int(win_height * 0.9)  # Allow up to 90% of display height
        margin = 10

        # Prepare font and wrap text to fit popup
        font = pygame.font.SysFont(None, 24)
        words = text.split()
        lines = []
        line = ""
        for word in words:
            test_line = f"{line} {word}".strip()
            test_surface = font.render(test_line, True, (255, 255, 255))
            if test_surface.get_width() > max_popup_width - 2 * margin and line:
                lines.append(line)
                line = word
            else:
                line = test_line
            
            #if line:
            #    lines.append(line)

        # Calculate popup size based on text
        line_height = font.get_height()
        popup_width = min(
            max([font.render(l, True, (255, 255, 255)).get_width() for l in lines]) + 2 * margin,
            max_popup_width
        )
        popup_height = min(len(lines) * line_height + 2 * margin, max_popup_height)

        # Position popup at top right
        popup_rect = pygame.Rect(
            win_width - popup_width - margin,
            margin,
            popup_width,
            popup_height
        )

        # Draw popup background and border
        pygame.draw.rect(self.screen, (50, 50, 50), popup_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), popup_rect, 2)

        # Render each line of text
        y = popup_rect.top + margin
        for l in lines:
            text_surface = font.render(l, True, (255, 255, 255))
            text_rect = text_surface.get_rect()
            text_rect.topleft = (popup_rect.left + margin, y)
            self.screen.blit(text_surface, text_rect)
            y += line_height

        pygame.display.flip()

        # Wait for user to click or press a key to close popup
        waiting = True
        while waiting:
            for popup_event in pygame.event.get():
                if popup_event.type == pygame.MOUSEBUTTONDOWN or popup_event.type == pygame.KEYDOWN or popup_event.type == pygame.QUIT:
                    waiting = False
                    if popup_event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()

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
                        self.render_popup(f"{piece}", event.pos)
                        

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