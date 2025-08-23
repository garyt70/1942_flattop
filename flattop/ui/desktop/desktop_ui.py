from asyncio import Task
from turtle import pos
import pygame
import sys
import math

from flattop.game_engine import perform_land_piece_action, perform_observation_phase, perform_turn_start_actions
from flattop.hex_board_game_model import HexBoardModel, Hex, Piece, TurnManager, get_distance  # Adjust import as needed
from flattop.operations_chart_models import Ship, Aircraft, Carrier, AirFormation, Base, TaskForce, AircraftOperationsStatus  # Adjust import as needed
from flattop.ui.desktop.base_ui import BaseUIDisplay, AircraftDisplay
from flattop.ui.desktop.airformation_ui import AirFormationUI
from flattop.ui.desktop.bomber_allocation_ui import BomberAllocationUI
from flattop.ui.desktop.combat_results_ui import CombatResultsScreen
from flattop.ui.desktop.desktop_popup import draw_game_model_popup, draw_piece_selection_popup, draw_turn_info_popup
from flattop.ui.desktop.taskforce_ui import TaskForceScreen
from flattop.ui.desktop.piece_image_factory import PieceImageFactory
from flattop.aircombat_engine import resolve_air_to_air_combat, classify_aircraft, resolve_base_anti_aircraft_combat, resolve_taskforce_anti_aircraft_combat, resolve_air_to_ship_combat, resolve_air_to_base_combat

from flattop.computer_oponent_engine import ComputerOpponent

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

