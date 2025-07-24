import pygame
import sys
import math

from flattop.hex_board_game_model import HexBoardModel, Hex, Piece  # Adjust import as needed
from flattop.operations_chart_models import Ship, Aircraft, Carrier, AirFormation, Base, TaskForce, AircraftOperationsStatus  # Adjust import as needed
from flattop.ui.desktop.base_ui import BaseUIDisplay, AircraftDisplay
from flattop.ui.desktop.airformation_ui import AirFormationUI
from flattop.ui.desktop.taskforce_ui import TaskForceScreen
from flattop.ui.desktop.piece_image_factory import PieceImageFactory
from flattop.aircombat_engine import resolve_air_to_air_combat, classify_aircraft, resolve_base_anti_aircraft_combat, resolve_taskforce_anti_aircraft_combat, resolve_air_to_ship_combat, resolve_air_to_base_combat

import flattop.ui.desktop.desktop_config as config
from flattop.weather_model import WeatherManager, CloudMarker, WindDirection


# Import color and size constants from config
HEX_SIZE = config.HEX_SIZE
HEX_HEIGHT = config.HEX_HEIGHT
HEX_WIDTH = config.HEX_WIDTH
HEX_SPACING = config.HEX_SPACING
BG_COLOR = config.BG_COLOR
HEX_COLOR = config.HEX_COLOR
HEX_BORDER = config.HEX_BORDER
COLOR_JAPANESE_PIECE = config.COLOR_JAPANESE_PIECE
COLOR_ALLIED_PIECE = config.COLOR_ALLIED_PIECE

