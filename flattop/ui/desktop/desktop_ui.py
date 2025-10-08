from asyncio import Task
from turtle import pos
import pygame
import sys
import math

from flattop.game_engine import perform_land_piece_action, perform_observation_for_piece, perform_observation_phase, perform_turn_start_actions
from flattop.hex_board_game_model import HexBoardModel, Hex, Piece, TurnManager, get_distance  # Adjust import as needed
from flattop.operations_chart_models import Ship, Aircraft, Carrier, AirFormation, Base, TaskForce, AircraftOperationsStatus  # Adjust import as needed
from flattop.ui.desktop.base_ui import BaseUIDisplay, AircraftDisplay
from flattop.ui.desktop.airformation_ui import AirFormationUI
from flattop.ui.desktop.bomber_allocation_ui import BomberAllocationUI
from flattop.ui.desktop.combat_results_ui import CombatResultsList, CombatResultsScreen
from flattop.ui.desktop.desktop_popup import Dashboard, draw_dashboard, draw_game_model_popup, draw_piece_selection_popup, draw_turn_info_popup, show_observation_report_popup, show_turn_change_popup
from flattop.ui.desktop.taskforce_ui import TaskForceScreen
from flattop.ui.desktop.piece_image_factory import PieceImageFactory
from flattop.aircombat_engine import resolve_air_to_air_combat, classify_aircraft, resolve_base_anti_aircraft_combat, resolve_taskforce_anti_aircraft_combat, resolve_air_to_ship_combat, resolve_air_to_base_combat

from flattop.computer_oponent_engine import ComputerOpponent

import flattop.ui.desktop.desktop_config as config
from flattop.weather_model import WeatherManager, CloudMarker, WindDirection