def perform_air_combat_ui(screen, piece:Piece,pieces:list[Piece], board:HexBoardModel, weather_manager:WeatherManager, turn_manager:TurnManager):
    """
    Handles the air combat UI logic for a given piece.
    This function will display the air combat UI and handle user interactions.
    """

    attacking_side = piece.side

    defending_taskforce_pieces = [p for p in board.pieces if isinstance(p.game_model, TaskForce) and p.side != attacking_side and p.position == piece.position]

    #perform UI selection of taskforces and plane allocation
    defending_taskforce_p:Piece = None
    if len(defending_taskforce_pieces) > 1:
        # Show a popup to select the taskforces
        defending_taskforce_p:Piece = draw_piece_selection_popup(screen, defending_taskforce_pieces, pos)
    elif len(defending_taskforce_pieces) == 1:
        # If there is only one taskforce on each side, then just use those
        defending_taskforce_p = defending_taskforce_pieces[0]

    # Check if the piece is in a hex with other air formations
    hex_airformations = [
        p for p in pieces
        if isinstance(p.game_model, AirFormation)
        and p.position == piece.position
    ]
    # Group by side
    sides = set(p.side for p in hex_airformations)

    attacking_aircraft_pieces = [p.game_model for p in hex_airformations if p.side == attacking_side]
    defending_aircraft_pieces = [p.game_model for p in hex_airformations if p.side != attacking_side]

    # Gather aircraft by role (interceptor, escort, bomber)
    attacking_interceptors, attacking_escorts, attacking_bombers = classify_aircraft(attacking_aircraft_pieces)
    defending_interceptors, defending_escorts, defending_bombers = classify_aircraft(defending_aircraft_pieces)

    pre_combat_count_attacking_interceptors = sum(ic.count for ic in attacking_interceptors)
    pre_combat_count_attacking_bombers = sum(b.count for b in attacking_bombers)
    pre_combat_count_attacking_escorts = sum(ec.count for ec in attacking_escorts)

    pre_combat_count_defending_interceptors = sum(ic.count for ic in defending_interceptors)
    pre_combat_count_defending_bombers = sum(b.count for b in defending_bombers)
    pre_combat_count_defending_escorts = sum(ec.count for ec in defending_escorts)

    ### Air 2 Air Combat ###
    result_attacking_a2a = None

    in_clouds = weather_manager.is_cloud_hex(piece.position)
    at_night = turn_manager.is_night()
    if len(sides) == 2:
        
        # For simplicity, assume two sides: attacking and defending
        #and there are two airformations

        # if no bombers on either side then convert interceptors to escorts 
        if not attacking_bombers and not defending_bombers:
            # Convert interceptors to escorts for one side so that we have interceptor to interceptor combat
            defending_escorts.extend(defending_interceptors)
            defending_interceptors = []
        
        result_attacking_a2a = resolve_air_to_air_combat(
            interceptors=attacking_interceptors,
            escorts=defending_escorts,
            bombers=defending_bombers,
            rf_expended=True,
            clouds=in_clouds,
            night=at_night
        )

        # need to update the air operations chart for each side
        # remove aircraft from air formations that have 0 or less count
        # removed airformations that have no aircraft left
        for af in attacking_aircraft_pieces:
            af.aircraft = [ac for ac in af.aircraft if ac.count > 0]
            if not af.aircraft:
                board.pieces.remove([p for p in hex_airformations if p.game_model == af][0])
        for af in defending_aircraft_pieces:
            af.aircraft = [ac for ac in af.aircraft if ac.count > 0]
            if not af.aircraft:
                board.pieces.remove([p for p in hex_airformations if p.game_model == af][0])

    ### execute anti aircraft combat ###
    # the taskforce being attacked by the air formations need to be selected.
    # find the attacking taskforces in the hex with the defending airformation and enable user to select one
    # find the defending taskforces in the hex with the attacking airformation and enable user to select one
    # display a popup with the taskforces and allow user to select one

    def perform_taskforce_anti_aircraft_combat(bombers:list[Aircraft], taskforce:TaskForce, pos:tuple[int, int]):
        combat_outcome = None
        if (taskforce and bombers):
            combat_outcome = resolve_taskforce_anti_aircraft_combat( bombers, taskforce, {"clouds": in_clouds, "night": at_night})

        return combat_outcome

    def perform_base_anti_aircraft_combat(bombers:list[Aircraft], base:Base):
        combat_outcome = None
        if (base and bombers):
                combat_outcome = resolve_base_anti_aircraft_combat( bombers, base, {"clouds": in_clouds, "night": at_night})

        return combat_outcome


    ### Anti-Aircraft combat ###
    result_tf_anti_aircraft = None
    if defending_taskforce_p:
        result_tf_anti_aircraft = perform_taskforce_anti_aircraft_combat(attacking_bombers, defending_taskforce_p.game_model, piece.position)

    defending_base_pieces = [p for p in board.pieces if isinstance(p.game_model, Base) and p.side != attacking_side and p.position == piece.position]
     #assume there is only ever one base
    result_base_anti_aircraft = None
    if defending_base_pieces:
        result_base_anti_aircraft = perform_base_anti_aircraft_combat(attacking_bombers,defending_base_pieces[0].game_model)

    #### execute the air combat attack against selected ship ####

    def perform_air_to_ship_combat(bombers:list[Aircraft], taskforce:TaskForce):
        # this involves choosing which ship is attacked by which aircraft
        # and then resolve the combat for each ship

        if not bombers or not taskforce:
            return None

        if len(bombers) == 0:
            return None


        ui = BomberAllocationUI(screen, taskforce.ships, bombers)
        allocation = ui.handle_events()
        print(allocation)

        if not allocation:
            # If no allocation was made, return None
            return None
        
        # Resolve combat for each ship in the taskforce
        # and return the results
        results = []
        for ship, allocated_bombers in allocation.items():
            if allocated_bombers:
                result = resolve_air_to_ship_combat(allocated_bombers, ship, clouds=in_clouds, night=at_night)
                results.append(result)
                if ship.status == "Sunk":
                    taskforce.ships.remove(ship)
        return results

    
    
    #attacking attack ship
    # airplanes attacking ships need to select a taskforce
    result_attacking_ship_air_attack = None
    if defending_taskforce_p:
        result_attacking_ship_air_attack = perform_air_to_ship_combat(attacking_bombers,defending_taskforce_p.game_model)

    result_attacking_base_air_attack = None
    if defending_base_pieces:
        result_attacking_base_air_attack = resolve_air_to_base_combat(attacking_bombers, defending_base_pieces[0].game_model, clouds=in_clouds, night=at_night)

    # First, remove aircraft with count 0 from all air formations in the hex
    for af_piece in hex_airformations:
        af = af_piece.game_model
        af.aircraft = [ac for ac in af.aircraft if ac.count > 0]

    # Then, remove air formation pieces from the board if they have no aircraft left
    for af_piece in hex_airformations:
        af = af_piece.game_model
        if not af.aircraft and af_piece in board.pieces:
            board.pieces.remove(af_piece)

    combat_results = {
        "result_attacker_a2a": result_attacking_a2a,
        "result_tf_anti_aircraft": result_tf_anti_aircraft,
        "result_base_anti_aircraft": result_base_anti_aircraft,
        "result_attacker_ship_air_attack": result_attacking_ship_air_attack,
        "result_attacker_base_air_attack": result_attacking_base_air_attack,
        "pre_combat_count_attacker_interceptors": pre_combat_count_attacking_interceptors,
        "pre_combat_count_attacker_bombers": pre_combat_count_attacking_bombers,
        "pre_combat_count_attacker_escorts": pre_combat_count_attacking_escorts,
        "pre_combat_count_defender_interceptors": pre_combat_count_defending_interceptors,
        "pre_combat_count_defender_bombers": pre_combat_count_defending_bombers,
        "pre_combat_count_defender_escorts": pre_combat_count_defending_escorts
    }

    return combat_results

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

        self.computer_opponent = ComputerOpponent("Japanese", self.board, self.weather_manager, self.turn_manager)  # Example initialization, can be set to "Allied" or "Japanese"
        # Perform initial turn start actions
        perform_observation_phase(self.board, self.weather_manager, self.turn_manager)

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
    
    def draw(self):
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
                piece:Piece = pieces[0]
                color = COLOR_JAPANESE_PIECE if piece.side == "Japanese" else COLOR_ALLIED_PIECE
                if isinstance(piece.game_model, AirFormation):
                    image = PieceImageFactory.airformation_image(color, observed=piece.observed_condition > 0)
                elif isinstance(piece.game_model, Base):
                    image = PieceImageFactory.base_image(color)
                elif isinstance(piece.game_model, TaskForce):
                    image = PieceImageFactory.taskforce_image(color, observed=piece.observed_condition > 0)
                
                rect = image.get_rect(center=center)
                self.screen.blit(image, rect)
            else:
                # Render stack image for multiple pieces
                #identify if any pieces have been observed
                image = PieceImageFactory.stack_image(pieces, observed=any(p.observed_condition > 0 for p in pieces))
                rect = image.get_rect(center=center)
                self.screen.blit(image, rect)

        # Draw the turn info in the bottom right corner
        self._draw_turn_info()

        # If a piece is being moved, draw it at the mouse position
        if self._moving_piece:
            self.show_max_move_distance(self._moving_piece)
        pygame.display.flip()
    
    def _draw_turn_info(self):
        draw_turn_info_popup(self)

    def render_popup(self, piece:Piece, pos):
        draw_game_model_popup(self, piece, pos)

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
    
    

    def show_max_move_distance(self, piece:Piece):
        # Highlight all hexes within the piece's movement range
        max_move = piece.movement_factor - piece.phase_move_count
        if max_move <= 0:
            return
        
        start_hex = piece.position

        for q in range(self.board.width):
            for r in range(self.board.height):
                dest_hex = Hex(q, r)
                distance = get_distance(start_hex, dest_hex)
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
        self.computer_opponent.perform_turn()
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
            self.draw()
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
            distance = get_distance(start_hex, dest_hex)
            max_move = moving_piece.movement_factor - moving_piece.phase_move_count

            # Prevent AirFormation from moving into a storm hex
            if isinstance(moving_piece.game_model, AirFormation):
                dest_hex_obj = self.board.get_hex(dest_hex.q, dest_hex.r)
                # Check if any piece in the destination hex is a storm CloudMarker
                if self.weather_manager.is_storm_hex(dest_hex_obj):
                    return

            if distance <= max_move:
                self.board.move_piece(moving_piece, dest_hex)
                #perform observation for just this piece
                if moving_piece.can_observe:
                    self._perform_observation(moving_piece)

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
        # airformation and plane move phase then enable move option
        if piece.can_move and not piece.has_moved:
            if isinstance(piece.game_model, AirFormation) and self.turn_manager.current_phase in ["Plane Movement"]:
                menu_options.append("Move")
                #also allow landing if in the same hex as a Base
                base_in_hex = any(
                    isinstance(p.game_model, (Base, TaskForce)) and p.position == piece.position and p.side == piece.side
                    for p in self.board.pieces
                )
                if base_in_hex and not piece.has_moved:
                    menu_options.append("Land")
            elif isinstance(piece.game_model, TaskForce) and self.turn_manager.current_phase in ["Task Force Movement"]:
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
                # Perform landing action for the AirFormation
                if isinstance(piece.game_model, AirFormation):
                    # Perform the landing action
                    perform_land_piece_action(piece, self.board, piece.position)
                    self._moving_piece = None
                    self._moving_piece_offset = None

            case "Combat":
                # Perform combat action for the AirFormation
                # This will involve selecting taskforces and performing air combat
                results = perform_air_combat_ui(self.screen, piece, self.board.pieces, self.board, self.weather_manager, self.turn_manager)
                # Optionally, show a popup with results

                ## air-to-air summary
                
                self.show_combat_results(results, pos)
                
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

    def show_combat_results(self, results, pos):

        """
        Combat results array

        Air to Air combat result return
        result = {
        "interceptor_hits_on_escorts": AirCombatResult(),
        "escort_hits_on_interceptors": AirCombatResult(),
        "interceptor_hits_on_bombers": AirCombatResult(),
        "bomber_hits_on_interceptors": AirCombatResult(),
        "eliminated": {"interceptors": [], "escorts": [], "bombers": []}
    }

    Anti aircradt results
    result = {"anti_aircraft": AirCombatResult(),
            "eliminated": {"interceptors": [], "escorts": [], "bombers": []}
            }

    Base combat results
    results = {"bomber_hits": AirCombatResult(),
           "eliminated": {"aircraft": []}
            }
    
    Ship combat results
    result = {"bomber_hits": AirCombatResult(),
            "eliminated": {"ships": []}
            }

        """

        if results==None:
            return
        
        """
            "result_attacker_a2a": result_computer_a2a,
            "result_tf_anti_aircraft": result_tf_anti_aircraft,
            "result_base_anti_aircraft": result_base_anti_aircraft,
            "result_attacker_ship_air_attack": result_computer_ship_air_attack,
            "result_attacker_base_air_attack": result_computer_base_air_attack,
            "pre_combat_count_attacker_interceptors": pre_combat_count_computer_interceptors,
            "pre_combat_count_attacker_bombers": pre_combat_count_computer_bombers,
            "pre_combat_count_attacker_escorts": pre_combat_count_computer_escorts,
            "pre_combat_count_defender_interceptors": pre_combat_count_enemy_interceptors,
            "pre_combat_count_defender_bombers": pre_combat_count_enemy_bombers,
            "pre_combat_count_defender_escorts": pre_combat_count_enemy_escorts
        """

        a2a = results.get("result_attacker_a2a")
        aa = []
        aa.append(results.get("result_tf_anti_aircraft"))
        aa.append(results.get("result_base_anti_aircraft"))
        ship = results.get("result_attacker_ship_air_attack")
        base = results.get("result_attacker_base_air_attack")


        results = {"air_to_air": a2a, "anti_aircraft": aa, "base": base, "ship": ship}
        ui = CombatResultsScreen(results, self.screen)

        ui.draw_results()
        pygame.display.flip()
        # Wait for user to click or press a key to close
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    waiting = False
    """
    def _make_a2a_summary(self, a2a):
        hits = []
        for k in ["interceptor_hits_on_escorts", "escort_hits_on_interceptors", "interceptor_hits_on_bombers", "bomber_hits_on_interceptors"]:
            v = a2a.get(k)
            if v and hasattr(v, "hits") and v.hits:
                hits.append(f"{k.replace('_', ' ').title()}: {sum(v.hits.values())}")
        elim = a2a.get("eliminated", {})
        lines.append(f"Player Escorts: {results['pre_combat_count_player_escorts']}")
        lines.append(f"Player Bombers: {results['pre_combat_count_player_bombers']}")
    
        lines.append(f"Computer Interceptors: {results['pre_combat_count_enemy_interceptors']}")
        lines.append(f"Computer Escorts: {results['pre_combat_count_enemy_escorts']}")
        lines.append(f"Computer Bombers: {results['pre_combat_count_enemy_bombers']}")
        lines.append("-----------------------")
        result_player_a2a = results.get("result_player_a2a")
        result_computer_a2a = results.get("result_enemy_a2a")
        result_player_anti_aircraft = results.get("result_player_anti_aircraft")
        result_computer_anti_aircraft = results.get("result_enemy_anti_aircraft")
        result_player_ship_air_attack = results.get("result_player_ship_air_attack")
        result_computer_ship_air_attack = results.get("result_enemy_ship_air_attack")
        result_player_base_air_attack = results.get("result_player_base_air_attack")
        result_computer_base_air_attack = results.get("result_enemy_base_air_attack")
        if result_player_a2a:

            lines.append("Player Air 2 Air Combat Results:")
            lines.append(f" {result_player_a2a['interceptor_hits_on_bombers']}")
            lines.append(f" {result_player_a2a['interceptor_hits_on_escorts']}")
            lines.append(f" {result_player_a2a['escort_hits_on_interceptors']}")
            lines.append(f" {result_player_a2a['bomber_hits_on_interceptors']}")
        if result_computer_a2a:
            lines.append("Computer Air 2 Air Combat Results:")
            lines.append(f" {result_computer_a2a['interceptor_hits_on_bombers']}")
            lines.append(f" {result_computer_a2a['interceptor_hits_on_escorts']}")
            lines.append(f" {result_computer_a2a['escort_hits_on_interceptors']}")
            lines.append(f" {result_computer_a2a['bomber_hits_on_interceptors']}")


        lines.append(f"\n")

        ## anti-aircraft summary ##
        if result_player_anti_aircraft:
            # Show the combat results for Player anti aircraft combat
            lines.append(f"Player Anti Aircraft Combat Results:")
            lines.append(f" {result_player_anti_aircraft['anti_aircraft'].summary}")


        if result_computer_anti_aircraft:
            # Show the combat results for Computer anti aircraft combat
            lines.append(f"Computer Anti Aircraft Combat Results:")
            lines.append(f" {result_computer_anti_aircraft['anti_aircraft'].summary}")


        ## air combat against ship
        if result_player_ship_air_attack:
            lines.append("Player Air Attack Results against Ship")
            #loop through the results and add the summary for each ship
            for result in result_player_ship_air_attack:
                if result:
                    lines.append(result["bomber_hits"].summary)

        if result_computer_ship_air_attack:
            lines.append("Computer Air Attack Results against Ship")
            for result in result_computer_ship_air_attack:
                if result:
                    lines.append(result["bomber_hits"].summary)

        if result_player_base_air_attack:
            lines.append("Player Air Attack Results against Base")
            lines.append(result_player_base_air_attack["bomber_hits"].summary)

        if result_computer_base_air_attack:
            lines.append("Computer Air Attack Results against Base")
            lines.append(result_computer_base_air_attack["bomber_hits"].summary)


        text = "\n".join(lines)

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
"""

    def render_piece_selection_popup(self, pieces, pos):
        return draw_piece_selection_popup(self.screen, pieces, pos)

    def _get_pieces_for_turn_change(self):
        """
        Use game_engine to get actionable pieces for the current phase.
        """
        from flattop.game_engine import get_actionable_pieces
        return get_actionable_pieces(self.board, self.turn_manager)

    def _perform_observation(self, piece: Piece):
        """
        Perform observation for a single piece using game_engine logic.
        """
        from flattop.game_engine import perform_observation_for_piece
        perform_observation_for_piece(piece, self.board, self.weather_manager, self.turn_manager)
    
        

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

        needs_redraw = True
        running = True
        while running:
            if needs_redraw:
                self.draw()  # Redraw board behind popup
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
                needs_redraw = False

            event = pygame.event.wait()
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return
                elif event.key == pygame.K_DOWN and scroll_offset + visible_lines < len(text_surfaces):
                    scroll_offset += 1
                    needs_redraw = True
                elif event.key == pygame.K_UP and scroll_offset > 0:
                    scroll_offset -= 1
                    needs_redraw = True
                elif pygame.K_1 <= event.key <= pygame.K_9:
                    idx = event.key - pygame.K_1 + scroll_offset
                    if 0 <= idx < len(unmoved):
                        self.show_piece_menu(unmoved[idx], (popup_rect.left + margin, popup_rect.top + margin))
                        return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                # Check if click is on Advance Phase/Turn button (only if no unmoved pieces)
                if next_phase_rect.collidepoint(mx, my):
                    # Advance to next phase, this will also handle turn change if at last phase
                    self.turn_manager.next_phase()
                    match self.turn_manager.current_phase_index:
                        case 0:
                            print("Starting a new turn")
                            perform_turn_start_actions(board=self.board, turn_manager=self.turn_manager, weather_manager=self.weather_manager)
                            self.computer_opponent.perform_observation()
                            self.computer_opponent.perform_turn()
                            print("Air Operations Phase")
                        case 1:
                            print("Task Force Movement Phase")
                            # no action this phase, just a placeholder. Menus change to Task Force Movement
                            self.computer_opponent.perform_turn()
                        case 2:
                            print("Plane Movement Phase")
                            # no action this phase, just a placeholder. Menus change to Plane Movement
                            self.computer_opponent.perform_turn()
                        case 3:
                            print("Combat Phase")
                            # no action this phase, just a placeholder. Menus change to Combat
                            self.turn_manager.last_combat_result = None
                            self.computer_opponent.perform_turn()
                            self.show_combat_results(self.turn_manager.last_combat_result, event.pos)

                    return
                # Check if click is on a piece line
                for i in range(scroll_offset, min(scroll_offset + visible_lines, len(text_surfaces))):
                    ts = text_surfaces[i]
                    text_rect = ts.get_rect(topleft=(popup_rect.left + margin, popup_rect.top + margin + header_surf.get_height() + margin // 2 + next_phase_rect.height + margin // 2 + (i - scroll_offset) * line_height))
                    if text_rect.collidepoint(mx, my) and len(unmoved) > 1:
                        self.show_piece_menu(unmoved[i], event.pos)
                        return
                # Scroll up/down if click on arrows
                if scroll_offset > 0:
                    up_arrow_rect = pygame.Rect(popup_rect.right - margin - 20, popup_rect.top + margin, 20, 20)
                    if up_arrow_rect.collidepoint(mx, my):
                        scroll_offset -= 1
                        needs_redraw = True
                if scroll_offset + visible_lines < len(text_surfaces):
                    down_arrow_rect = pygame.Rect(popup_rect.right - margin - 20, popup_rect.bottom - margin - 20, 20, 20)
                    if down_arrow_rect.collidepoint(mx, my):
                        scroll_offset += 1
                        needs_redraw = True

    def run(self):
        """
        Start the UI event loop.
        """
        self.run_with_click_return()