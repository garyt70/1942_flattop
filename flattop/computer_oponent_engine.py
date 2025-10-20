"""
Computer opponent engine for the Flattop game.
This module contains the logic for the computer opponent's actions and decisions during the game.
It is designed to simulate a human computer's decisions based on the current game state.

Example usage:
---------------
from flattop.computer_oponent_engine import ComputerOpponent

# Create the computer opponent for one side (e.g., 'Japanese')
ai = ComputerOpponent('Japanese')

# In your main game loop, call ai.perform_turn() for the AI side each phase:
# ai.perform_turn(board, weather_manager, turn_manager)

# To perform observation for the AI side:
# ai.perform_observation(board, weather_manager, turn_manager)

# The AI will:
# - Move toward and attack only observed enemy pieces
# - If no enemies are observed, create/search with air formations to try to find the enemy
# - Only use available aircraft for search (from bases or carriers)
# - Use existing combat logic for air-to-air, anti-aircraft, and bombing

# You can extend this class to add more advanced strategies or targeting logic as needed.
"""

"""
TODO: Fixes for known issues:

- Task forces should prioritize attacking enemy ships over land targets
- Combat must remove task forces from the board when they are destroyed (no ships left)

"""

from collections import deque
import random
import logging
from flattop.hex_board_game_model import HexBoardModel, Piece, TurnManager, get_distance
from flattop.operations_chart_models import AirFormation, Aircraft, AircraftOperationsStatus, AircraftType, TaskForce, Base
from flattop.aircombat_engine import (
    classify_aircraft,
    resolve_air_to_air_combat,
    resolve_taskforce_anti_aircraft_combat,
    resolve_base_anti_aircraft_combat,
    resolve_air_to_ship_combat,
    resolve_air_to_base_combat
)
from flattop.game_engine import get_actionable_pieces, perform_observation_for_piece, perform_observation_for_side
from flattop.weather_model import WeatherManager

# Configure logging for this module
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


# Helper to get a unique id for a base_piece (use id() or a unique attribute)
def _get_base_id(base_piece:Piece):
    return base_piece.name

