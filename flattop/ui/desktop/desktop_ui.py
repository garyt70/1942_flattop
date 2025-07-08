import pygame
import sys
import math

from flattop.hex_board_game_model import HexBoardModel, Hex, Piece  # Adjust import as needed
from flattop.operations_chart_models import AirFormation, Base, TaskForce, AirOperationsChart  # Adjust import as needed
from flattop.ui.desktop.base_ui import BaseUIDisplay
from flattop.ui.desktop.taskforce_ui import TaskForceScreen
from flattop.ui.desktop.base_ui import AircraftDisplay


# Hexagon settings
HEX_SIZE = 20  # Radius of hex
HEX_HEIGHT = math.sqrt(3) * HEX_SIZE
HEX_WIDTH = 2 * HEX_SIZE
HEX_SPACING = 5  # Space between hexes

# Colors
BG_COLOR = (30, 30, 30)
HEX_COLOR = (173, 216, 230)  # Light blue
HEX_BORDER = (100, 100, 100)
COLOR_JAPANESE_PIECE = (255, 0, 0)  # RED
COLOR_ALLIED_PIECE = (0, 128, 255)  # Blue


class PieceImageFactory:
    """
    Generates pygame.Surface images for AirFormation, Base, and TaskForce pieces.
    Each image is a colored shape (circle, triangle, or square) with a simple icon drawn in the center.
    """

    @staticmethod
    def airformation_image(color, size=HEX_SIZE):
        # Circle with a simple "plane" icon (horizontal line and tail)
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        radius = size // 1.5 #3
        pygame.draw.circle(surf, color, center, radius)
        # Draw a simple plane: a line with a tail
        pygame.draw.line(surf, (255, 255, 255), (center[0] - radius//2, center[1]), (center[0] + radius//2, center[1]), 2)
        pygame.draw.line(surf, (255, 255, 255), (center[0], center[1]), (center[0], center[1] + radius//2), 2)
        return surf

    @staticmethod
    def base_image(color, size=HEX_SIZE):
        # Triangle with a simple "building" icon (rectangle and door)
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        tri_size = size #// 2
        points = [
            (center[0], center[1] - tri_size//2),
            (center[0] - tri_size//2, center[1] + tri_size//2),
            (center[0] + tri_size//2, center[1] + tri_size//2)
        ]
        pygame.draw.polygon(surf, color, points)
        # Draw a simple building: rectangle and door
        rect_w, rect_h = tri_size//2, tri_size//3
        rect_x = center[0] - rect_w//2
        rect_y = center[1]
        pygame.draw.rect(surf, (255, 255, 255), (rect_x, rect_y, rect_w, rect_h))
        # Door
        door_w, door_h = rect_w//3, rect_h//2
        door_x = center[0] - door_w//2
        door_y = rect_y + rect_h - door_h
        pygame.draw.rect(surf, (100, 100, 100), (door_x, door_y, door_w, door_h))
        return surf

    @staticmethod
    def taskforce_image(color, size=HEX_SIZE):
        # Draw a fleet of 4 ships (rectangles) in formation, top-down view, on a square playing piece with background color
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        # Draw the square playing piece background
        bg_color = color  # Board background color, adjust as needed
        pygame.draw.rect(surf, bg_color, (0, 0, size, size), border_radius=6)
        pygame.draw.rect(surf, (200, 200, 200), (0, 0, size, size), 2, border_radius=6)

        ship_w = size // 3
        ship_h = size // 8
        spacing = size // 10
        # Arrange ships in two rows of two
        start_x = (size - (2 * ship_w + spacing)) // 2
        start_y = (size - (2 * ship_h + spacing)) // 2
        ship_color = color
        outline_color = (255, 255, 255)
        for row in range(2):
            for col in range(2):
                x = start_x + col * (ship_w + spacing)
                y = start_y + row * (ship_h + spacing)
                rect = pygame.Rect(x, y, ship_w, ship_h)
                pygame.draw.rect(surf, ship_color, rect)
                pygame.draw.rect(surf, outline_color, rect, 2)
                # Draw a small bridge on each ship (a small square at the front)
                bridge_w = ship_w // 5
                bridge_h = ship_h // 2
                bridge_x = x + ship_w // 2 - bridge_w // 2
                bridge_y = y
                pygame.draw.rect(surf, outline_color, (bridge_x, bridge_y, bridge_w, bridge_h))
        return surf

    @staticmethod
    def stack_image(pieces, size=HEX_SIZE):
        """
        Draws a stack indicator for multiple pieces in a hex, as overlapping squares.
        Each square is the same size as the hex, but offset so the stack is visible.
        The top piece is fully visible, and each piece underneath is offset and partially visible.
        pieces: list of Piece objects in the stack (max 4 shown).
        """
        surf = pygame.Surface((size + size // 1.5, size + size // 1.5), pygame.SRCALPHA)
        overlap = size // 4  # Amount each square is offset to show underneath
        max_show = min(len(pieces), 4)

        def piece_color(piece):
            return COLOR_ALLIED_PIECE if getattr(piece, "side", "") == "Allied" else COLOR_JAPANESE_PIECE

        # Draw from bottom to top so the top piece is fully visible
        for i in range(max_show):
            color = piece_color(pieces[i])
            offset = (max_show - 1 - i) * overlap
            rect = pygame.Rect(offset, offset, size, size)
            pygame.draw.rect(surf, color, rect)
            pygame.draw.rect(surf, (200, 200, 200), rect, 2)

        # Draw a number if more than 4
        if len(pieces) > 4:
            font = pygame.font.SysFont(None, 18)
            text = font.render(str(len(pieces)), True, (255, 255, 255))
            text_rect = text.get_rect(center=(surf.get_width() // 1.5, surf.get_height() // 1.5))
            surf.blit(text, text_rect)
        return surf


class DesktopUI:
    """
    DesktopUI provides a graphical user interface for displaying and interacting with a hexagonal board game
    using the pygame library. It handles rendering the board, pieces, and popups, as well as user interactions
    such as dragging pieces, panning the board, and displaying information popups.
    Attributes:
        board: The game board object containing hex grid and pieces.
        screen: The pygame display surface.
        origin: The pixel coordinates of the board's origin (top-left offset).
        can_pan: Boolean indicating if panning is enabled (when board is larger than window).
    Methods:
        __init__(board):
            Initializes the DesktopUI with the given board.
        initialize():
            Initializes pygame, sets up the display window, and determines if panning is needed.
        draw_hex(center, color, border_color):
            Draws a single hexagon at the specified center with given fill and border colors.
        hex_to_pixel(q, r):
            Converts hex grid coordinates (q, r) to pixel coordinates on the screen.
        get_piece_at_pixel(pos):
            Returns the piece located at the given pixel position, or None if no piece is present.
        render_screen():
            Renders the entire board, including hexes and pieces, to the screen.
        render_popup(text, pos):
            Displays a popup window with the given text at the specified position, and waits for user input to close.
        run_with_click_return():
            Main event loop for the UI, handling user input for dragging pieces, panning, and popups.
        run():
            Starts the UI event loop.
    """
    
    def __init__(self, board=HexBoardModel(10, 10), turn_manager=None):
        self.board = board
        self.screen = None
        self.origin = (HEX_WIDTH // 2 + HEX_SPACING, HEX_HEIGHT // 2 + HEX_SPACING)
        self._dragging = False
        self._last_mouse_pos = None
        self._moving_piece = None
        self._moving_piece_offset = (0, 0)
        # Add turn manager reference
        if turn_manager is None:
            from flattop.hex_board_game_model import TurnManager
            self.turn_manager = TurnManager()
        else:
            self.turn_manager = turn_manager

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

        # Set the display mode with RESIZABLE flag
        self.screen = pygame.display.set_mode((win_width, win_height), pygame.RESIZABLE)

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
                hex_obj = self.board.get_hex(q, r)
                # Determine color based on terrain attribute
                if hasattr(hex_obj, "terrain"):
                    terrain = hex_obj.terrain
                    if terrain == "sea":
                        color = (173, 216, 230)  # Light blue
                    elif terrain == "land":
                        color = (34, 139, 34)    # Forest green
                    elif terrain == "mountain":
                        color = (139, 137, 137)  # Gray
                    elif terrain == "base":
                        color = (255, 215, 0)    # Gold
                    else:
                        color = HEX_COLOR        # Default color
                else:
                    color = HEX_COLOR
                center = self.hex_to_pixel(q, r)
                self.draw_hex(center, color, HEX_BORDER)

        # Draw the pieces on the board
        hex_piece_map = {}
        for piece in self.board.pieces:
            pos = (piece.position.q, piece.position.r)
            if pos not in hex_piece_map:
                hex_piece_map[pos] = []
            hex_piece_map[pos].append(piece)

        for (q, r), pieces in hex_piece_map.items():
            center = self.hex_to_pixel(q, r)
            if len(pieces) == 1:
                piece = pieces[0]
                color = COLOR_JAPANESE_PIECE if piece.side == "Japanese" else COLOR_ALLIED_PIECE
                if piece.game_model.__class__.__name__ == "AirFormation":
                    image = PieceImageFactory.airformation_image(color)
                elif piece.game_model.__class__.__name__ == "Base":
                    image = PieceImageFactory.base_image(color)
                elif piece.game_model.__class__.__name__ == "TaskForce":
                    image = PieceImageFactory.taskforce_image(color)
                else:
                    image = PieceImageFactory.airformation_image(color)
                rect = image.get_rect(center=center)
                self.screen.blit(image, rect)
            else:
                # Render stack image for multiple pieces
                image = PieceImageFactory.stack_image(pieces)
                rect = image.get_rect(center=center)
                self.screen.blit(image, rect)

        # Draw the turn info in the bottom right corner
        self._draw_turn_info()

        # If a piece is being moved, draw it at the mouse position
        if self._moving_piece:
            self.show_max_move_distance(self._moving_piece)
        pygame.display.flip()
    
    def _draw_turn_info(self):
        # Draws the current day and hour in the bottom right corner
        font = pygame.font.SysFont(None, 28)
        day = self.turn_manager.current_day
        hour = self.turn_manager.current_hour
        text = f"Day: {day}  Hour: {hour:02d}:00"
        text_surf = font.render(text, True, (255, 255, 255))
        text_rect = text_surf.get_rect()
        win_width, win_height = self.screen.get_size()
        margin = 24
        text_rect.bottomright = (win_width - margin, win_height - margin)
        # Draw a semi-transparent background for readability
        bg_rect = pygame.Rect(
            text_rect.left - 8, text_rect.top - 4,
            text_rect.width + 16, text_rect.height + 8
        )
        pygame.draw.rect(self.screen, (30, 30, 30, 180), bg_rect)
        self.screen.blit(text_surf, text_rect)
        # Save for click detection
        self._turn_info_rect = text_rect.copy()

    def render_popup(self, piece:Piece, pos):
        #TODO: consider using pygame menu for popups and dialogs as well as menu option
        # Calculate maximum popup size (20% of display area, but allow up to 90% of height)
        win_width, win_height = self.screen.get_size()
        margin = 10

        if isinstance(piece.game_model, Base):
            # If the piece is a Base, use the BaseUIDisplay to render it
            # This allows for a more detailed and interactive display of the Base piece
            
            baseUI = BaseUIDisplay( piece.game_model, self.screen)
            baseUI.air_op_chart = self.board.players[piece.side]
            baseUI.turn_manager = self.turn_manager
            baseUI.draw()
            for af in baseUI.created_air_formations:
                self.board.add_piece(Piece(
                    name=f"AF#{af.number}",  #need to fix this or decide if AirFormation number are needed
                    side=piece.game_model.side,
                    position=piece.position,
                    gameModel=af))
            return
        
        
        elif isinstance(piece.game_model, TaskForce):
            # If the piece is a TaskForce, use the TaskForceScreen to render it
            # This allows for a more detailed and interactive display of the TaskForce piece
            try:
                tf_screen = TaskForceScreen(piece.game_model)
                tf_screen.air_ops_chart = self.board.players[piece.side]
                tf_screen.draw(self.screen)
                pygame.display.flip()
                # Wait for user to close the TaskForce screen
                waiting = True
                while waiting:
                    for popup_event in pygame.event.get():
                        tf_screen.handle_event(popup_event)
                        if popup_event.type == pygame.MOUSEBUTTONDOWN or popup_event.type == pygame.KEYDOWN or popup_event.type == pygame.QUIT:
                            waiting = False
                            if popup_event.type == pygame.QUIT:
                                pygame.quit()
                                sys.exit()
                #create a piece for any created air formations
                if tf_screen.base_dialog:
                    for af in tf_screen.base_dialog.created_air_formations:
                        self.board.add_piece(Piece(
                            name=f"AF#{af.number}",  #TODO: need to fix this or decide if AirFormation number are needed
                            side=piece.game_model.side,
                            position=piece.position,
                            gameModel=af))
                        
                return
            except ImportError:
                pass  # Fallback to default popup if import fails
        elif isinstance(piece.game_model, AirFormation):
            # If the piece is an AirFormation, use the AircraftDisplay to render it
            # This allows for a more detailed and interactive display of the AirFormation piece
            try:
                # Draw a popup background for the AirFormation details
                font = pygame.font.SysFont(None, 24)
                header_font = pygame.font.SysFont(None, 28, bold=True)
                popup_width = int(win_width * 0.85)
                popup_height = int(win_height * 0.5)
                popup_rect = pygame.Rect(
                    win_width // 2 - popup_width // 2,
                    win_height // 2 - popup_height // 2,
                    popup_width,
                    popup_height
                )
                pygame.draw.rect(self.screen, (50, 50, 50), popup_rect)
                pygame.draw.rect(self.screen, (200, 200, 200), popup_rect, 2)

                # Draw header
                header = f"Air Formation: {getattr(piece, 'name', str(piece))}"
                header_surf = header_font.render(header, True, (255, 255, 0))
                self.screen.blit(header_surf, (popup_rect.left + margin, popup_rect.top + margin))

                # Draw aircraft list header and list
                y = popup_rect.top + margin + header_surf.get_height() + margin // 2
                y = AircraftDisplay.draw_aircraft_list_header(self.screen, piece.game_model.aircraft, popup_rect.left + margin, y)
                y = AircraftDisplay.draw_aircraft_list(self.screen, piece.game_model.aircraft, popup_rect.left + margin, y + 5)

                pygame.display.flip()

                # Wait for user to close popup
                waiting = True
                while waiting:
                    for popup_event in pygame.event.get():
                        if popup_event.type == pygame.MOUSEBUTTONDOWN or popup_event.type == pygame.KEYDOWN or popup_event.type == pygame.QUIT:
                            waiting = False
                            if popup_event.type == pygame.QUIT:
                                pygame.quit()
                                sys.exit()
                return
            except ImportError:
                pass
        else:
            # Prepare text for popup
            text= f"{piece}"

            # Prepare font
            font = pygame.font.SysFont(None, 24)
            lines = text.split('\n')
            text_surfaces = [font.render(line, True, (255, 255, 255)) for line in lines]

            # Calculate popup size based on the widest line and total height
            popup_width = max(ts.get_width() for ts in text_surfaces) + 2 * margin
            popup_height = sum(ts.get_height() for ts in text_surfaces) + (len(text_surfaces) + 1) * margin // 2

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
            for ts in text_surfaces:
                text_rect = ts.get_rect()
                text_rect.topleft = (popup_rect.left + margin, y)
                self.screen.blit(ts, text_rect)
                y += ts.get_height() + margin // 2

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




    def pixel_to_hex_coord(self, x, y):
        # Convert pixel coordinates to hex grid coordinates and return a Hex object
        x -= self.origin[0]
        y -= self.origin[1]
        q = int(round((2/3 * x) / HEX_SIZE))
        r = int(round((y / (math.sqrt(3) * HEX_SIZE)) - 0.5 * (q % 2)))
        # Ensure q and r are within board bounds
        if 0 <= q < self.board.width and 0 <= r < self.board.height:
            return Hex(q, r)
        return None
    
    def get_distance(self, start_hex, dest_hex):
        # Calculate distance using offset coordinates (odd-q vertical layout)
        # See: https://www.redblobgames.com/grids/hexagons/#distances-offset
        # Convert offset (odd-q) coordinates to cube coordinates for accurate distance calculation
        def offset_to_cube(q, r):
            # Odd-q vertical layout
            x = q
            z = r - (q - (q & 1)) // 2
            y = -x - z
            return (x, y, z)
        start_cube = offset_to_cube(start_hex.q, start_hex.r)
        dest_cube = offset_to_cube(dest_hex.q, dest_hex.r)
        dx = dest_cube[0] - start_cube[0]
        dy = dest_cube[1] - start_cube[1]
        dz = dest_cube[2] - start_cube[2]
        distance = max(abs(dx), abs(dy), abs(dz))
        print(f"Cube distance from {start_hex} to {dest_hex}: {distance}")
        return distance

    def show_max_move_distance(self, piece:Piece):
        # Highlight all hexes within the piece's movement range
        max_move = piece.movement_factor
        start_hex = piece.position

        for q in range(self.board.width):
            for r in range(self.board.height):
                dest_hex = Hex(q, r)
                distance = self.get_distance(start_hex, dest_hex)
                if distance <= max_move:
                    center = self.hex_to_pixel(q, r)
                    # Draw a semi-transparent overlay on the hex
                    overlay = pygame.Surface((HEX_WIDTH, HEX_HEIGHT), pygame.SRCALPHA)
                    points = []
                    for i in range(6):
                        angle = math.pi / 3 * i
                        x = HEX_SIZE + HEX_SIZE * math.cos(angle)
                        y = HEX_SIZE + HEX_SIZE * math.sin(angle)
                        points.append((x, y))
                    pygame.draw.polygon(overlay, (200, 200, 200, 100), points)
                    self.screen.blit(overlay, (center[0] - HEX_SIZE, center[1] - HEX_SIZE))
        pygame.display.flip()

    def run_with_click_return(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self._handle_mouse_button_down(event)

                elif event.type == pygame.MOUSEMOTION:
                    self._handle_mouse_motion(event)
                
                elif event.type == pygame.MOUSEBUTTONUP:
                    #assume dragging is done when mouse button is released
                    self._dragging = False

            #self.screen.fill(BG_COLOR)
            self.render_screen()
            pygame.display.flip()

        pygame.quit()
        sys.exit()

    def _handle_mouse_button_down(self, event):
        # Handles mouse interaction for selecting and dragging pieces on a hex grid.
        # If a piece exists at the mouse event position, it prepares the piece for moving by:
        #   - Storing the piece as '_moving_piece'
        #   - Calculating the offset between the mouse position and the center of the piece (using hex_to_pixel)
        #     so the piece follows the cursor smoothly during dragging.
        # If no piece is present, it starts a generic drag operation (e.g., for panning the board)
        #   - Sets '_dragging' to True and records the last mouse position.

        # If a piece is already being moved, handle the mouse button up event
        if self._moving_piece:
            self._handle_move_piece(event)
            return

        # Check if click is on the turn info display
        if hasattr(self, "_turn_info_rect") and self._turn_info_rect.collidepoint(event.pos):
            self.show_unmoved_pieces_popup()
            return

        original_button = event.button

        pieces = self.get_pieces_at_pixel(event.pos)
        if len(pieces) == 1:
            piece = pieces[0]
        elif len(pieces) > 1:
            piece = self.render_piece_selection_popup(pieces, event.pos)
        else:
            piece = None

        if original_button == 1:
            if piece:
                self.show_piece_menu(piece, event.pos)
            else:
                self._dragging = True
                self._last_mouse_pos = event.pos
        elif original_button == 3:
            piece = self.get_piece_at_pixel(event.pos)
            if piece:
                self.render_popup(piece, event.pos)
       

    def _handle_move_piece(self, event):
        # Handles moving a piece when the mouse button is released.
        # It checks if the piece can be moved within its movement factor and updates the board accordingly.
        # If the move is valid, it moves the piece to the new hex; otherwise, it ignores the move.
        # After moving, it resets the '_moving_piece' to None.
        
        # Save state for run loop
        moving_piece = self._moving_piece
        moving_piece_offset = self._moving_piece_offset
        if not moving_piece:
            # If no piece is being moved, just return
            return
        # If a piece is being moved, check if the move is valid
        mouse_x, mouse_y = event.pos
        dest_hex = self.pixel_to_hex_coord(mouse_x, mouse_y)
        if dest_hex:
            start_hex = moving_piece.position
            distance = self.get_distance(start_hex, dest_hex)
            max_move = moving_piece.movement_factor
            if distance <= max_move:
                self.board.move_piece(moving_piece, dest_hex)
            # else: ignore move (could add feedback)
        self._moving_piece = None
        self._moving_piece_offset = (0, 0)  # Reset the offset after moving
           
    def _handle_mouse_motion(self, event):
        moving_piece = self._moving_piece
        moving_piece_offset = self._moving_piece_offset
        dragging = self._dragging
        last_mouse_pos = self._last_mouse_pos

        if moving_piece:
            # If a piece is being moved, draw it at the mouse position with an offset
            # This allows the piece to follow the cursor smoothly
            mouse_x, mouse_y = event.pos
            pygame.draw.circle(self.screen, (255, 0, 0), (mouse_x - moving_piece_offset[0], mouse_y - moving_piece_offset[1]), HEX_SIZE // 3)
            pygame.display.flip()
        elif dragging:
            mouse_x, mouse_y = event.pos
            last_x, last_y = last_mouse_pos
            dx = mouse_x - last_x
            dy = mouse_y - last_y
            self.origin = (self.origin[0] + dx, self.origin[1] + dy)
            self._last_mouse_pos = event.pos
        # Save state for run loop
        #if not hasattr(self, '_dragging'):
        #    self._dragging = dragging
        #if not hasattr(self, '_last_mouse_pos'):
        #    self._last_mouse_pos = last_mouse_pos

    def get_pieces_at_pixel(self, pos):
        # Return all pieces at the hex under the given pixel
        x, y = pos
        x -= self.origin[0]
        y -= self.origin[1]
        q = int(round((2/3 * x) / HEX_SIZE))
        r = int(round((y / (math.sqrt(3) * HEX_SIZE)) - 0.5 * (q % 2)))
        return [piece for piece in self.board.pieces if piece.position.q == q and piece.position.r == r]

    def show_piece_menu(self, piece:Piece, pos):
        # When a piece is clicked, display a menu with options to Move or Details
        if piece.can_move and not piece.has_moved:
            # If the piece can move and has not moved yet, show the Move option
            menu_options = ["Move", "Details", "Cancel"]
        else:
            # If the piece cannot move or has already moved, show only Details and Cancel 
             menu_options = ["Details", "Cancel"]
        font = pygame.font.SysFont(None, 28)
        margin = 10
        option_height = font.get_height() + margin
        menu_width = max(font.size(opt)[0] for opt in menu_options) + 2 * margin
        menu_height = option_height * len(menu_options) + margin
        mouse_x, mouse_y = pos
        menu_rect = pygame.Rect(mouse_x, mouse_y, menu_width, menu_height)

        # Draw menu
        pygame.draw.rect(self.screen, (60, 60, 60), menu_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), menu_rect, 2)
        for i, opt in enumerate(menu_options):
            opt_surf = font.render(opt, True, (255, 255, 255))
            self.screen.blit(opt_surf, (menu_rect.left + margin, menu_rect.top + margin + i * option_height))
        pygame.display.flip()

        # Wait for user selection
        selected = None
        while selected is None:
            for menu_event in pygame.event.get():
                if menu_event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif menu_event.type == pygame.MOUSEBUTTONDOWN:
                    mx2, my2 = menu_event.pos
                    if menu_rect.collidepoint(mx2, my2):
                        idx = (my2 - menu_rect.top - margin) // option_height
                        if 0 <= idx < len(menu_options):
                            selected = menu_options[idx]
                            break
                elif menu_event.type == pygame.KEYDOWN:
                    if menu_event.key == pygame.K_ESCAPE:
                        selected = "Cancel"
                        break

        if selected == "Details":
            self.render_popup(piece, pos)
        elif selected == "Move":
            self._dragging = False
            center = self.hex_to_pixel(piece.position.q, piece.position.r)
            if piece.can_move:
                self.show_max_move_distance(piece)
                self._moving_piece = piece
                self._moving_piece_offset = (mouse_x - center[0], mouse_y - center[1])
                
            else:
                self._moving_piece = None
                self._moving_piece_offset = None
                # Cancel just returns, nothing to do

    def render_piece_selection_popup(self, pieces, pos):
        # Display a popup with a list of pieces and let the user select one
        win_width, win_height = self.screen.get_size()
        margin = 10
        font = pygame.font.SysFont(None, 24)
        # Show: Piece name, type, and side
        lines = [
            f"{i+1}: {getattr(piece, 'name', str(piece))} | {piece.game_model.__class__.__name__} | {getattr(piece, 'side', '')}"
            for i, piece in enumerate(pieces)
        ]
        text_surfaces = [font.render(line, True, (255, 255, 255)) for line in lines]
        popup_width = max(ts.get_width() for ts in text_surfaces) + 2 * margin
        popup_height = sum(ts.get_height() for ts in text_surfaces) + (len(text_surfaces) + 1) * margin // 2
        popup_rect = pygame.Rect(
            win_width // 2 - popup_width // 2,
            win_height // 2 - popup_height // 2,
            popup_width,
            popup_height
        )
        pygame.draw.rect(self.screen, (50, 50, 50), popup_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), popup_rect, 2)
        y = popup_rect.top + margin
        for ts in text_surfaces:
            text_rect = ts.get_rect()
            text_rect.topleft = (popup_rect.left + margin, y)
            self.screen.blit(ts, text_rect)
            y += ts.get_height() + margin // 2
        pygame.display.flip()

        # Wait for user to click on a line or press a number key
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if pygame.K_1 <= event.key <= pygame.K_9:
                        idx = event.key - pygame.K_1
                        if idx < len(pieces):
                            return pieces[idx]
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    if popup_rect.collidepoint(mx, my):
                        rel_y = my - popup_rect.top - margin
                        line_height = text_surfaces[0].get_height() + margin // 2
                        idx = rel_y // line_height
                        if 0 <= idx < len(pieces):
                            return pieces[idx]
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return None

    def show_unmoved_pieces_popup(self):
        # Display a scrollable popup listing all pieces that can move but have not moved yet,
        # and allow the user to advance the turn.
        win_width, win_height = self.screen.get_size()
        margin = 16
        font = pygame.font.SysFont(None, 24)
        header_font = pygame.font.SysFont(None, 28, bold=True)
        # Filter pieces that can move and have not moved
        unmoved = [p for p in self.board.pieces if getattr(p, "can_move", False) and not getattr(p, "has_moved", False)]
        lines = [
            f"{i+1}: {getattr(piece, 'name', str(piece))} | {piece.game_model.__class__.__name__} | {getattr(piece, 'side', '')}"
            for i, piece in enumerate(unmoved)
        ]
        if not lines:
            lines = ["No pieces can move this turn."]
        text_surfaces = [font.render(line, True, (255, 255, 255)) for line in lines]
        header_surf = header_font.render("Unmoved Pieces", True, (255, 255, 0))
        next_turn_surf = header_font.render("Advance Turn", True, (0, 255, 0))
        popup_width = max([header_surf.get_width(), next_turn_surf.get_width()] + [ts.get_width() for ts in text_surfaces]) + 2 * margin
        visible_lines = min(10, len(text_surfaces))
        line_height = font.get_height() + 4
        popup_height = header_surf.get_height() + next_turn_surf.get_height() + visible_lines * line_height + 5 * margin
        popup_rect = pygame.Rect(
            win_width // 2 - popup_width // 2,
            win_height // 2 - popup_height // 2,
            popup_width,
            popup_height
        )
        scroll_offset = 0

       
        # Draw popup background and border
        self.render_screen()  # Redraw board behind popup
        pygame.draw.rect(self.screen, (50, 50, 50), popup_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), popup_rect, 2)
        # Draw header
        y = popup_rect.top + margin
        self.screen.blit(header_surf, (popup_rect.left + margin, y))
        y += header_surf.get_height() + margin // 2

        # Draw Advance Turn button
        next_turn_rect = next_turn_surf.get_rect(topleft=(popup_rect.left + margin, y))
        pygame.draw.rect(self.screen, (30, 80, 30), next_turn_rect.inflate(12, 8))
        self.screen.blit(next_turn_surf, next_turn_rect.topleft)
        y += next_turn_rect.height + margin // 2

        # Draw visible lines with scrolling
        for i in range(scroll_offset, min(scroll_offset + visible_lines, len(text_surfaces))):
            ts = text_surfaces[i]
            text_rect = ts.get_rect()
            text_rect.topleft = (popup_rect.left + margin, y)
            self.screen.blit(ts, text_rect)
            y += line_height

        # Draw scroll indicators if needed
        if scroll_offset > 0:
            up_arrow = font.render("^", True, (255, 255, 255))
            self.screen.blit(up_arrow, (popup_rect.right - margin - up_arrow.get_width(), popup_rect.top + margin))
        if scroll_offset + visible_lines < len(text_surfaces):
            down_arrow = font.render("v", True, (255, 255, 255))
            self.screen.blit(down_arrow, (popup_rect.right - margin - down_arrow.get_width(), popup_rect.bottom - margin - down_arrow.get_height()))

        pygame.display.flip()

        while True:
            
            # Wait for user interaction
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                    elif event.key == pygame.K_DOWN and scroll_offset + visible_lines < len(text_surfaces):
                        scroll_offset += 1
                    elif event.key == pygame.K_UP and scroll_offset > 0:
                        scroll_offset -= 1
                    elif pygame.K_1 <= event.key <= pygame.K_9:
                        idx = event.key - pygame.K_1 + scroll_offset
                        if 0 <= idx < len(unmoved):
                            self.show_piece_menu(unmoved[idx], (popup_rect.left + margin, popup_rect.top + margin))
                            return
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    # Check if click is on Advance Turn button
                    if next_turn_rect.collidepoint(mx, my):
                        self.turn_manager.next_turn()
                        self.board.reset_pieces_for_new_turn()
                        return
                    # Check if click is on a piece line
                    for i in range(scroll_offset, min(scroll_offset + visible_lines, len(text_surfaces))):
                        ts = text_surfaces[i]
                        text_rect = ts.get_rect(topleft=(popup_rect.left + margin, popup_rect.top + margin + header_surf.get_height() + margin // 2 + next_turn_rect.height + margin // 2 + (i - scroll_offset) * line_height))
                        if text_rect.collidepoint(mx, my):
                            self.show_piece_menu(unmoved[i], event.pos)
                            return
                    # Scroll up/down if click on arrows
                    if scroll_offset > 0:
                        up_arrow_rect = pygame.Rect(popup_rect.right - margin - 20, popup_rect.top + margin, 20, 20)
                        if up_arrow_rect.collidepoint(mx, my):
                            scroll_offset -= 1
                    if scroll_offset + visible_lines < len(text_surfaces):
                        down_arrow_rect = pygame.Rect(popup_rect.right - margin - 20, popup_rect.bottom - margin - 20, 20, 20)
                        if down_arrow_rect.collidepoint(mx, my):
                            scroll_offset += 1

    def run(self):
        """
        Start the UI event loop.
        """
        self.run_with_click_return()