FEATURE_FLAG_TESTING = config.FEATURE_FLAG_TESTING


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
        self.dashboard: Dashboard = None
        self.origin = (HEX_WIDTH // 2 + HEX_SPACING, HEX_HEIGHT // 2 + HEX_SPACING)
        self._dragging = False
        self._last_mouse_pos = None
        self._moving_piece = None
        self._moving_piece_offset = (0, 0)
        self.turn_manager = turn_manager
        self.weather_manager = weather_manager  
        if self.turn_manager is None:
            from flattop.hex_board_game_model import TurnManager
            self.turn_manager = TurnManager()
        if self.weather_manager is None:
            self.weather_manager = WeatherManager(self.board) 

        self.minimap_rect = None
        self.minimap_scale = 0.25  # 25% of screen
        self.minimap_dragging = False
        self.minimap_resize_start = None
        self.minimap_min_size = 100
        self.minimap_max_size = 600

    def reposition_taskforces(self):
        """
        Allows the human user to reposition their own TaskForce pieces on the mapboard before the game starts.
        User can click and drag their TaskForce pieces to any valid hex.
        User can also pan the map by clicking and dragging on any hex that does not contain a human TaskForce.
        Press ESC or Enter to finish repositioning.
        """

        running = True
        selected_piece: Piece = None
        offset = (0, 0)
        dragging_map = False
        last_mouse_pos = None

        clock = pygame.time.Clock()
        
        while running:
            clock.tick(30)  # Limit to 30 FPS
            self.draw()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                        running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        pieces = self.get_pieces_at_pixel(event.pos)
                        # Only allow repositioning for human side's TaskForce pieces
                        found_human_taskforce = False
                        for piece in pieces:
                            if isinstance(piece.game_model, TaskForce) and piece.side != self.computer_opponent.side:
                                selected_piece = piece
                                center = self.hex_to_pixel(piece.position.q, piece.position.r)
                                offset = (event.pos[0] - center[0], event.pos[1] - center[1])
                                found_human_taskforce = True
                                break
                        if not found_human_taskforce:
                            # Start dragging map if no human TaskForce is present
                            dragging_map = True
                            last_mouse_pos = event.pos
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1 and selected_piece:
                        dest_hex = self.pixel_to_hex_coord(event.pos[0], event.pos[1])
                        if dest_hex:
                            selected_piece.position = dest_hex
                        selected_piece = None
                    if event.button == 1 and dragging_map:
                        dragging_map = False
                        last_mouse_pos = None
                        self.draw()
                elif event.type == pygame.MOUSEMOTION:
                    if selected_piece:
                        # Optionally, show the piece following the mouse
                        self.draw()
                        mouse_x, mouse_y = event.pos
                        image = PieceImageFactory.taskforce_image(
                            COLOR_JAPANESE_PIECE if selected_piece.side == "Japanese" else COLOR_ALLIED_PIECE,
                            observed=selected_piece.observed_condition > 0
                        )
                        rect = image.get_rect(center=(mouse_x - offset[0], mouse_y - offset[1]))
                        self.screen.blit(image, rect)
                        pygame.display.flip()
                    elif dragging_map and last_mouse_pos:
                        mouse_x, mouse_y = event.pos
                        last_x, last_y = last_mouse_pos
                        dx = mouse_x - last_x
                        dy = mouse_y - last_y
                        self.origin = (self.origin[0] + dx, self.origin[1] + dy)
                        last_mouse_pos = event.pos
                        self.draw_minimap()
                        
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

        self.board.pieces.extend(self.weather_manager.get_weather_pieces())
        self.computer_opponent = ComputerOpponent("Japanese", self.board, self.weather_manager, self.turn_manager)  # Example initialization, can be set to "Allied" or "Japanese"
        self.reposition_taskforces()
        self.turn_manager.current_phase_index = 0
         # Perform initial turn start actions
        perform_observation_phase(self.board, self.weather_manager, self.turn_manager)
        
        

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
    
    def draw_minimap(self):
        # Calculate minimap size and position
        screen_w, screen_h = self.screen.get_size()
        size = int(min(screen_w, screen_h) * self.minimap_scale)
        if not self.minimap_rect:
            self.minimap_rect = pygame.Rect(screen_w - size - 10, 10, size, size)
        else:
            self.minimap_rect.width = size
            self.minimap_rect.height = size
            self.minimap_rect.x = screen_w - size - 10
            self.minimap_rect.y = 10
        # Draw minimap background as sea color
        SEA_COLOR = (80, 160, 220)
        pygame.draw.rect(self.screen, SEA_COLOR, self.minimap_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), self.minimap_rect, 2)
        # Draw hex grid with terrain and weather (skip sea hexes)
        cols, rows = self.board.width, self.board.height
        grid_w, grid_h = cols, rows
        dot_radius = max(2, size // (max(cols, rows) * 4))
        for q in range(cols):
            for r in range(rows):
                hex_obj = self.board.get_hex(q, r)
                # Only draw non-sea terrain and weather overlays
                if hasattr(hex_obj, "terrain") and hex_obj.terrain != "sea":
                    x = self.minimap_rect.x + int((q + 0.5) * size / grid_w)
                    y = self.minimap_rect.y + int((r + 0.5) * size / grid_h)
                    if hex_obj.terrain == "land":
                        color = (34, 139, 34)  # Green
                    elif hex_obj.terrain == "mountain":
                        color = (139, 137, 137)  # Gray
                    elif hex_obj.terrain == "base":
                        color = (255, 215, 0)  # Gold
                    else:
                        color = (120, 120, 120)
                    # Weather overlay
                    weather_piece = next((p for p in self.board.pieces if p.position.q == q and p.position.r == r and isinstance(p, CloudMarker)), None)
                    if weather_piece:
                        if weather_piece.is_storm:
                            color = (180, 0, 180)  # Storm: purple
                        else:
                            color = (200, 200, 200)  # Cloud: light gray
                    pygame.draw.circle(self.screen, color, (x, y), dot_radius)
                else:
                    # Draw weather overlays on sea hexes only if present
                    weather_piece = next((p for p in self.board.pieces if p.position.q == q and p.position.r == r and isinstance(p, CloudMarker)), None)
                    if weather_piece:
                        x = self.minimap_rect.x + int((q + 0.5) * size / grid_w)
                        y = self.minimap_rect.y + int((r + 0.5) * size / grid_h)
                        if weather_piece.is_storm:
                            color = (180, 0, 180)  # Storm: purple
                        else:
                            color = (200, 200, 200)  # Cloud: light gray
                        pygame.draw.circle(self.screen, color, (x, y), dot_radius)
        # Draw TaskForce and AirFormation dots
        for piece in self.board.pieces:
            if FEATURE_FLAG_TESTING:
                can_display = True
            else:
                can_display = (isinstance(piece.game_model, (TaskForce, AirFormation))) and piece.observed_condition > 0
            if piece.side == self.computer_opponent.side and not can_display:
                continue

            if isinstance(piece.game_model, TaskForce):
                color = (255, 0, 0) if piece.side == "Japanese" else (0, 0, 255)
                x = self.minimap_rect.x + int((piece.position.q + 0.5) * size / grid_w)
                y = self.minimap_rect.y + int((piece.position.r + 0.5) * size / grid_h)
                pygame.draw.circle(self.screen, color, (x, y), dot_radius + 2)
            elif isinstance(piece.game_model, AirFormation):
                color = (255, 255, 0) if piece.side == "Japanese" else (0, 255, 0)
                x = self.minimap_rect.x + int((piece.position.q + 0.5) * size / grid_w)
                y = self.minimap_rect.y + int((piece.position.r + 0.5) * size / grid_h)
                pygame.draw.circle(self.screen, color, (x, y), dot_radius + 1)
        # Draw visible region box
        # Calculate visible hex region
        # Calculate the visible hex region based on the current origin offset
        left = max(0, int(-((self.origin[0] - HEX_WIDTH // 2) / (HEX_WIDTH * .75))))
        top = max(0, int(-((self.origin[1] - HEX_HEIGHT // 2) / (HEX_HEIGHT * 1.1))))
        vis_cols = int(self.screen.get_width() / (HEX_WIDTH * .75))
        vis_rows = int(self.screen.get_height() / (HEX_HEIGHT * 1.1))
        box_x = self.minimap_rect.x + int(left * size / grid_w)
        box_y = self.minimap_rect.y + int(top * size / grid_h)
        box_w = int(vis_cols * size / grid_w)
        box_h = int(vis_rows * size / grid_h)
        pygame.draw.rect(self.screen, (255, 255, 255), (box_x, box_y, box_w, box_h), 2)
        # Draw resize handle (bottom right corner)
        handle_size = 12
        handle_rect = pygame.Rect(
            self.minimap_rect.right - handle_size,
            self.minimap_rect.bottom - handle_size,
            handle_size, handle_size)
        pygame.draw.rect(self.screen, (180, 180, 180), handle_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), handle_rect, 2)
        self.minimap_handle_rect = handle_rect

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
                if FEATURE_FLAG_TESTING:
                    can_display = True
                else:
                    can_display = ((isinstance(piece.game_model, (TaskForce, AirFormation))) and piece.observed_condition > 0) or isinstance(piece.game_model, (Base))
                #skip rendering opponent pieces that have not been observed
                if piece.side == self.computer_opponent.side and not can_display:
                    continue
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
                #skip rendering opponent pieces that have not been observed
                pieces_to_display = None
                if FEATURE_FLAG_TESTING:
                    pieces_to_display = pieces
                else:
                    #pieces to display.  Always display bases.  Only display enemy taskforces and airformations that have been observed. Always display own pieces
                    pieces_to_display = [p for p in pieces if (isinstance(p.game_model, Base)) or (p.side != self.computer_opponent.side) or (p.observed_condition > 0 and isinstance(p.game_model, (TaskForce, AirFormation)))]
                if not pieces_to_display:
                    continue
                # Render stack image for multiple pieces
                #identify if any pieces have been observed
                image = PieceImageFactory.stack_image(pieces_to_display, observed=any(p.observed_condition > 0 for p in pieces))
                rect = image.get_rect(center=center)
                self.screen.blit(image, rect)

        # Draw the turn info in the bottom right corner
        self._draw_turn_info()
        self.draw_minimap()

        # If a piece is being moved, draw it at the mouse position
        if self._moving_piece:
            self.show_max_move_distance(self._moving_piece)
        pygame.display.flip()
    
    def _draw_turn_info(self):
        draw_turn_info_popup(self)
        draw_dashboard(self)

    def render_popup(self, piece:Piece, pos):
        if self.computer_opponent.side == piece.side and not FEATURE_FLAG_TESTING: #draw limited details for opponent pieces
            #draw observed status results
            gm = piece.game_model
            if gm and gm.observed_condition > 0:
                gm = piece.game_model
                show_observation_report_popup(self, gm.observation_result, pos)
        else: #draw the details for own pieces
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
        clock = pygame.time.Clock()
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
                    self.minimap_dragging = False
                    self.minimap_resize_start = None
            self.draw()
            clock.tick(30)

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

        # Check if click is on the dashboard
        if self.dashboard.dashboard_rect.collidepoint(event.pos):
            self.dashboard.handle_click(event.pos)
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
        # Minimap resize logic
        if hasattr(self, 'minimap_handle_rect') and self.minimap_handle_rect.collidepoint(event.pos):
            self.minimap_dragging = True
            self.minimap_resize_start = event.pos
            self.minimap_start_scale = self.minimap_scale
            return

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
        # Minimap resizing
        if self.minimap_dragging and self.minimap_resize_start:
            mx, my = event.pos
            sx, sy = self.minimap_resize_start
            delta = max(mx - sx, my - sy)
            screen_w, screen_h = self.screen.get_size()
            base_size = int(min(screen_w, screen_h) * self.minimap_start_scale)
            new_size = max(self.minimap_min_size, min(self.minimap_max_size, base_size + delta))
            self.minimap_scale = new_size / min(screen_w, screen_h)
            return
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
                ## air-to-air summary
                self.show_combat_results(results, pos)
                
                combat_result_id = f"{piece.name}_{self.turn_manager.turn_number}"
                self.turn_manager.add_combat_result(combat_result_id, results)
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

        if results==None:
            return
        
        a2a = results.get("result_attacker_a2a")
        aa = []
        aa.append(results.get("result_tf_anti_aircraft"))
        aa.append(results.get("result_base_anti_aircraft"))
        ship = results.get("result_attacker_ship_air_attack")
        base = results.get("result_attacker_base_air_attack")


        result_data = {"air_to_air": a2a, "anti_aircraft": aa, "base": base, "ship": ship}
        ui = CombatResultsScreen(result_data, self.screen)
        ui.draw_results()
        ui.run()
    

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
    
    

    def save_game(self):
        from flattop.save_load_game import save_game_state
        save_game_state(self.board, self.turn_manager, self.weather_manager)

    def load_game(self):
        import os
        from flattop.save_load_game import load_game_state
        home_dir = os.path.expanduser("~")
        save_dir = os.path.join(home_dir, "flattop_1942")
        if not os.path.exists(save_dir):
            print("No save directory found.")
            return
        files = [f for f in os.listdir(save_dir) if f.endswith(".json")]
        if not files:
            print("No save files found.")
            return
        selected = self._show_file_selection_popup(files)
        if not selected:
            return
        board, turn_manager, weather_manager = load_game_state(filename=selected)
        self.board = board
        self.turn_manager = turn_manager
        self.weather_manager = weather_manager
        computerPlayerSide = self.computer_opponent.side
        self.computer_opponent = ComputerOpponent(computerPlayerSide, self.board, self.weather_manager, self.turn_manager)  # Reinitialize computer opponent
        self.draw()

    def _show_file_selection_popup(self, files):
        # Simple pygame popup for file selection
        font = pygame.font.SysFont(None, 28)
        margin = 10
        option_height = font.get_height() + margin
        menu_width = max(font.size(f)[0] for f in files) + 2 * margin
        menu_height = option_height * len(files) + margin
        screen = self.screen
        screen_w, screen_h = screen.get_size()
        menu_rect = pygame.Rect((screen_w - menu_width) // 2, (screen_h - menu_height) // 2, menu_width, menu_height)
        pygame.draw.rect(screen, (60, 60, 60), menu_rect)
        pygame.draw.rect(screen, (200, 200, 200), menu_rect, 2)
        for i, fname in enumerate(files):
            surf = font.render(fname, True, (255, 255, 255))
            screen.blit(surf, (menu_rect.left + margin, menu_rect.top + margin + i * option_height))
        pygame.display.flip()
        selected = None
        while selected is None:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    if menu_rect.collidepoint(mx, my):
                        idx = (my - menu_rect.top - margin) // option_height
                        if 0 <= idx < len(files):
                            selected = files[idx]
                            break
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return None
        return selected

    def run(self):
        """
        Start the UI event loop.
        """
        self.run_with_click_return()