# You may need to define or import PieceImageFactory if not already present
# from flattop.ui.desktop.piece_image_factory import PieceImageFactory

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

    def __init__(self, board=HexBoardModel(10, 10), turn_manager=None, weather_manager=None):
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

        if weather_manager is None:
            self.weather_manager = WeatherManager(self.board) 
        else:
            self.weather_manager = weather_manager

        self.board.pieces.extend(self.weather_manager.get_weather_pieces())

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
       
        hex_piece_map = {}
        for piece in self.board.pieces:
            pos = (piece.position.q, piece.position.r)
            if pos not in hex_piece_map:
                hex_piece_map[pos] = []
            hex_piece_map[pos].append(piece)

        #draw the weather pieces
        for (q, r), pieces in hex_piece_map.items():
            center = self.hex_to_pixel(q, r)
            for piece in pieces:
                if isinstance(piece, CloudMarker):
                    if piece.is_storm:
                        image = PieceImageFactory.storm_image()
                    else:
                        image = PieceImageFactory.cloud_image()
                    rect = image.get_rect(center=center)
                    self.screen.blit(image, rect)   
                elif isinstance(piece.game_model, WindDirection):
                    image = PieceImageFactory.wind_direction_image(piece.game_model.direction, piece.game_model.sector)
                    rect = image.get_rect(center=center)
                    self.screen.blit(image, rect)

        #draw the game pieces
        # Iterate through hex_piece_map to draw pieces
        for (q, r), pieces in hex_piece_map.items():
            center = self.hex_to_pixel(q, r)
            #skip weather and wind direction pieces
            isOnlyWeather = True
            for wpiece in pieces:
                if not (isinstance(wpiece, (CloudMarker)) or isinstance(wpiece.game_model, WindDirection)):
                    isOnlyWeather = False

            if isOnlyWeather:
                continue

            if len(pieces) == 1:
                piece = pieces[0]
                color = COLOR_JAPANESE_PIECE if piece.side == "Japanese" else COLOR_ALLIED_PIECE
                if isinstance(piece.game_model, Ship):
                    image = PieceImageFactory.ship_image(color)
                elif isinstance(piece.game_model, Aircraft):
                    image = PieceImageFactory.aircraft_image(color)
                elif isinstance(piece.game_model, Carrier):
                    image = PieceImageFactory.carrier_image(color)
                elif isinstance(piece.game_model, AirFormation):
                    image = PieceImageFactory.airformation_image(color)
                elif isinstance(piece.game_model, Base):
                    image = PieceImageFactory.base_image(color)
                elif isinstance(piece.game_model, TaskForce):
                    image = PieceImageFactory.taskforce_image(color)
                
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
        # Draws the current day, hour, phase, and initiative in the bottom right corner
        font = pygame.font.SysFont(None, 28)
        day = self.turn_manager.current_day
        hour = self.turn_manager.current_hour
        phase = self.turn_manager.current_phase if hasattr(self.turn_manager, "current_phase") else ""
        initiative = getattr(self.turn_manager, "side_with_initiative", None)
        initiative_text = f"Initiative: {initiative}" if initiative else ""
        text = f"Day: {day}  Hour: {hour:02d}:00"
        phase_text = f"Phase: {phase}"

        text_surf = font.render(text, True, (255, 255, 255))
        phase_surf = font.render(phase_text, True, (255, 255, 0))
        initiative_surf = font.render(initiative_text, True, (0, 255, 255)) if initiative_text else None

        text_rect = text_surf.get_rect()
        phase_rect = phase_surf.get_rect()
        initiative_rect = initiative_surf.get_rect() if initiative_surf else None

        win_width, win_height = self.screen.get_size()
        margin = 24
        spacing = 6

        # Stack initiative above phase, phase above time
        if initiative_surf:
            initiative_rect.bottomright = (win_width - margin, win_height - margin - text_rect.height - spacing - phase_rect.height - spacing)
            phase_rect.bottomright = (win_width - margin, win_height - margin - text_rect.height - spacing)
        else:
            phase_rect.bottomright = (win_width - margin, win_height - margin - text_rect.height - spacing)
        text_rect.bottomright = (win_width - margin, win_height - margin)

        # Draw semi-transparent backgrounds for readability
        bg_rects = []
        if initiative_surf:
            bg_rect_initiative = pygame.Rect(
            initiative_rect.left - 8, initiative_rect.top - 4,
            initiative_rect.width + 16, initiative_rect.height + 8
            )
            bg_rects.append(bg_rect_initiative)
        bg_rect_phase = pygame.Rect(
            phase_rect.left - 8, phase_rect.top - 4,
            phase_rect.width + 16, phase_rect.height + 8
        )
        bg_rect_time = pygame.Rect(
            text_rect.left - 8, text_rect.top - 4,
            text_rect.width + 16, text_rect.height + 8
        )
        bg_rects.extend([bg_rect_phase, bg_rect_time])

        for bg_rect in bg_rects:
            pygame.draw.rect(self.screen, (30, 30, 30, 180), bg_rect)

        if initiative_surf:
            self.screen.blit(initiative_surf, initiative_rect)
        self.screen.blit(phase_surf, phase_rect)
        self.screen.blit(text_surf, text_rect)

        # Save for click detection (use the union of all rects)
        rects = [text_rect, phase_rect]
        if initiative_rect:
            rects.append(initiative_rect)
        self._turn_info_rect = rects[0].unionall(rects[1:])

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
            baseUI.handle_events()
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
            
            airformation_ui = AirFormationUI(piece.game_model, self.screen)
            airformation_ui.draw()
            airformation_ui.handle_events()
           
            return
            
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
        #print(f"Cube distance from {start_hex} to {dest_hex}: {distance}")
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
            self.show_turn_change_popup()
            return

        original_button = event.button

        pieces = self.get_pieces_at_pixel(event.pos)
        if len(pieces) > 0:
            isOnlyWeather = (len(pieces) == sum(1 for wpiece in pieces
                                                if (isinstance(wpiece, (CloudMarker)) or isinstance(wpiece.game_model, WindDirection))))
            if isOnlyWeather:
                # If only weather pieces are present, ignore the click
                return
        
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
        elif original_button == 3 and piece:
            #piece = self.get_piece_at_pixel(event.pos)
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

            # Prevent AirFormation from moving into a storm hex
            if isinstance(moving_piece.game_model, AirFormation):
                dest_hex_obj = self.board.get_hex(dest_hex.q, dest_hex.r)
                # Check if any piece in the destination hex is a storm CloudMarker
                if self.weather_manager.is_storm_hex(dest_hex_obj):
                    return

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
        menu_options = []

        # If the piece is an AirFormation and it is in the same hex as a Base then show a menu option to land the AirFormation
        if isinstance(piece.game_model, AirFormation):
            if self.turn_manager.current_phase == "Air Operations":
                base_in_hex = any(
                    isinstance(p.game_model, (Base, TaskForce)) and p.position == piece.position and p.side == piece.side
                    for p in self.board.pieces
                )
                if base_in_hex and not piece.has_moved:
                    menu_options.append("Land")

        # If the piece is a Base, show options to launch or land AirFormations
            # Check for enemy AirFormation in the same hex for combat
            if "Combat" in self.turn_manager.current_phase:
                enemy_airformations = [
                    p for p in self.board.pieces
                    if isinstance(p.game_model, AirFormation)
                    and p.position == piece.position
                    and p.side != piece.side
                ]
                enemy_taskforces = [
                    p for p in self.board.pieces
                    if isinstance(p.game_model, TaskForce)
                    and p.position == piece.position
                    and p.side != piece.side
                ]
                enemy_base = [
                    p for p in self.board.pieces
                    if isinstance(p.game_model, Base)
                    and p.position == piece.position
                    and p.side != piece.side
                ]
                if enemy_airformations or enemy_taskforces or enemy_base:
                    menu_options.append("Combat")

        if piece.can_move and not piece.has_moved and "Movement" in self.turn_manager.current_phase:
            menu_options.append("Move")

        menu_options.extend(["Details", "Cancel"])


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

        match selected:
            case "Land":   
                #landing an AirFormation sets the aircraft to the Base's air operations chart
                # and removes the AirFormation piece from the board
                # the aircraft are added to the Base's air operations chart will have a Just Landed status
                if isinstance(piece.game_model, AirFormation):
                    # Find the Base in the same hex as the AirFormation
                    base_piece:Piece = next(
                        (p for p in self.board.pieces if isinstance(p.game_model, (Base, TaskForce)) and p.position == piece.position),
                        None
                    )
                    base:Base = None
                    if base_piece:
                        if isinstance(base_piece.game_model, Base):
                            base = base_piece.game_model
                            # Ensure the Base has an air operations tracker
                        if isinstance(base_piece.game_model, TaskForce):
                            tf:TaskForce = base_piece.game_model
                            #loop through the ships to ensure there is a carrier. If there is a carrier, then set the base to the carrier's air operations chart
                            for ship in tf.ships:  
                                if isinstance(ship, Carrier):
                                    base = ship.base
                                    break 
                        
                    if base:
                        # Add aircraft to the Base's air operations chart
                        for aircraft in piece.game_model.aircraft:
                            base.air_operations_tracker.set_operations_status(aircraft, AircraftOperationsStatus.JUST_LANDED)
                        # Remove the AirFormation piece from the board
                        self.board.pieces.remove(piece)
                        self._moving_piece = None
                        self._moving_piece_offset = None
                
            case "Combat":
                # Find all AirFormations in the hex
                hex_airformations = [
                    p for p in self.board.pieces
                    if isinstance(p.game_model, AirFormation)
                    and p.position == piece.position
                ]
                # Group by side
                sides = set(p.side for p in hex_airformations)
                
                allied_aircraft = [p.game_model for p in hex_airformations if p.side == "Allied"]
                japanese_aircraft = [p.game_model for p in hex_airformations if p.side == "Japanese"]

                # Gather aircraft by role (interceptor, escort, bomber)
                allied_interceptors, allied_escorts, allied_bombers = classify_aircraft(allied_aircraft)
                japanese_interceptors, japanese_escorts, japanese_bombers = classify_aircraft(japanese_aircraft)

                pre_combat_count_allied_interceptors = sum(ic.count for ic in allied_interceptors)
                pre_combat_count_allied_bombers = sum(b.count for b in allied_bombers)
                pre_combat_count_allied_escorts = sum(ec.count for ec in allied_escorts)

                pre_combat_count_japanese_interceptors = sum(ic.count for ic in japanese_interceptors)
                pre_combat_count_japanese_bombers = sum(b.count for b in japanese_bombers)
                pre_combat_count_japanese_escorts = sum(ec.count for ec in japanese_escorts)

                ### Air 2 Air Combat ###
                result_allied_a2a = None
                result_japanese_a2a = None

                in_clouds = self.weather_manager.is_cloud_hex(piece.position)
                at_night = self.turn_manager.is_night()
                if len(sides) == 2:
                   
                    # For simplicity, assume two sides: Allied and Japanese
                    #and there are two airformations

                    # if no bombers on either side then convert interceptors to escorts 
                    if not allied_bombers and not japanese_bombers:
                        # Convert interceptors to escorts for one side so that we have interceptor to interceptor combat
                        japanese_escorts.extend(japanese_interceptors)
                        japanese_interceptors = []
                    
                    result_allied_a2a = resolve_air_to_air_combat(
                        interceptors=allied_interceptors,
                        escorts=japanese_escorts,
                        bombers=japanese_bombers,
                        rf_expended=True,
                        clouds=in_clouds,
                        night=at_night
                    )

                    if not allied_bombers and not japanese_bombers:
                        # Convert interceptors to escorts for one side so that we have interceptor to interceptor combat
                        allied_escorts.extend(allied_interceptors)
                        allied_interceptors = []
                    
                    result_japanese_a2a = resolve_air_to_air_combat(
                        interceptors=japanese_interceptors,
                        escorts=allied_escorts,
                        bombers=allied_bombers,
                        rf_expended=True,
                        clouds=in_clouds,
                        night=at_night
                    )

                    # need to update the air operations chart for each side
                    # remove aircraft from air formations that have 0 or less count
                    # removed airformations that have no aircraft left
                    for af in allied_aircraft:
                        af.aircraft = [ac for ac in af.aircraft if ac.count > 0]
                        if not af.aircraft:
                            #self.board.pieces.remove(Piece(name=af.name, side="Allied", position=af.position, gameModel=af))
                            self.board.pieces.remove([p for p in hex_airformations if p.game_model == af][0])
                    for af in japanese_aircraft:
                        af.aircraft = [ac for ac in af.aircraft if ac.count > 0]
                        if not af.aircraft:
                            #self.board.pieces.remove(Piece(name=af.name, side="Japanese", position=af.position, gameModel=af))
                            self.board.pieces.remove([p for p in hex_airformations if p.game_model == af][0])
                    
                
                ### execute anti aircraft combat ###
                # the taskforce being attacked by the air formations need to be selected.
                # find the allied taskforces in the hex with the japanese airformation and enable user to select one
                # find the japanese taskforces in the hex with the allied airformation and enable user to select one
                # display a popup with the taskforces and allow user to select one

                def perform_taskforce_anti_aircraft_combat(bombers:list[Aircraft], task_force_pieces:list[Piece], pos:tuple[int, int]):
                    combat_outcome = None
                    if (task_force_pieces and bombers):
                        if len(task_force_pieces) == 1:
                            # If there is only one taskforce on each side, then just use those
                            tf_p = task_force_pieces[0]
                        else:
                            # Show a popup to select the taskforces
                            tf_p:Piece = self.render_piece_selection_popup(task_force_pieces, pos)
                        
                        if tf_p:
                            # Now we have the taskforces, we can resolve anti aircraft combat
                            tf_selected:TaskForce = tf_p.game_model
                                    
                        if tf_selected:
                            combat_outcome = resolve_taskforce_anti_aircraft_combat( bombers, tf_selected)
                        
                    return combat_outcome

                def perform_base_anti_aircraft_combat(bombers:list[Aircraft], base:Base):
                    combat_outcome = None
                    if (base and bombers):
                         combat_outcome = resolve_base_anti_aircraft_combat( bombers, base)
                        
                    return combat_outcome


                ### Anti-Aircraft combat ### 
                    
                allied_taskforce_pieces = [p for p in self.board.pieces if isinstance(p.game_model, TaskForce) and p.side == "Allied" and p.position == piece.position]
                result_allied_anti_aircraft = perform_taskforce_anti_aircraft_combat(japanese_bombers, allied_taskforce_pieces, pos)
                japanese_taskforce_pieces = [p for p in self.board.pieces if isinstance(p.game_model, TaskForce) and p.side == "Japanese" and p.position == piece.position]
                result_japanese_anti_aircraft = perform_taskforce_anti_aircraft_combat(allied_bombers, japanese_taskforce_pieces, pos)
                
                allied_base_pieces = [p for p in self.board.pieces if isinstance(p.game_model, Base) and p.side == "Allied" and p.position == piece.position]
                japanese_base_pieces = [p for p in self.board.pieces if isinstance(p.game_model, Base) and p.side == "Japanese" and p.position == piece.position]
                #assume there is only ever one base.  Also re-using the anti-aircraft results as assuming TF and Base won't be in same hex.
                if allied_base_pieces:
                    result_allied_anti_aircraft = perform_base_anti_aircraft_combat(japanese_bombers,allied_base_pieces[0].game_model)
                #assume there is only ever one base
                if japanese_base_pieces:
                    result_japanese_anti_aircraft = perform_base_anti_aircraft_combat(allied_bombers,japanese_base_pieces[0].game_model)

                #### execute the air combat attack against selected ship ####

                def perform_air_to_ship_combat(bombers:list[Aircraft], taskforce:TaskForce):
                    # this involves choosing which ship is attacked by which aircraft
                     #TODO implement logic to select ship to attack by which aircraft
                     #TODO implement logic to select attack type (e.g. level, torpedo, dive bomber, etc.)

                     #TODO: simple combat for now, change this later
                    ship_selected:Ship = None
                    try:
                        #this is where selection needs to take place
                        ship_selected = taskforce[0].game_model.ships[0]
                        attack_type_selected = "level"  # default attack type, can be changed later
                    except:
                        pass
                    
                    result = None
                    if ship_selected:
                        result = resolve_air_to_ship_combat(bombers,ship_selected, attack_type=attack_type_selected, clouds=in_clouds, night=at_night)
                        if ship_selected.status == "Sunk":
                            taskforce[0].game_model.ships.remove(ship_selected)
                    return result
                
                #allied attach ship
                result_allied_ship_air_attack = perform_air_to_ship_combat(allied_aircraft,japanese_taskforce_pieces)
                result_japanese_ship_air_attack = perform_air_to_ship_combat(japanese_bombers, allied_taskforce_pieces)

                result_allied_base_air_attack = None
                if japanese_base_pieces:
                    result_allied_base_air_attack = resolve_air_to_base_combat(allied_bombers, japanese_base_pieces[0].game_model, clouds=in_clouds, night=at_night)

                result_japanese_base_air_attack = None
                if allied_base_pieces:
                    result_japanese_base_air_attack = resolve_air_to_base_combat(japanese_bombers, allied_base_pieces[0].game_model, clouds=in_clouds, night=at_night)

                # Optionally, show a popup with results

                ## air-to-air summary
                font = pygame.font.SysFont(None, 24)
                
                lines = ["Combat Results:"]
                
                lines.append(f"Allied Interceptors: {pre_combat_count_allied_interceptors}")
                lines.append(f"Allied Escorts: {pre_combat_count_allied_escorts}")
                lines.append(f"Allied Bombers: {pre_combat_count_allied_bombers}")
            
                lines.append(f"Japanese Interceptors: {pre_combat_count_japanese_interceptors}")
                lines.append(f"Japanese Escorts: {pre_combat_count_japanese_escorts}")
                lines.append(f"Japanese Bombers: {pre_combat_count_japanese_bombers}")
                lines.append("-----------------------")

                if result_allied_a2a:
                    
                    lines.append("Allied Air 2 Air Combat Results:")
                    lines.append(f" {result_allied_a2a['interceptor_hits_on_bombers']}")
                    lines.append(f" {result_allied_a2a['interceptor_hits_on_escorts']}")
                    lines.append(f" {result_allied_a2a['escort_hits_on_interceptors']}")
                    lines.append(f" {result_allied_a2a['bomber_hits_on_interceptors']}")
                if result_japanese_a2a:
                    lines.append("Japanese Air 2 Air Combat Results:")
                    lines.append(f" {result_japanese_a2a['interceptor_hits_on_bombers']}")
                    lines.append(f" {result_japanese_a2a['interceptor_hits_on_escorts']}")
                    lines.append(f" {result_japanese_a2a['escort_hits_on_interceptors']}")
                    lines.append(f" {result_japanese_a2a['bomber_hits_on_interceptors']}")
                
                
                lines.append(f"\n")

                ## anti-aircraft summary ##
                if result_allied_anti_aircraft:
                    # Show the combat results for Allied anti aircraft combat
                    lines.append(f"Allied Anti Aircraft Combat Results:")
                    lines.append(f" {result_allied_anti_aircraft['anti_aircraft'].summary}")
                    

                if result_japanese_anti_aircraft:   
                    # Show the combat results for Japanese anti aircraft combat
                    lines.append(f"Japanese Anti Aircraft Combat Results:")
                    lines.append(f" {result_japanese_anti_aircraft['anti_aircraft'].summary}")
                
                
                ## air combat against ship
                if result_allied_ship_air_attack:
                    lines.append("Allied Air Attack Results")
                    lines.append(result_allied_ship_air_attack["bomber_hits"].summary)

                if result_japanese_ship_air_attack:
                    lines.append("Japanese Air Attacke Results")
                    lines.append(result_japanese_ship_air_attack["bomber_hits"].summary)

                if result_allied_base_air_attack:
                    lines.append("Allied Air Attack Results")
                    lines.append(result_allied_base_air_attack["bomber_hits"].summary)

                if result_japanese_base_air_attack:
                    lines.append("Japanese Air Attacke Results")
                    lines.append(result_japanese_base_air_attack["bomber_hits"].summary)


                popup_text = "\n".join(lines)
                self.show_combat_results(popup_text, pos)
                
                return
                

            case "Details":
                self.render_popup(piece, pos)
            case "Move":
                self._dragging = False
                center = self.hex_to_pixel(piece.position.q, piece.position.r)
                if piece.can_move:
                    self.show_max_move_distance(piece)
                    self._moving_piece = piece
                    self._moving_piece_offset = (mouse_x - center[0], mouse_y - center[1])
            case _:      
                # If the selected option is not recognized, reset moving state and assume cancel
                self._moving_piece = None
                self._moving_piece_offset = None
                # Cancel just returns, nothing to do
                return

    def show_combat_results(self, text, pos):
        # Display a popup with the combat results
        win_width, win_height = self.screen.get_size()
        margin = 10
        font = pygame.font.SysFont(None, 24)
        lines = text.split('\n')
        text_surfaces = [font.render(line, True, (255, 255, 255)) for line in lines]
        popup_width = max(ts.get_width() for ts in text_surfaces) + 2 * margin
        popup_height = sum(ts.get_height() for ts in text_surfaces) + (len(text_surfaces) + 1) * margin // 2
        popup_rect = pygame.Rect(
            pos[0] - popup_width // 2,
            pos[1] - popup_height // 2,
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

        # Wait for user to click or press a key to close popup
        waiting = True
        while waiting:
            for popup_event in pygame.event.get():
                if popup_event.type == pygame.MOUSEBUTTONDOWN or popup_event.type == pygame.KEYDOWN or popup_event.type == pygame.QUIT:
                    waiting = False
                    if popup_event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()


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

    def _get_pieces_for_turn_change(self):
        """
        Move phase = get all pieces that can move but have not moved yet.
        Combat phase = get all pieces that can attack but have not attacked yet.
        Air Operations phase = get all bases that have available Launch or Ready Factor count.

        """
        all_pieces:list[Piece] = self.board.pieces
        action_available_pieces = []
        if self.turn_manager.current_phase == "Plane Movement":
            action_available_pieces = [p for p in all_pieces if p.can_move and not p.has_moved and isinstance(p.game_model, AirFormation)]
        elif self.turn_manager.current_phase == "Task Force Movement":
            action_available_pieces = [p for p in all_pieces if p.can_move and not p.has_moved and isinstance(p.game_model, TaskForce)]
        elif self.turn_manager.current_phase == "Combat":
            action_available_pieces = [p for p in all_pieces if p.can_attack]
        elif self.turn_manager.current_phase == "Air Operations":
            bases = []  
            for piece in all_pieces:
                base = None
                if isinstance(piece.game_model, Base):
                    base = piece.game_model
                elif isinstance(piece.game_model, TaskForce):
                    carriers: list[Carrier] = piece.game_model.get_carriers()
                    if len(carriers) > 0:
                        # If the TaskForce has carriers, use the first carrier's air operations chart
                        base = carriers[0].base

                # Check if the base has any aircraft that can launch or are ready
                if base:
                    air_op_config = base.air_operations_config
                    if base.used_launch_factor < air_op_config.launch_factor_max or \
                        base.used_ready_factor < air_op_config.ready_factors:
                        air_op_tracker = base.air_operations_tracker

                        # Check if the base has any aircraft that can launch or are ready
                        # If the base has an air operations tracker, check if it has any aircraft that can launch or are ready
                        if len(air_op_tracker.ready) + len(air_op_tracker.readying) + len(air_op_tracker.just_landed) > 0:
                            action_available_pieces.append(piece)
            
        return action_available_pieces

    def show_turn_change_popup(self):
        # Display a scrollable popup listing all pieces that can move but have not moved yet,
        # and allow the user to advance the phase or turn only if all phases are complete.
        win_width, win_height = self.screen.get_size()
        margin = 16
        font = pygame.font.SysFont(None, 24)
        header_font = pygame.font.SysFont(None, 28, bold=True)

        # Get current phase and phase list from TurnManager
        current_phase = self.turn_manager.current_phase
        phase_list = self.turn_manager.PHASES
        phase_idx = phase_list.index(current_phase) if current_phase in phase_list else 0

        # Filter pieces that can move and have not moved (for this phase, if applicable)
        unmoved = self._get_pieces_for_turn_change()
        lines = [
            f"{i+1}: {getattr(piece, 'name', str(piece))} | {piece.game_model.__class__.__name__} | {getattr(piece, 'side', '')}"
            for i, piece in enumerate(unmoved)
        ]
        if not lines:
            lines = ["No pieces can act this phase."]

        text_surfaces = [font.render(line, True, (255, 255, 255)) for line in lines]
        header_surf = header_font.render(f"Phase: {current_phase}", True, (255, 255, 0))
        # Button text depends on whether this is the last phase
        if phase_idx == len(phase_list) - 1:
            next_phase_text = "Advance Turn"
        else:
            next_phase_text = f"Advance Phase ({phase_list[phase_idx+1]})"
        next_phase_surf = header_font.render(next_phase_text, True, (0, 255, 0))

        popup_width = max([header_surf.get_width(), next_phase_surf.get_width()] + [ts.get_width() for ts in text_surfaces]) + 2 * margin
        visible_lines = min(10, len(text_surfaces))
        line_height = font.get_height() + 4
        popup_height = header_surf.get_height() + next_phase_surf.get_height() + visible_lines * line_height + 5 * margin
        popup_rect = pygame.Rect(
            win_width // 2 - popup_width // 2,
            win_height // 2 - popup_height // 2,
            popup_width,
            popup_height
        )
        scroll_offset = 0

        while True:
            # Draw popup background and border
            self.render_screen()  # Redraw board behind popup
            pygame.draw.rect(self.screen, (50, 50, 50), popup_rect)
            pygame.draw.rect(self.screen, (200, 200, 200), popup_rect, 2)
            # Draw header
            y = popup_rect.top + margin
            self.screen.blit(header_surf, (popup_rect.left + margin, y))
            y += header_surf.get_height() + margin // 2

            # Draw Advance Phase/Turn button (disabled if unmoved pieces remain)
            next_phase_rect = next_phase_surf.get_rect(topleft=(popup_rect.left + margin, y))
            if unmoved:
                pygame.draw.rect(self.screen, (80, 80, 80), next_phase_rect.inflate(12, 8))  # Disabled look
                self.screen.blit(next_phase_surf, next_phase_rect.topleft)
            else:
                pygame.draw.rect(self.screen, (30, 80, 30), next_phase_rect.inflate(12, 8))
                self.screen.blit(next_phase_surf, next_phase_rect.topleft)
            y += next_phase_rect.height + margin // 2

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
                    # Check if click is on Advance Phase/Turn button (only if no unmoved pieces)
                    if next_phase_rect.collidepoint(mx, my):
                       
                        # Advance to next phase
                        self.turn_manager.next_phase()
                        #TODO  - handle processing of a new phase
                        # 
                        
                        match self.turn_manager.current_phase_index:
                            case 0:
                                print("Starting a new turn")
                                self.weather_manager.wind_phase(self.turn_manager)
                                self.weather_manager.cloud_phase(self.turn_manager)
                                self.board.reset_pieces_for_new_turn()
                            
                                print("Air Operations Phase")
                            case 1:
                                print("Shadowing Phase")
                            case 2:
                                print("Task Force Movement Phase")
                            case 3:
                                print("Plane Movement Phase")
                            case 4:
                                print("Combat Phase")
                            case 5:
                                print("Repair Phase")
                    
                        return
                    # Check if click is on a piece line
                    for i in range(scroll_offset, min(scroll_offset + visible_lines, len(text_surfaces))):
                        ts = text_surfaces[i]
                        text_rect = ts.get_rect(topleft=(popup_rect.left + margin, popup_rect.top + margin + header_surf.get_height() + margin // 2 + next_phase_rect.height + margin // 2 + (i - scroll_offset) * line_height))
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