class ComputerOpponent:
    def __init__(self, side:str, board:HexBoardModel=None, weather_manager:WeatherManager=None, turn_manager:TurnManager=None):
        self.side = side  # 'Allied' or 'Japanese'
        self.board = board
        self.weather_manager = weather_manager
        self.turn_manager = turn_manager
        # Track created search air formations per base (by base_piece id)
        self._search_airformation_counts = {}  # {base_piece_id: count}
        logger.info(f"ComputerOpponent initialized for side: {side}")
        
    def _update_last_spotted_taskforce(self, observed_enemy_pieces):
        """
        Update the last known location of enemy task forces.
        """
        if not hasattr(self, '_last_spotted_taskforces'):
            self._last_spotted_taskforces = {}
        for enemy in observed_enemy_pieces:
            gm = getattr(enemy, 'game_model', None)
            if isinstance(gm, TaskForce):
                logger.info(f"Updating last spotted location for enemy task force {enemy.name} at {enemy.position}")
                self._last_spotted_taskforces[enemy.name] = enemy.position

    def _get_last_spotted_taskforce_hex(self):
        """
        Return the most recently spotted enemy task force location, if any.
        """
        if hasattr(self, '_last_spotted_taskforces') and self._last_spotted_taskforces:
            # Return the most recently updated location
            # (dict preserves insertion order in Python 3.7+)
            return list(self._last_spotted_taskforces.values())[-1]
        return None

    def _focused_search_pattern(self, center_hex, radius=2):
        """
        Return a list of hexes in a ring/spiral around center_hex within the given radius.
        """
        from flattop.hex_board_game_model import get_distance
        if not center_hex:
            return []
        return [tile for tile in self.board.tiles if 0 < get_distance(center_hex, tile) <= radius]
    
    def _move_taskforce_toward(self, piece:Piece, target_hex):
        logger.debug(f"_move_taskforce_toward: Moving {piece.name} toward {target_hex}")
        """
        Rules for moving a taskforce toward a target hex:
        - Move only over sea hexes
        - Plot the shortest sea-only path to the target hex, avoiding land hexes.
        - For each move, perform observation.
        """


        def find_shortest_sea_path(start_hex, end_hex):
            """
            Find shortest sea-only path from start_hex to end_hex using a modified postman algorithm.
            The algorithm prefers moving directly toward the destination, but if blocked by land, it tries up to 5 alternative paths around obstacles.
            Returns a list of hexes (including start and end) or None if no path.
            """

            def neighbors(hex):
                return self.board.get_neighbors(hex)

            # Improved shortest sea path algorithm:
            # 1. Try direct route (straight line) from start to end. If all hexes are sea, return that path.
            # 2. If blocked by land, try "left" and "right" detours around the obstacle.
            # 3. If both detours succeed, choose the shortest. If neither, return None.

            def straight_line_path(start_hex, end_hex):
                # Returns a list of hexes from start to end in a straight line (using axial coordinates)
                path = [start_hex]
                q1, r1 = start_hex.q, start_hex.r
                q2, r2 = end_hex.q, end_hex.r
                steps = max(abs(q2 - q1), abs(r2 - r1))
                for i in range(1, steps + 1):
                    t = i / steps
                    q = round(q1 + (q2 - q1) * t)
                    r = round(r1 + (r2 - r1) * t)
                    hex = self.board.get_hex(q, r)
                    if hex:
                        path.append(hex)
                return path

            def is_sea_path(path):
                return all(self.board.get_terrain(hex) == 'sea' for hex in path)

            def detour_path(start_hex, end_hex, direction):
                # direction: 'left' or 'right'
                
                # Modified: Find a path that traces the boundary of land to reach the destination hex.
                # This uses BFS but prefers moves that keep land on one side (i.e., "hug" the coast).

                def trace_land_boundary_path(start_hex, end_hex):
                    visited = set()
                    queue = deque()
                    queue.append((start_hex, [start_hex]))
                    
                    while queue:
                        current, path = queue.popleft()
                        
                        # If current is the end_hex, return path
                        if current == end_hex:
                            return path
                        
                        # Skip if already visited
                        if current in visited:
                            continue
                        visited.add(current)
                        
                        # Get neighbors and filter valid ones
                        current_neighbors = neighbors(current)
                        
                        # Find valid sea neighbors (on board)
                        valid_neighbors = []
                        for neighbor in current_neighbors:
                            # Check if neighbor is on the board
                            if not self.board.is_valid_tile(neighbor):
                                continue
                            
                            # Only consider sea hexes
                            if neighbor.terrain != 'sea':
                                continue
                            
                            # Skip already visited
                            if neighbor in visited:
                                continue
                            
                            valid_neighbors.append(neighbor)
                        
                        # For finding path around islands, prefer hexes adjacent to land
                        # but also allow open sea hexes to ensure we can find a path
                        boundary_neighbors = []
                        open_sea_neighbors = []
                        
                        for neighbor in valid_neighbors:
                            # Check if any of neighbor's neighbors are land
                            neighbor_neighbors = neighbors(neighbor)
                            land_adjacent = any(
                                self.board.is_valid_tile(n) and n.terrain == 'land' 
                                for n in neighbor_neighbors
                            )
                            if land_adjacent:
                                boundary_neighbors.append(neighbor)
                            else:
                                open_sea_neighbors.append(neighbor)
                        
                        # Prioritize boundary neighbors, but also consider open sea
                        # Sort to favor direction and distance to goal
                        if direction == 'left':
                            boundary_neighbors.sort(key=lambda n: (n.q - current.q, n.r - current.r))
                            open_sea_neighbors.sort(key=lambda n: (n.q - current.q, n.r - current.r))
                        else:  # 'right' or default
                            boundary_neighbors.sort(key=lambda n: get_distance(n, end_hex))
                            open_sea_neighbors.sort(key=lambda n: get_distance(n, end_hex))
                        
                        # Add boundary neighbors first, then open sea neighbors
                        all_neighbors = boundary_neighbors + open_sea_neighbors
                        
                        for neighbor in all_neighbors:
                            queue.append((neighbor, path + [neighbor]))
                    
                    return None

                # Use the land boundary tracing pathfinder
                boundary_path = trace_land_boundary_path(start_hex, end_hex)
                if boundary_path:
                    return boundary_path
            # 1. Try direct route
            direct_path = straight_line_path(start_hex, end_hex)
            if is_sea_path(direct_path):
                return direct_path
            else:
                logger.debug(f"Direct path from {start_hex} to {end_hex} blocked by land.")
                # identify the first land hex in the direct path and use that as a waypoint
                waypoint = None
                for hex in direct_path:
                    if hex.terrain == 'land':
                        waypoint = hex #record the last sea hex before land
                        break
                
                #reset the straight line path to contain only sea hexes up to the first land hex
                direct_sea_path = [hex for hex in direct_path if hex.terrain == 'sea']



            # 2. Try left detour
            left_path = detour_path(waypoint, end_hex, 'left')
            # 3. Try right detour
            right_path = detour_path(waypoint, end_hex, 'right')

            # 4. Choose shortest valid path
            valid_paths = [p for p in [left_path, right_path] if p is not None]

            if not valid_paths:
                return None

            detour_path = min(valid_paths, key=len)
            detour_sea_path = [hex for hex in detour_path if hex.terrain == 'sea']
            # Combine direct_sea_path and detour_sea_path, skipping duplicates
            # Start with direct_sea_path, then add detour_sea_path skipping any hex already in direct_sea_path
            sea_path = direct_sea_path + [hex for hex in detour_sea_path[1:] if hex not in direct_sea_path]
            return sea_path


        current_hex = piece.position
        max_steps = piece.movement_factor 
        observed_enemy_pieces = []
        path = find_shortest_sea_path(current_hex, target_hex)
        if path and len(path) > 1:
            # Move up to max_steps along the path
            steps = min(max_steps, len(path) - 1)
            for i in range(1, steps + 1):
                next_hex = path[i]
                logger.debug(f"Moving {piece.name} from {current_hex} to {next_hex} distance {get_distance(current_hex, next_hex)}")
                self.board.move_piece(piece, next_hex)
                current_hex = next_hex
                 # Perform observation after each move
                observed_enemy_pieces = perform_observation_for_piece(piece, self.board, self.weather_manager, self.turn_manager)
                self._update_last_spotted_taskforce(observed_enemy_pieces)
        return observed_enemy_pieces
    
    def _move_toward(self, piece : Piece, target_hex, stop_distance=0):
        logger.debug(f"_move_toward: Moving {piece.name} toward {target_hex} with stop_distance={stop_distance}")
        """
        Move the piece toward the target_hex, stopping at stop_distance if possible.
        Only move over sea hexes for air formations and task forces. Planes do not move into storm hexes.
        """
        observed_enemy_pieces = []

        gm = getattr(piece, 'game_model', None)
        is_plane = isinstance(gm, AirFormation)

        current = piece.position
        max_move = 0
        if is_plane:
            max_move = getattr(piece, 'movement_factor', 1) * getattr(piece.game_model, 'range_remaining', 1)
        elif isinstance(gm, TaskForce):
            max_move = 999 # taskforce has unlimited range for the game
            return self._move_taskforce_toward(piece, target_hex)

        # If already within stop_distance, do not move
        from flattop.hex_board_game_model import get_distance
        distance_to_destination = get_distance(current, target_hex)
        if distance_to_destination <= stop_distance:
            return None
        # Only allow sea hexes, and for planes, avoid storm hexes
        
        candidates = []
        for tile in self.board.tiles:
            if distance_to_destination > max_move:
                continue
            # Only restrict to sea for TaskForce, not for AirFormation (planes can move over land and sea)
            if not is_plane and self.board.get_terrain(tile) != 'sea':
                continue
            if is_plane and self.weather_manager is not None:
                if self.weather_manager.get_weather_at_hex(tile) == 'storm':
                    continue
            candidates.append(tile)
        # Move to the closest hex to target_hex within range, but not closer than stop_distance
        best_hex = None
        best_dist = float('inf')
        for tile in candidates:
            dist = get_distance(tile, target_hex)
            if stop_distance <= dist < best_dist:
                best_hex = tile
                best_dist = dist
        if best_hex:
            # Move in increments of up to 3 hexes toward best_hex

            steps = min(3, get_distance(piece.position, best_hex))
            current_hex = piece.position

            for _ in range(steps):
                # Find the next hex 1 step closer to best_hex
                if is_plane:
                    neighbors = [tile for tile in self.board.tiles if get_distance(current_hex, tile) == 1]
                else:
                    # For taskforces, only consider sea hexes as neighbors
                    neighbors = [tile for tile in self.board.tiles if get_distance(current_hex, tile) == 1 and self.board.get_terrain(tile) == 'sea']
                if not neighbors:
                    break
                # Choose the neighbor closest to best_hex
                next_hex = min(neighbors, key=lambda tile: get_distance(tile, best_hex))
                # Avoid storm hexes for planes
                if is_plane and self.weather_manager and self.weather_manager.get_weather_at_hex(next_hex) == 'storm':
                    break
                current_hex = next_hex
                # Optionally, could observe after each step
                self.board.move_piece(piece, current_hex)
                observed_enemy_pieces = perform_observation_for_piece(piece,self.board, self.weather_manager, self.turn_manager)
                self._update_last_spotted_taskforce(observed_enemy_pieces)
                if len(observed_enemy_pieces) > 0:
                    break

        return observed_enemy_pieces

    def _move_random_within_range(self, piece, max_range=2):
        logger.debug(f"_move_random_within_range: Moving {piece.name} randomly within range {max_range}")
        """
        Move the piece to a random valid hex within max_range, avoiding land for air formations and task forces. Planes do not move into storm hexes.
        """    
        current = piece.position
        gm = getattr(piece, 'game_model', None)
        is_plane = isinstance(gm, AirFormation)
        candidates = []
        for tile in self.board.tiles:
            if tile == current:
                continue
            if get_distance(current, tile) > max_range:
                continue
            if not is_plane and self.board.get_terrain(tile) != 'sea':
                continue
            if is_plane and self.weather_manager is not None:
                if self.weather_manager.get_weather_at_hex(tile) == 'storm':
                    continue
            candidates.append(tile)
        if candidates:
            dest = random.choice(candidates)
            self.board.move_piece(piece, dest)
            observed_enemy_pieces = perform_observation_for_piece(piece,self.board, self.weather_manager, self.turn_manager)
            self._update_last_spotted_taskforce(observed_enemy_pieces)

    def _move_intelligent_search(self, piece, max_range=4):
        logger.info(f"_move_intelligent_search: {piece.name} searching with max_range={max_range}")
        """
        Move the piece in an intelligent search pattern in short increments:
        1. Keep track of previously searched hexes
        2. Maintain consistent direction for multiple turns
        3. Avoid storms and previously searched areas 
        4. Move in short steps (1-2 hexes) and observe after each step
        5. Return to base when fuel is low
        """
        if not hasattr(self, '_search_history'):
            self._search_history = {}  # Track searched hexes
        if not hasattr(self, '_search_direction'):
            self._search_direction = {}  # Track search direction per piece

        current = piece.position
        gm = getattr(piece, 'game_model', None)

        # Initialize search direction if not set
        if piece.name not in self._search_direction:
            self._search_direction[piece.name] = random.choice(['NE', 'E', 'SE', 'SW', 'W', 'NW'])

        # Make multiple short moves of 1-2 hexes up to max_range
        moves_remaining = max_range
        while moves_remaining > 0:
            # Get candidate hexes 1-2 hexes away
            candidates = []
            for tile in self.board.tiles:
                if tile == piece.position:
                    continue
                dist = get_distance(piece.position, tile)
                if dist > min(2, moves_remaining):
                    continue
                # Skip storm hexes for air formations
                if isinstance(gm, AirFormation) and self.weather_manager and self.weather_manager.get_weather_at_hex(tile) == 'storm':
                    continue
                # Prefer unsearched hexes
                if tile not in self._search_history.get(piece.name, set()):
                    candidates.append(tile)

            if not candidates:
                # If no unsearched hexes nearby, allow searched hexes but change direction
                self._search_direction[piece.name] = random.choice(['NE', 'E', 'SE', 'SW', 'W', 'NW'])
                candidates = [tile for tile in self.board.tiles 
                            if tile != piece.position 
                            and get_distance(piece.position, tile) <= min(2, moves_remaining)
                            and (not isinstance(gm, AirFormation) 
                                or not self.weather_manager 
                                or self.weather_manager.get_weather_at_hex(tile) != 'storm')]

            if not candidates:
                break

            # Choose next hex based on current search direction
            direction = self._search_direction[piece.name]
            best_hex = None
            best_score = float('-inf')

            for tile in candidates:
                # Score based on direction and previous searches
                dx = tile.q - piece.position.q
                dy = tile.r - piece.position.r

                # Calculate directional score
                dir_score = {
                    'E': dx,
                    'W': -dx,
                    'NE': dx + dy,
                    'SW': -(dx + dy),
                    'SE': dx - dy,
                    'NW': -dx + dy
                }[direction]

                # Penalty for searched hexes
                search_penalty = -5 if tile in self._search_history.get(piece.name, set()) else 0
                
                score = dir_score + search_penalty
                
                if score > best_score:
                    best_score = score
                    best_hex = tile

            if best_hex:
                # Move piece and reduce remaining movement
                dist_moved = get_distance(piece.position, best_hex)
                observed_enemy_pieces = self._move_toward(piece, best_hex)
                moves_remaining -= dist_moved

                logger.debug(f"Moving {piece.name} from {piece.position} to {best_hex}, distance moved: {dist_moved}")

                # Record searched hex
                if piece.name not in self._search_history:
                    self._search_history[piece.name] = set()
                self._search_history[piece.name].add(best_hex)

                # Perform observation after each move
                if len(observed_enemy_pieces) > 0:
                    #stop when an enemy is spotted
                    moves_remaining = 0
                    break


                # Periodically change direction
                if random.random() < 0.2:  # 20% chance to change direction
                    current_idx = ['NE', 'E', 'SE', 'SW', 'W', 'NW'].index(direction)
                    new_idx = (current_idx + random.choice([-1, 0, 1])) % 6
                    self._search_direction[piece.name] = ['NE', 'E', 'SE', 'SW', 'W', 'NW'][new_idx]
            else:
                break
   

    def perform_turn(self):
        """
        Perform all actions for the computer opponent for the current phase.
        Only move/attack observed enemy pieces. If no enemies are observed, create/search with air formations.
        Handles Air Operations phase: arms aircraft and creates air formations for CAP/interception or search.
        """
        phase = self.turn_manager.current_phase
        logger.info(f"Performing turn for phase: {phase}")
        actionable = get_actionable_pieces(self.board, self.turn_manager, self.side)
        observed_enemy_pieces = [p for p in self.board.pieces if p.side != self.side and getattr(p, 'observed_condition', 0) > 0]
        try:
            if phase == "Air Operations":
                logger.debug("Starting Air Operations phase.")
                self._perform_air_operations_phase(self.board, observed_enemy_pieces)
            elif phase == "Plane Movement":
                logger.debug("Starting Plane Movement phase.")
                self._perform_movement_phase(actionable, observed_enemy_pieces, move_type="plane")
            elif phase == "Task Force Movement":
                logger.debug("Starting Task Force Movement phase.")
                self._perform_movement_phase(actionable, observed_enemy_pieces, move_type="taskforce")
            elif phase == "Combat":
                logger.debug("Starting Combat phase.")
                result = self._perform_combat_phase(actionable, observed_enemy_pieces)
                if result and len(result) > 0:
                    # Add combat results to the turn manager for logging or further processing
                    for k, v in result.items():
                        if v is not None:
                            logger.info(f"Adding combat result for {k}: {v}")
                            self.turn_manager.add_combat_result(k, v)

        except Exception as e:
            logger.error(f"Error during perform_turn: {e}", exc_info=True)
            raise e #quit the game otherwise the exception is being sunk

    def _select_best_armament(self, ac: Aircraft, target_type="CV") -> str:
        attack_factor_ap = max(ac.combat_data.dive_bombing_ship_ap,
                                            ac.combat_data.level_bombing_high_base_ap,
                                            ac.combat_data.level_bombing_low_ship_ap)
        attack_factor_torpedo = ac.combat_data.torpedo_bombing_ship

        if ac.is_interceptor:
            return None  # Interceptors have no armament
         # Prioritize AP for attacking ships, Torpedo for CVs if available, otherwise GP
         # If both AP and Torpedo are available for CVs, choose the higher attack factor
         # If neither AP nor Torpedo is available, use GP
         # For other target types, always use GP

        if target_type == "CV" and (attack_factor_ap > 0 or attack_factor_torpedo > 0):
            return "AP" if attack_factor_ap > attack_factor_torpedo else "Torpedo"
        return "GP"

    def _create_interceptor_formation(self, air_targets:Piece, base_position, base:Base):
    
        ready = list(base.air_operations_tracker.ready)
        if not ready:
            return
        
        # If there are ready aircraft, create an interceptor air formation to attack
        max_launch = min(sum(ac.count for ac in ready), base.available_launch_factor_max - base.used_launch_factor)
        if max_launch <= 0:
            return

        for air_target in air_targets:
            dist = get_distance(base_position, air_target.position)
            if dist <= 10:
                interceptors = [ac for ac in ready if ac.armament is None and ac.is_interceptor]
                if interceptors:
                    af = base.create_air_formation(random.randint(1, 35), aircraft=interceptors)
                    if af:
                        logger.debug(f"Creating interceptor air formation {af.name} at base {base.name} for air target {air_target.name}.")
                        af_piece = Piece(name=af.name, side=self.side, position=base_position, gameModel=af)
                        self.board.add_piece(af_piece)
                    break

    def _perform_air_operations_ready_factor(self, base:Base):
        """
        Move aircraft from just landed to readying based on available ready factors.
        """
       
        if base.used_ready_factor >= base.available_ready_factor:
            logger.debug(f"Base {base.name} has no ready factors left, skipping moving just landed aircraft.")
            return

        readying = list(base.air_operations_tracker.readying)
        for ac in readying:
            max_ready = min(ac.count, base.available_ready_factor - base.used_ready_factor)
            if max_ready <= 0:
                break
            best_armament = self._select_best_armament(ac)
            to_aircraft : Aircraft = ac.copy()
            to_aircraft.armament = best_armament
            to_aircraft.count = max_ready
            base.air_operations_tracker.set_operations_status(to_aircraft, AircraftOperationsStatus.READY, ac)
            logger.debug(f"Moving {to_aircraft.count} aircraft {to_aircraft.type} to ready at base {base.name}.")
        if base.used_ready_factor >= base.available_ready_factor:
            return
        # Move aircraft from just landed to readying based on available ready factors.
        for ac in list(base.air_operations_tracker.just_landed):
            max_ready = min(ac.count, base.available_ready_factor - base.used_ready_factor)
            if max_ready <= 0:
                break
            to_aircraft : Aircraft = ac.copy()
            to_aircraft.count = max_ready
            base.air_operations_tracker.set_operations_status(to_aircraft, AircraftOperationsStatus.READYING, ac)
            logger.debug(f"Moving {to_aircraft.count} aircraft {to_aircraft.type} to readying at base {base.name}.")

    def _perform_air_operations_phase(self, board, observed_enemy_pieces):
        """
        AI logic for Air Operations phase:
        - If a TaskForce is observed, arm aircraft with AP (armor-piercing) if available in readying, and move to ready if ready factors allow.
        - If an enemy AirFormation is observed within 10 hexes of a base, create an interceptor air formation if possible.
        - If no observed enemies, create search air formations using best (longest range) ready aircraft, in small groups (1-3 aircraft), and only if ready/launch factors allow.
        - Move aircraft in just landed to readying, using ready_factor limits.
        """
        own_pieces = [p for p in board.pieces if p.side == self.side]
        base_pieces = [p for p in own_pieces if isinstance(p.game_model, Base)]
        taskforce_pieces = [p for p in own_pieces if isinstance(p.game_model, TaskForce)]
        bases = [p.game_model for p in base_pieces if isinstance(p.game_model, Base)]
        carrier_bases = []
        for p in taskforce_pieces:
            carrier_bases.extend(p.game_model.get_carriers())

        bases.extend([c.base for c in carrier_bases if hasattr(c, 'base') and c.base is not None])  

        for base in bases:
            self._perform_air_operations_ready_factor(base)

        # 1. Arm aircraft with AP if TaskForce is observed and launch them to attack
        taskforce_targets = [p for p in observed_enemy_pieces if isinstance(p.game_model, TaskForce)]
        if taskforce_targets:
            base:Base
            for base in bases:
                ready = list(base.air_operations_tracker.ready)
                if ready:
                    # If there are ready aircraft, create an air formation to attack
                    max_launch = min(sum(ac.count for ac in ready), base.available_launch_factor_max - base.used_launch_factor)
                    if max_launch <= 0:
                        continue
                    attack_aircraft = self._select_best_ready_aircraft(ready, max_count=max_launch, purpose="attack_ship")
                    af = base.create_air_formation(random.randint(1, 35), aircraft=attack_aircraft)
                    if af:
                        logger.debug(f"Creating air formation {af.name} at base {base.name} to attack taskforce.")
                        af_piece = Piece(name=af.name, side=self.side, position=base_piece.position, gameModel=af)
                        board.add_piece(af_piece)

        
        # 2. If enemy AirFormation observed within 10 hexes, create interceptor air formation if possible
        air_targets = [p for p in observed_enemy_pieces if isinstance(p.game_model, AirFormation)]
        if air_targets and len(air_targets) > 0:
            logger.info(f"Observed enemy air targets, creating interceptors")
            for base_piece in base_pieces:
                self._create_interceptor_formation(air_targets, base_piece.position, base_piece.game_model)
            for tf_piece in taskforce_pieces:
                tf:TaskForce  = tf_piece.game_model
                for carrier in tf.get_carriers() if hasattr(tf, 'get_carriers') else []:
                    base = getattr(carrier, 'base', None)
                    if not base:
                        continue
                    self._create_interceptor_formation(air_targets, tf_piece.position, base)
        
        # 3. If no observed enemies, create search air formations (using best ready aircraft, 1-3 per formation, and only if ready/launch factors allow)
        if not observed_enemy_pieces:
            logger.info("No observed enemies. Creating search air formations.")
            self._create_search_airformations(board)

    def _handle_airformation_move_to_base(self, piece, nearest_base_piece:Piece, min_range_left, min_base_dist):
        # Move toward base in short hops (2-3 hexes)
        hops = min(3, min_range_left, min_base_dist)
        for _ in range(hops):
            if get_distance(piece.position, nearest_base_piece.position) > 0:
                self.board.move_piece(piece, nearest_base_piece.position)
                # Optionally, call observation after each move
                if hasattr(self, 'perform_observation'):
                    self.perform_observation()
        # If air formation is at base, land it and remove from board
        if piece.position == nearest_base_piece.position:
            base: Base = None
            if isinstance(nearest_base_piece.game_model, TaskForce):
                # If the base is on a carrier, get the carrier's base
                carrier: TaskForce = nearest_base_piece.game_model
                carriers = carrier.get_carriers()
                if carriers and len(carriers) > 0:
                    base = carriers[0].base
            else:
                base = nearest_base_piece.game_model
                
            
            nearest_base_piece.game_model
            airformation: AirFormation = piece.game_model
            # Land each aircraft in the air formation
            logger.info(f"AirFormation {airformation.name} landing at base {base.name}.")
            for ac in airformation.aircraft:
                # Add aircraft back to base's tracker (simulate landing)
                base.air_operations_tracker.set_operations_status(ac, AircraftOperationsStatus.JUST_LANDED)
                logger.info(f"Aircraft {ac} landed at base {base.name}.")
                # If this is a search airformation, reduce the count for the origin base
                if hasattr(airformation, '_is_search_formation') and airformation._is_search_formation:
                    origin_base_id = getattr(airformation, '_origin_base', None)
                    if origin_base_id:
                        # Find base ID for the origin base
                        if origin_base_id in self._search_airformation_counts:
                            self._search_airformation_counts[origin_base_id] = max(0, self._search_airformation_counts[origin_base_id] - 1)
                            logger.debug(f"Reduced search airformation count for base {origin_base_id} to {self._search_airformation_counts[origin_base_id]}")
                        break
            # Remove air formation piece from board
            if piece in self.board.pieces:
                self.board.pieces.remove(piece)

    def _handle_check_airformation_fuel_ammo_and_move(self, piece:Piece, base_pieces):

        af : AirFormation = piece.game_model
        # Check if any aircraft in formation has low fuel (just enough to return to base)
        # the -5 is to give some movement for landing.
        min_range_left = af.range_remaining * af.movement_factor - 5
        logger.info(f"Checking range of AirFormation {af.name}")
        logger.debug(f"AirFormation {af.name} has min_range_left={min_range_left}")

        # Find nearest base
        nearest_base_piece = None
        min_base_dist = float('inf')
        for base_piece in base_pieces:
            dist = get_distance(piece.position, base_piece.position)
            if dist < min_base_dist:
                min_base_dist = dist
                nearest_base_piece = base_piece
        # If range is low (<= distance to base + 1), start moving back
        if (nearest_base_piece and min_range_left <= min_base_dist + 1) or af.range_remaining <= 2:
            logger.info(f"AirFormation {af.name} low on fuel, moving toward nearest base {nearest_base_piece}.")
            self._handle_airformation_move_to_base(piece, nearest_base_piece, min_range_left, min_base_dist)
            return True  # Indicate that movement was handled
        
        # if a bomber and there are no armed aircraft then move toward base to re-arm
        if any(ac.is_bomber and ac.armament is None for ac in af.aircraft):
            logger.info(f"AirFormation {af.name} no longer armed, moving toward nearest base {nearest_base_piece}.")
            self._handle_airformation_move_to_base(piece, nearest_base_piece, min_range_left, min_base_dist)
            return True  # Indicate that movement was handled
        
        return False  # No special movement needed
    

    def _perform_taskforce_movement_phase(self, actionable, observed_enemy_pieces):
       
        # If actionable is None, recompute it
        if actionable is None:  
            # Only move pieces belonging to the computer side
            actionable = [p for p in actionable if p.side == self.side and p.can_move and not p.has_moved and isinstance(getattr(p, 'game_model', None), TaskForce)]
        
        base_pieces = [p for p in actionable if isinstance(p.game_model, Base)]
        base_hexes = [b.position for b in base_pieces]
        # Update last spotted enemy task force locations
        self._update_last_spotted_taskforce(observed_enemy_pieces)
        last_spotted_hex = self._get_last_spotted_taskforce_hex()

        for piece in actionable:
            logger.debug(f"Processing piece {piece.name} for movement.")

            #determine task force type = CV == carrier group, transport or battle group
            tf : TaskForce = piece.game_model
            tf_type = None
            if any(ship.type == "AP" for ship in tf.ships):
                #a taskforce with an AP is a transport group even if there are carriers present
                tf_type = 'transport'
            elif hasattr(tf, 'get_carriers') and tf.get_carriers():
                tf_type = 'carrier'
            else:
                tf_type = 'battle'

            

            if (not observed_enemy_pieces or len(observed_enemy_pieces) == 0) and not last_spotted_hex:
                logger.info(f"No observed enemies for piece {piece.name}. Moving in search pattern.")
                # No observed enemies: move in a search pattern                
                """
                task force movement rules
                
                - Move toward last known enemy task force location if available
                - Move toward nearest enemy base 
                - Taskforce with carriers should keep their distance from enemy task forces (at least 10-20 hexes)
                - Otherwise, move randomly but avoid clustering with other friendly task forces (maintain at least 2-3 hexes apart)
                """

                
                # Move toward last known enemy task force location if available
                last_spotted_hex = self._get_last_spotted_taskforce_hex()
                if last_spotted_hex and tf_type in ['carrier', 'battle']:

                    dist_to_enemy_tf = get_distance(piece.position, last_spotted_hex)
                    if tf_type == 'carrier' and dist_to_enemy_tf < 10:
                        # Move away from enemy task force
                        candidates = [tile for tile in self.board.tiles
                                        if self.board.get_terrain(tile) == 'sea'
                                        and get_distance(tile, last_spotted_hex) > 10
                                        and get_distance(piece.position, tile) <= 3]
                        if candidates:
                            dest = random.choice(candidates)
                            self.board.move_piece(piece, dest)
                    else:
                        # Move toward enemy task force
                        self._move_toward(piece, last_spotted_hex, stop_distance=0)
                else:
                    logger.info(f"No last spotted enemy task force location for piece {piece.name} or transport, moving towards enemy base.")
                    # Move toward nearest enemy base
                    enemy_base_pieces = [p for p in self.board.pieces if p.side != self.side and isinstance(p.game_model, Base)]
                    if enemy_base_pieces:
                        nearest_base = min(enemy_base_pieces, key=lambda b: get_distance(piece.position, b.position))
                        self._move_toward(piece, nearest_base.position, stop_distance=0)
            else:
                # Observed enemies present: 
                # Carriers should move no closer than 10 hexes to observed enemy task forces
                # Battle groups can move directly toward observed enemy task forces
                # Transports should avoid observed enemy task forces by at least 20 hexes and moved toward nearest enemy base

                logger.info(f"Observed enemies present. Moving piece {piece.name} toward nearest enemy.")
                if last_spotted_hex and tf_type in ['carrier', 'battle']:

                    dist_to_enemy_tf = get_distance(piece.position, last_spotted_hex)
                    if tf_type == 'carrier' and dist_to_enemy_tf < 10:
                        # Move away from enemy task force
                        candidates = [tile for tile in self.board.tiles
                                        if self.board.get_terrain(tile) == 'sea'
                                        and get_distance(tile, last_spotted_hex) > 10
                                        and get_distance(piece.position, tile) <= 3]
                        if candidates:
                            dest = random.choice(candidates)
                            self.board.move_piece(piece, dest)
                    else:
                        # Move toward enemy task force
                        self._move_toward(piece, last_spotted_hex, stop_distance=0)
                else:
                    logger.info(f"No last spotted enemy task force location for piece {piece.name} or transport, moving towards enemy base.")
                    # Move toward nearest enemy base
                    enemy_base_pieces = [p for p in self.board.pieces if p.side != self.side and isinstance(p.game_model, Base)]
                    if enemy_base_pieces:
                        nearest_base = min(enemy_base_pieces, key=lambda b: get_distance(piece.position, b.position))
                        self._move_toward(piece, nearest_base.position, stop_distance=0)
                
        # Additional rules to consider:
        # - Air formations should avoid moving into hexes with friendly task forces to prevent stacking.
        # - Bombers should coordinate attacks if multiple formations are available (strike together).
        # - Interceptors could prioritize defending high-value bases/carriers.
        # - Task forces should avoid moving into hexes with enemy air formations unless protected by CAP.
        # - Air formations should avoid moving into hexes with poor weather (clouds) unless necessary for attack.
        # - Implement fuel/range tracking for each aircraft and force landing if range is too low.
        # - Add logic for retreating if odds are unfavorable (e.g., outnumbered/intercepted).

    def _perform_airformation_movement_phase(self, actionable, observed_enemy_pieces):

        if actionable is None:  
            # Only move pieces belonging to the computer side
            actionable = [p for p in actionable if p.side == self.side and p.can_move and not p.has_moved and isinstance(getattr(p, 'game_model', None), AirFormation)]
        

        own_pieces = [p for p in self.board.pieces if p.side == self.side]
        base_pieces = [p for p in own_pieces if isinstance(p.game_model, Base)]
        #add taskforce carriers as bases
        taskforce_pieces = [p for p in own_pieces if isinstance(p.game_model, TaskForce)]
        for p in taskforce_pieces:
            tf:TaskForce = p.game_model
            carriers = tf.get_carriers() if hasattr(tf, 'get_carriers') else []
            if carriers:
                #as there can only be one carrier per taskforce in the current game then we can add just the taskforce
                base_pieces.append(p)
            
        base_hexes = [b.position for b in base_pieces]
        # Update last spotted enemy task force locations
        self._update_last_spotted_taskforce(observed_enemy_pieces)
        last_spotted_hex = self._get_last_spotted_taskforce_hex() if not observed_enemy_pieces else None

        piece:Piece
        for piece in actionable:
            logger.debug(f"Processing piece {piece.name} for movement.")
            af:AirFormation = getattr(piece, 'game_model', None)
            #handle running out of range
            # Range logic: if any aircraft in formation has just enough range to return to base, move toward nearest base
            logger.debug(f"Checking low fuel for AirFormation {af.name}.")
            if self._handle_check_airformation_fuel_ammo_and_move(piece, base_pieces):
                continue

            # If no currently observed enemy, but a task force was previously spotted, do focused search
            
            search_airformations = []
            if last_spotted_hex:
                logger.info(f"No currently observed enemies, but last spotted at {last_spotted_hex}. Performing focused search.")
                # Select 2-3 available air formations (prefer bombers)
                airformations = [p for p in actionable if isinstance(getattr(p, 'game_model', None), AirFormation)]
                bombers = [p for p in airformations if any(ac.is_bomber for ac in p.game_model.aircraft)]
                others = [p for p in airformations if p not in bombers]
                search_airformations = bombers[:3] if len(bombers) >= 2 else (bombers + others)[:3]

                # Get search hexes around last spotted location
                search_hexes = self._focused_search_pattern(last_spotted_hex, radius=2)
                # Assign each air formation a different search hex (spread out)
                for idx, piece in enumerate(search_airformations):
                    if search_hexes:
                        target_hex = search_hexes[idx % len(search_hexes)]
                        self._move_toward(piece, target_hex, stop_distance=0)
                        if hasattr(self, 'perform_observation'):
                            observed_enemy_pieces = self.perform_observation()
                            self._update_last_spotted_taskforce(observed_enemy_pieces)
                continue


            if (not observed_enemy_pieces or len(observed_enemy_pieces) == 0) and not last_spotted_hex:
                logger.info(f"No observed enemies for piece {piece.name}. Moving in search pattern.")
                # No observed enemies: move in a search pattern                
                
                # Classify aircraft: if all are bombers, treat as bomber; else, treat as fighter/interceptor
                is_bomber = any(ac.is_bomber for ac in af.aircraft)

                if is_bomber and base_hexes:
                    # Bombers: search more widely (random within movement range)
                    move_range = getattr(af, 'movement_factor', 4)
                    self._move_intelligent_search(piece, max_range=move_range)
                else:
                    # Fighters/interceptors: move close to nearest base (within 2-3 hexes)
                    logger.debug(f"Fighter/interceptor {piece.name} logic")
                    # Find nearest base
                    min_dist = float('inf')
                    nearest_base = None
                    for base_hex in base_hexes:
                        dist = get_distance(piece.position, base_hex)
                        if dist < min_dist:
                            min_dist = dist
                            nearest_base = base_hex
                    # Move toward base, but not into the base hex (prefer 1-3 hexes away)
                    if nearest_base and min_dist > 1:
                        # Make multiple short moves (2-3 hexes) toward base
                        logger.debug(f"Fighter/interceptor {piece.name} moving toward nearest base.")
                        hops = min(3, min_dist)
                        for _ in range(hops):
                            if get_distance(piece.position, nearest_base) > 1:
                                result = self._move_toward(piece, nearest_base, stop_distance=1)
                                if len(result) > 0:
                                    break #stop moving
                    else:
                        # Already close, loiter or move randomly within 2 hexes
                        logger.debug(f"Fighter/interceptor {piece.name} already close to base, loitering.")
                        self._move_random_within_range(piece, max_range=4)
                
            else:
                logger.info(f"Observed enemies present. Moving piece {piece.name} toward nearest enemy.")
                # Move each actionable piece toward the nearest observed enemy
                #Rules for moving toward enemy:
                # - If the enemy is an airformation then keep own interceptor formations a the nearest friendly base , This is the CAP for the base.
                # - If the enemy is a TaskForce, move toward it so that the computer opponent can attack it with its air formations.
                # - If the enemy is a Base, move toward it to attack with air formations.
                # - Computer opponent airformations with bombers should continue to follow the enemy TaskForce or Base, but not move into storm hexes.
                # - Air formations make multiple short moves (2-3 hexes) toward their destination
                # Gather friendly task force positions for stacking avoidance
                friendly_taskforce_hexes = [p.position for p in self.board.pieces if p.side == self.side and isinstance(getattr(p, 'game_model', None), TaskForce)]
                # Gather all actionable bombers for coordination
                actionable_bombers = [p for p in actionable if isinstance(getattr(p, 'game_model', None), AirFormation) and all(ac.armament is not None for ac in p.game_model.aircraft)]
                # Track which bombers have already moved for coordination
                bombers_moved = set()
                
                if not piece.can_move:
                    continue

                # Find nearest enemy and its type
                min_dist = float('inf')
                target = None
                target_type = None
                for enemy in observed_enemy_pieces:
                    dist = get_distance(piece.position, enemy.position)
                    if dist < min_dist:
                        min_dist = dist
                        target = enemy
                        target_type = type(enemy.game_model)
                if target:
                    # CAP logic: If enemy is AirFormation and own piece is interceptor, prioritize high-value base/carrier
                    is_interceptor = any(ac.is_interceptor for ac in af.aircraft)
                    if target_type == AirFormation and is_interceptor:
                        logger.debug(f"Interceptor {af.name} prioritizing CAP for base/carrier.")
                        # Prioritize high-value base/carrier for CAP
                        high_value_bases = [b for b in base_pieces if getattr(b.game_model, 'is_high_value', False)]
                        cap_base_hexes = [b.position for b in high_value_bases] if high_value_bases else base_hexes
                        min_base_dist = float('inf')
                        nearest_base = None
                        for base_hex in cap_base_hexes:
                            dist = get_distance(piece.position, base_hex)
                            if dist < min_base_dist:
                                min_base_dist = dist
                                nearest_base = base_hex
                        # Move to base if not already there
                        if nearest_base and piece.position != nearest_base:
                            self._move_toward(piece, nearest_base, stop_distance=0)
                            if hasattr(self, 'perform_observation'):
                                self.perform_observation()
                        continue
                    # Bombers: coordinate attacks if multiple formations are available
                    is_bomber = any(ac.is_bomber for ac in af.aircraft)
                    if target_type in (TaskForce, Base) and is_bomber:
                        logger.debug(f"Bomber {af.name} coordinating attack on {target.name}.")
                        # Only move bombers together if not already moved
                        if piece not in bombers_moved:
                            # Find all bombers targeting the same enemy
                            group = [b for b in actionable_bombers if get_distance(b.position, target.position) == min_dist]
                            for bomber in group:
                                hops = min(3, min_dist)
                                for _ in range(hops):
                                    if get_distance(bomber.position, target.position) > 0:
                                        self._move_toward(bomber, target.position)
                                        if hasattr(self, 'perform_observation'):
                                            self.perform_observation()
                                bombers_moved.add(bomber)
                        continue
                    # Other air formations: avoid stacking with friendly task forces and avoid poor weather
                    if target_type in (TaskForce, Base) and not is_bomber:
                        hops = min(3, min_dist)
                        for _ in range(hops):
                            if get_distance(piece.position, target.position) > 0:
                                next_hex = target.position

                                # Avoid storms
                                if self.weather_manager.is_storm_hex(next_hex):
                                    self._move_random_within_range(piece, max_range=2)
                                else:
                                    self._move_toward(piece, next_hex)
                                self.perform_observation()
                        continue
                    # If enemy is AirFormation and own piece is not interceptor, loiter or move randomly
                    if target_type == AirFormation and not is_interceptor:
                        self._move_random_within_range(piece, max_range=2)
                        self.perform_observation()
                        continue
                   
        # Additional rules to consider:
        # - Air formations should avoid moving into hexes with friendly task forces to prevent stacking.
        # - Bombers should coordinate attacks if multiple formations are available (strike together).
        # - Interceptors could prioritize defending high-value bases/carriers.
        # - Task forces should avoid moving into hexes with enemy air formations unless protected by CAP.
        # - Air formations should avoid moving into hexes with poor weather (clouds) unless necessary for attack.
        # - Implement fuel/range tracking for each aircraft and force landing if range is too low.
        # - Add logic for retreating if odds are unfavorable (e.g., outnumbered/intercepted).

    def _perform_movement_phase(self, actionable, observed_enemy_pieces, move_type=None):
        logger.info(f"Executing movement phase for move_type={move_type}")
        """
        Move phase logic:
        - If observed enemy pieces exist, move toward nearest observed enemy.
        - If no observed enemies, move in a search pattern:
            - Fighters/interceptors (non-bombers) move close to bases (CAP/intercept role).
            - Bombers can search more widely (random within range).
        - Air formations consider aircraft range; if low, move toward nearest base.
        - Air formations make multiple short moves (2-3 hexes) toward their destination, observing after each move.
        """
        # If actionable is None, recompute it
        if actionable is None:
            
            actionable = get_actionable_pieces(self.board, self.turn_manager, self.side)
        if not actionable:
            return
        # Only move pieces belonging to the computer side
        actionable = [p for p in actionable if p.side == self.side and p.can_move and not p.has_moved]
        # Determine which type of pieces to move this phase
        if move_type == "plane":
            self._perform_airformation_movement_phase(actionable, observed_enemy_pieces)
            return
        elif move_type == "taskforce":
            self._perform_taskforce_movement_phase(actionable, observed_enemy_pieces)
            return
        
        

    def _perform_combat_phase_for_piece_in_hex(self, piece, observed_enemy_pieces):
        logger.debug(f"Resolving combat for {piece.name} in hex {piece.position}")
        """
        Perform combat for a single piece in a hex with observed enemy pieces.
        This is a helper function to handle combat resolution for a specific piece.
        """
        if not observed_enemy_pieces:
            return None
        # Check if the piece is in a hex with observed enemy pieces
        hex_enemies = [e for e in observed_enemy_pieces if e.position == piece.position]
        if not hex_enemies:
            return None
        
        # Check if the piece is in a hex with other air formations on the same side
        hex_airformations = [
            p for p in self.board.pieces
            if isinstance(p.game_model, AirFormation)
            and p.position == piece.position
            and p.side == piece.side
        ]

        computer_taskforce_pieces = [p for p in self.board.pieces if isinstance(p.game_model, TaskForce) and p.side == piece.side and p.position == piece.position]
        enemy_taskforce_pieces = [p for p in self.board.pieces if isinstance(p.game_model, TaskForce) and p.side != piece.side and p.position == piece.position]

        computer_taskforce_p:TaskForce = None
        # if there is more than one taskforce, then we need to choose the one with the most carriers and high value ships
        def get_high_value_ship_count(taskforce):
            """
            Returns a tuple representing the number of high value ships in the taskforce,
            ordered by priority: (CV_count, BBS_count, CA_count, other_count)
            """
            if not hasattr(taskforce, 'ships'):
                return (0, 0, 0, 0)
            cv_types = ('CV', 'CVA')
            bbs_types = ('BBS',)
            ca_types = ('CA',)
            cv_count = sum(1 for ship in taskforce.ships if getattr(ship, 'type', None) in cv_types)
            bbs_count = sum(1 for ship in taskforce.ships if getattr(ship, 'type', None) in bbs_types)
            ca_count = sum(1 for ship in taskforce.ships if getattr(ship, 'type', None) in ca_types)
            other_count = sum(1 for ship in taskforce.ships if getattr(ship, 'type', None) not in cv_types + bbs_types + ca_types)
            return (cv_count, bbs_count, ca_count, other_count)

        if len(computer_taskforce_pieces) > 0:
            computer_taskforce_pieces = sorted(
            computer_taskforce_pieces,
            key=lambda p: (
                len(p.game_model.get_carriers() if hasattr(p.game_model, 'get_carriers') else []),
                get_high_value_ship_count(p.game_model)
            ),
            reverse=True
            )
            computer_taskforce_p = computer_taskforce_pieces[:1][0]

        enemy_taskforce_p:TaskForce = None
        if len(enemy_taskforce_pieces) > 0:
            enemy_taskforce_pieces = sorted(
            enemy_taskforce_pieces,
            key=lambda p: (
                len(p.game_model.get_carriers() if hasattr(p.game_model, 'get_carriers') else []),
                get_high_value_ship_count(p.game_model)
            ),
            reverse=True
            )
            enemy_taskforce_p = enemy_taskforce_pieces[:1][0]

        computer_airformations = [p.game_model for p in hex_airformations if p.side == piece.side]
        enemy_airformations = [p.game_model for p in hex_enemies if isinstance(p.game_model, AirFormation) and p.position == piece.position]

        # Gather aircraft by role (interceptor, escort, bomber)
        computer_interceptors, computer_escorts, computer_bombers = classify_aircraft(computer_airformations)
        enemy_interceptors, enemy_escorts, enemy_bombers = classify_aircraft(enemy_airformations)

        pre_combat_count_computer_interceptors = sum(ic.count for ic in computer_interceptors)
        pre_combat_count_computer_bombers = sum(b.count for b in computer_bombers)
        pre_combat_count_computer_escorts = sum(ec.count for ec in computer_escorts)

        pre_combat_count_enemy_interceptors = sum(ic.count for ic in enemy_interceptors)
        pre_combat_count_enemy_bombers = sum(b.count for b in enemy_bombers)
        pre_combat_count_enemy_escorts = sum(ec.count for ec in enemy_escorts)

        

        result_computer_a2a = None

        in_clouds = self.weather_manager.is_cloud_hex(piece.position)
        at_night = self.turn_manager.is_night()

        # For simplicity, assume two sides: Allied and Japanese
        #and there are two airformations

        # if no bombers on either side then convert interceptors to escorts
        result_computer_a2a = None
        if not computer_bombers and not enemy_bombers:
            # Convert interceptors to escorts for one side so that we have interceptor to interceptor combat
            enemy_escorts.extend(enemy_interceptors)
            enemy_interceptors = []
        elif computer_interceptors and enemy_bombers:
            result_computer_a2a = resolve_air_to_air_combat(
                interceptors=computer_interceptors,
                escorts=enemy_escorts,
                bombers=enemy_bombers,
                rf_expended=True,
                clouds=in_clouds,
                night=at_night)
        elif enemy_interceptors and computer_bombers:
            result_computer_a2a = resolve_air_to_air_combat(
                interceptors=enemy_interceptors,
                escorts=computer_escorts,
                bombers=computer_bombers,
                rf_expended=True,
                clouds=in_clouds,
                night=at_night)

        # need to update the air operations chart for each side
        # remove aircraft from air formations that have 0 or less count
        # removed airformations that have no aircraft left
        for af in computer_airformations:
            af.aircraft = [ac for ac in af.aircraft if ac.count > 0]
            if len(af.aircraft) == 0:
                logger.debug(f"Removing empty computer air formation {af.name} from board.")
                self.board.pieces.remove(next(p for p in self.board.pieces if p.game_model == af))
        for af in enemy_airformations:
            af.aircraft = [ac for ac in af.aircraft if ac.count > 0]
            if len(af.aircraft) == 0:
                logger.debug(f"Removing empty enemy air formation {af.name} from board.")
                self.board.pieces.remove(next(p for p in self.board.pieces if p.game_model == af))

        ### execute anti aircraft combat ###
        # the taskforce being attacked by the air formations need to be selected.
        # find the allied taskforces in the hex with the japanese airformation and enable user to select one
        # find the japanese taskforces in the hex with the allied airformation and enable user to select one
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
        if enemy_taskforce_p:
            result_tf_anti_aircraft = perform_taskforce_anti_aircraft_combat(computer_bombers, enemy_taskforce_p.game_model, piece.position)

        enemy_base_pieces = [p for p in self.board.pieces if isinstance(p.game_model, Base) and p.side != piece.side and p.position == piece.position]
         #assume there is only ever one base
        result_base_anti_aircraft = None
        if enemy_base_pieces:
            result_base_anti_aircraft = perform_base_anti_aircraft_combat(computer_bombers,enemy_base_pieces[0].game_model)

        #### execute the air combat attack against selected ship ####

        def perform_air_to_ship_combat(bombers:list[Aircraft], taskforce:TaskForce):
            # this involves choosing which ship is attacked by which aircraft
            # and then resolve the combat for each ship

            if not bombers or not taskforce:
                return None

            if len(bombers) == 0:
                return None


            # Allocate bombers to ships in the taskforce, prioritizing high-value ships, carriers, and battleships
            def allocate_bombers_to_ships(bombers, ships):
                """
                Allocate bombers to ships in the taskforce, prioritizing high-value ships:
                - Carrier (CV): 3 x ship.damage_factor aircraft
                - Battleship (BBS): 4 x ship.damage_factor aircraft
                - Capital ships (CA): 3 x ship.damage_factor aircraft
                - Others: 5 aircraft per ship
                Returns a dict: {ship: [list of bombers]}
                """
                if not bombers or not ships:
                    return {}

                # Flatten bombers into a list of individual aircraft (if count > 1)
                bomber_list = []
                for bomber in bombers:
                    for _ in range(getattr(bomber, "count", 1)):
                        bomber_copy = bomber.copy() if hasattr(bomber, "copy") else bomber
                        bomber_copy.count = 1
                        bomber_list.append(bomber_copy)

                allocation = {ship: [] for ship in ships}

                # Determine allocation requirements per ship
                ship_requirements = []
                for ship in ships:
                    ship_type = getattr(ship, "type", "")
                    damage_factor = getattr(ship, "damage_factor", 1)
                    if ship_type == "CV":
                        required = 3 * damage_factor
                    elif ship_type == "BBS":
                        required = 4 * damage_factor
                    elif ship_type == "CA":
                        required = 3 * damage_factor
                    else:
                        required = 5
                    ship_requirements.append((ship, required))

                # Allocate bombers to ships by priority until bombers run out
                bomber_idx = 0
                total_bombers = len(bomber_list)
                for ship, required in ship_requirements:
                    allocated = 0
                    while allocated < required and bomber_idx < total_bombers:
                        allocation[ship].append(bomber_list[bomber_idx])
                        allocated += 1
                        bomber_idx += 1
                    # If bombers run out, stop allocating
                    if bomber_idx >= total_bombers:
                        break

                # Optionally, merge bombers of the same type back into single objects with count
                for ship, bombers in allocation.items():
                    type_map = {}
                    for b in bombers:
                        key = (getattr(b, "type", None), getattr(b, "armament", None))
                        if key not in type_map:
                            b_copy = b.copy() if hasattr(b, "copy") else b
                            b_copy.count = 1
                            type_map[key] = b_copy
                        else:
                            type_map[key].count += 1
                    allocation[ship] = list(type_map.values())

                return allocation
            
            allocation = allocate_bombers_to_ships(bombers, taskforce.ships)
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

            for bomber in bombers:
                # because the computer logic does a allocation of bombers to ships as a copy of the original bomber,
                # we need to set the armament to None after combat so that the bomber is not used again in the next combat phase.
                # This is to simulate the bomber being used up in the combat.
                # 
                # Set armament to None after combat
                bomber.armament = None
                # reduce the range by 1 for each bomber that has attacked
                #if height is high and attack is level then do not reduce range
                if bomber.height != "High" or bomber.attack_type != "Level":
                    bomber.range_remaining = max(0, bomber.range_remaining - 1)

            return results

    
    
        #computer attack ship
        # airplanes attacking ships need to select a taskforce
        result_computer_ship_air_attack = None

        if enemy_taskforce_p:
            result_computer_ship_air_attack = perform_air_to_ship_combat(computer_bombers,enemy_taskforce_p.game_model)

        result_computer_base_air_attack = None
        if enemy_base_pieces:
            result_computer_base_air_attack = resolve_air_to_base_combat(computer_bombers, enemy_base_pieces[0].game_model, clouds=in_clouds, night=at_night)

        # First, remove aircraft with count 0 from all air formations in the hex
        for af_piece in hex_airformations + [p for p in hex_enemies if isinstance(p.game_model, AirFormation)]:
            af = af_piece.game_model
            af.aircraft = [ac for ac in af.aircraft if ac.count > 0]

        # Then, remove air formation pieces from the board if they have no aircraft left
        for af_piece in hex_airformations + [p for p in hex_enemies if isinstance(p.game_model, AirFormation)]:
            af = af_piece.game_model
            if not af.aircraft and af_piece in self.board.pieces:
                self.board.pieces.remove(af_piece)


        combat_results = {
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
        }

        return combat_results
    
    def _perform_combat_phase(self, pieces, observed_enemy_pieces):
        logger.info("Executing combat phase.")
        """
        For each piece that can attack, attempt to attack an observed enemy in the same hex.
        Only attack observed enemies.
        """
        #loop through all pieces that can attack
        combat_results = {}
        for piece in pieces:
            if not piece.can_attack:
               continue
            # Check if the piece is in a hex with observed enemy pieces
            combat_result_id = f"{piece.name}_{self.turn_manager.turn_number}"
            combat_results[combat_result_id] = self._perform_combat_phase_for_piece_in_hex(piece, observed_enemy_pieces)


        # TaskForce attacks (surface combat not implemented)
        # Could add surface combat logic here

        return combat_results

    def _select_best_ready_aircraft(self, ready_list, max_count, purpose='search'):
        sort_field = 'range'

        match purpose:
            case 'search':
                sort_field = 'range'
            case 'attack_ship':
                sort_field = 'torpedo_bombing_ship'
            case 'attack_base':
                sort_field = 'level_bombing_high_base_gp'

        sorted_ready = sorted(ready_list, key=lambda ac: (-getattr(ac, sort_field, 0), ac.count))
        selected = []
        total = 0
        for ac in sorted_ready:
            if total + ac.count > max_count:
                ac_copy = ac.copy()
                ac_copy.count = max_count - total
                ac.count -= ac_copy.count
                if ac.count <= 0:
                    ready_list.remove(ac)
                if ac_copy.count <= 0:
                    continue
                selected.append(ac_copy)
                break
            selected.append(ac)
            total += ac.count
            if total >= max_count:
                break
        return selected

    def _create_search_airformation_for_base(self, base : Base, base_piece: Piece):
        MAX_PER_BASE = 4
        board = self.board
        
        ready_aircraft = list(base.air_operations_tracker.ready)
        launch_factors_left = base.available_launch_factor_max - base.used_launch_factor
        created_airformation = []
        
        base_id = _get_base_id(base)
        if base_id not in self._search_airformation_counts:
            self._search_airformation_counts[base_id] = 0
        
        if self._search_airformation_counts[base_id] >= MAX_PER_BASE:
            return created_airformation

        if ready_aircraft and launch_factors_left > 0:
            for _ in range(random.randint(1, 2)):
                best = self._select_best_ready_aircraft(ready_aircraft, max_count=random.randint(1, 3))
                if not best:
                    break
                logger.debug(f"Selected best ready aircraft for search: {[ac.type for ac in best]}")
                for ac in best:
                    af:AirFormation = base.create_air_formation(random.randint(1, 35), aircraft=[ac])
                    created_airformation.append(af)
                    if af:
                        logger.debug(f"Creating search air formation {af.name} at base {base.name}.")  
                        af._is_search_formation = True
                        af._origin_base = base.name
                        af_piece = Piece(name=af.name, side=self.side, position=base_piece.position, gameModel=af)
                        board.add_piece(af_piece)
                        self._search_airformation_counts[base_id] += 1
                    else:
                        break
        elif base.used_ready_factor < base.available_ready_factor:
            # If no ready aircraft, but ready factors left, move aircraft from readying to ready, choose aircraft with best range
            readying_aircraft = list(base.air_operations_tracker.readying)
            if readying_aircraft:
                best = self._select_best_ready_aircraft(readying_aircraft, max_count=launch_factors_left)
                if best:
                    for ac in best:
                        logger.debug(f"Moving {ac.count} aircraft {ac.type} to ready at base {base.name}.")
                        to_aircraft : Aircraft = ac.copy()
                        best_armament = self._select_best_armament(ac)  # default to AP as assuming searching for enemy ships
                        to_aircraft.armament = best_armament
                        to_aircraft.count = min(ac.count, base.available_ready_factor - base.used_ready_factor)
                        base.air_operations_tracker.set_operations_status(to_aircraft, 'ready', ac)
                        if base.used_ready_factor >= base.available_ready_factor:
                            break
        return created_airformation      

    def _create_search_airformations(self, board):
        logger.debug("Creating search air formations with per-base cap.")
        """
        During Air Operations phase: create air formations for search from available bases/carriers, but do not move them yet.
        Each base can create no more than 4 search air formations. Track created search air formations in self._search_airformation_counts.
        """
        own_pieces = [p for p in board.pieces if p.side == self.side]
        bases = [p for p in own_pieces if isinstance(p.game_model, Base)]
        taskforces = [p for p in own_pieces if isinstance(p.game_model, TaskForce)]


        for base_piece in bases:
            base: Base = base_piece.game_model
            if not base:
                continue
            self._create_search_airformation_for_base(base, base_piece)

        for tf_piece in taskforces:
            tf: TaskForce = tf_piece.game_model
            for carrier in tf.get_carriers() if hasattr(tf, 'get_carriers') else []:
                base = getattr(carrier, 'base', None)
                if not base:
                    continue
                self._create_search_airformation_for_base(base, tf_piece)

    def _move_search_airformations(self, board):
        logger.debug("Moving search air formations.")
        """
        During Plane Movement phase: move air formations (with no observed enemy) in a search pattern (random within range).
        """
        own_pieces = [p for p in board.pieces if p.side == self.side]
        for piece in own_pieces:
            gm = getattr(piece, 'game_model', None)
            if isinstance(gm, AirFormation):
                max_move = gm.movement_factor
                possible_hexes = [tile for tile in board.tiles if tile != piece.position and get_distance(piece.position, tile) <= max_move]
                if possible_hexes:
                    dest = random.choice(possible_hexes)
                    logger.debug(f"Moving search air formation {piece.name} from {piece.position} to {dest}.")
                    self._move_toward(piece, dest)

    def perform_observation(self):
        """
        Perform observation for all pieces of this side.
        """
        return perform_observation_for_side(self.side, self.board, self.weather_manager, self.turn_manager)
    
    def start_new_turn(self):
        """
        At the start of a new turn its necessary to check how many search air formations exist for each base. 
        It is possible that some air formations have been destroyed or are no longer exist (ran out of fuel)

        """
        search_bases = [p.game_model for p in self.board.pieces if p.side == self.side and isinstance(p.game_model, Base)]
        for base in search_bases:
            base_id = _get_base_id(base)
            self._search_airformation_counts[base_id] = sum(
                1 for p in self.board.pieces if p.side == self.side 
                and isinstance(p.game_model, AirFormation) 
                and getattr(p.game_model, '_is_search_formation', False)
                and getattr(p.game_model, '_origin_base', None) == base.name
            )