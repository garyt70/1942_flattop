"""
Computer opponent engine for the Flattop game.
This module contains the logic for the computer opponent's actions and decisions during the game.
It is designed to simulate a human player's decisions based on the current game state.

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
- Improve enemy detection logic to avoid false negatives
- Optimize movement algorithms for better pathfinding
- Enhance combat resolution to account for more variables

- Logic for low range aircraft to return to base. This is not working correctly as it is in the condition when there are no observed enemy pieces.
- Air formations should not move into storm hexes
- Task forces should prioritize attacking enemy ships over land targets
- Combat should remove aircraft from air formation when they are destroyed (count==0)
- Combat must remove air formations from the board when they are destroyed (no aircraft left)
- Combat needs to remove sunk ships from the task force
- Combat must remove task forces from the board when they are destroyed (no ships left)

"""

import random
from flattop.hex_board_game_model import HexBoardModel, Piece, TurnManager, get_distance
from flattop.operations_chart_models import AirFormation, Aircraft, AircraftOperationsStatus, TaskForce, Base
from flattop.aircombat_engine import (
    classify_aircraft,
    resolve_air_to_air_combat,
    resolve_taskforce_anti_aircraft_combat,
    resolve_base_anti_aircraft_combat,
    resolve_air_to_ship_combat,
    resolve_air_to_base_combat
)
from flattop.game_engine import get_actionable_pieces, perform_observation_for_side
from flattop.weather_model import WeatherManager

class ComputerOpponent:
    def _move_toward(self, piece, target_hex, stop_distance=0):
        """
        Move the piece toward the target_hex, stopping at stop_distance if possible.
        Only move over sea hexes for air formations and task forces. Planes do not move into storm hexes.
        """
        from flattop.hex_board_game_model import get_distance
        current = piece.position
        max_move = getattr(piece, 'movement_factor', 1)
        # If already within stop_distance, do not move
        if get_distance(current, target_hex) <= stop_distance:
            return
        # Only allow sea hexes, and for planes, avoid storm hexes
        gm = getattr(piece, 'game_model', None)
        is_plane = isinstance(gm, AirFormation)
        candidates = []
        for tile in self.board.tiles:
            if get_distance(current, tile) > max_move:
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
            self.board.move_piece(piece, best_hex)

    def _move_random_within_range(self, piece, max_range=2):
        """
        Move the piece to a random valid hex within max_range, avoiding land for air formations and task forces. Planes do not move into storm hexes.
        """
        from flattop.hex_board_game_model import get_distance
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

    def _move_intelligent_search(self, piece, max_range=4):
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
                self.board.move_piece(piece, best_hex)
                moves_remaining -= dist_moved

                # Record searched hex
                if piece.name not in self._search_history:
                    self._search_history[piece.name] = set()
                self._search_history[piece.name].add(best_hex)

                # Perform observation after each move
                if hasattr(self, 'perform_observation'):
                    self.perform_observation()

                # Periodically change direction
                if random.random() < 0.2:  # 20% chance to change direction
                    current_idx = ['NE', 'E', 'SE', 'SW', 'W', 'NW'].index(direction)
                    new_idx = (current_idx + random.choice([-1, 0, 1])) % 6
                    self._search_direction[piece.name] = ['NE', 'E', 'SE', 'SW', 'W', 'NW'][new_idx]
            else:
                break
    # Implementation notes:
    # - Only observed enemy pieces (observed_condition > 0) are considered for movement/attack
    # - Air formations are created and launched if no enemies are observed, to simulate search/recon
    # - Movement is toward the nearest observed enemy, avoiding land for task forces
    # - Combat is resolved using the existing aircombat_engine functions
    # - Surface combat for task forces is not implemented, but can be added
    # - The AI does not currently coordinate multiple air formations or optimize search patterns
    # - This class is designed for turn-based invocation from the main game loop
    def __init__(self, side:str, board:HexBoardModel=None, weather_manager:WeatherManager=None, turn_manager:TurnManager=None):
        self.side = side  # 'Allied' or 'Japanese'
        self.board = board
        self.weather_manager = weather_manager
        self.turn_manager = turn_manager
    
    def perform_turn(self):
        """
        Perform all actions for the computer opponent for the current phase.
        Only move/attack observed enemy pieces. If no enemies are observed, create/search with air formations.
        Handles Air Operations phase: arms aircraft and creates air formations for CAP/interception or search.
        """
        phase = self.turn_manager.current_phase
        all_actionable = get_actionable_pieces(self.board, self.turn_manager)
        actionable = [p for p in all_actionable if p.side == self.side] # Filter actionable pieces for this side
        observed_enemy_pieces = [p for p in self.board.pieces if p.side != self.side and getattr(p, 'observed_condition', 0) > 0]
        if phase == "Air Operations":
            self._perform_air_operations_phase(self.board, observed_enemy_pieces)
        elif phase == "Plane Movement":
            self._perform_movement_phase(actionable, observed_enemy_pieces, move_type="plane")
        elif phase == "Task Force Movement":
            self._perform_movement_phase(actionable, observed_enemy_pieces, move_type="taskforce")
        elif phase == "Combat":
            result = self._perform_combat_phase(actionable, observed_enemy_pieces)
            if result and len(result) > 0:
                self.turn_manager.add_combat_result(result)
                print(f"Combat results: {result}")


    def _perform_air_operations_phase(self, board, observed_enemy_pieces):
        """
        AI logic for Air Operations phase:
        - If a TaskForce is observed, arm aircraft with AP (armor-piercing) if available in readying, and move to ready if ready factors allow.
        - If an enemy AirFormation is observed within 10 hexes of a base, create an interceptor air formation if possible.
        - If no observed enemies, create search air formations using best (longest range) ready aircraft, in small groups (1-3 aircraft), and only if ready/launch factors allow.
        """
        own_pieces = [p for p in board.pieces if p.side == self.side]
        bases = [p for p in own_pieces if isinstance(p.game_model, Base)]
        taskforces = [p for p in own_pieces if isinstance(p.game_model, TaskForce)]

        # 1. Arm aircraft with AP if TaskForce is observed
        taskforce_targets = [p for p in observed_enemy_pieces if isinstance(p.game_model, TaskForce)]
        if taskforce_targets:
            for base_piece in bases:
                base: Base = base_piece.game_model
                readying = base.air_operations_tracker.readying
                ready = base.air_operations_tracker.ready
                ready_factors_left = base.air_operations_config.ready_factors - base.used_ready_factor

            # Arm aircraft in readying with AP and move to ready if possible
            for ac in readying:
                if getattr(ac, 'armament', None) != 'AP' and ready_factors_left > 0:
                    ac.armament = 'AP'
                    base.air_operations_tracker.set_operations_status(ac, 'ready')
                    ready_factors_left -= ac.count

            # If there are ready aircraft, create an air formation to attack the taskforce
            if ready:
                # Select up to 3 ready aircraft for the attack formation
                attack_aircraft = ready[:3]
                af = base.create_air_formation(random.randint(1, 35), aircraft=attack_aircraft)
                if af:
                    af_piece = Piece(name=af.name, side=self.side, position=base_piece.position, gameModel=af)
                    board.add_piece(af_piece)

            for tf_piece in taskforces:
                tf = tf_piece.game_model
                for carrier in tf.get_carriers() if hasattr(tf, 'get_carriers') else []:
                    base = getattr(carrier, 'base', None)
                    if not base:
                        continue
                    readying = base.air_operations_tracker.readying
                    ready = base.air_operations_tracker.ready
                    ready_factors_left = base.air_operations_config.ready_factors - base.used_ready_factor

                    for ac in readying:
                        if getattr(ac, 'armament', None) != 'AP' and ready_factors_left > 0:
                            ac.armament = 'AP'
                            base.air_operations_tracker.set_operations_status(ac, 'ready')
                            ready_factors_left -= ac.count

                    if ready:
                        attack_aircraft = ready[:3]
                        af = base.create_air_formation(random.randint(1, 35), aircraft=attack_aircraft)
                        if af:
                            af_piece = Piece(name=af.name, side=self.side, position=tf_piece.position, gameModel=af)
                        board.add_piece(af_piece)
            
                    
        # 2. If enemy AirFormation observed within 10 hexes, create interceptor air formation if possible
        air_targets = [p for p in observed_enemy_pieces if isinstance(p.game_model, AirFormation)]
        for base_piece in bases:
            base = base_piece.game_model
            # Find enemy air formations within 10 hexes
            for air_target in air_targets:
                dist = get_distance(base_piece.position, air_target.position)
                if dist <= 10:
                    # Find ready aircraft that can serve as interceptors (no armament or fighter types)
                    interceptors = [ac for ac in base.air_operations_tracker.ready if getattr(ac, 'armament', None) is None or ac.type in ('Zero', 'Wildcat', 'P-38', 'P-39', 'P-40', 'Beaufighter')]
                    if interceptors:
                        # Move interceptors to new air formation (CAP)
                        af = base.create_air_formation(random.randint(1, 35), aircraft=interceptors)
                        if af:
                            af_piece = Piece(name=af.name, side=self.side, position=base_piece.position, gameModel=af)
                            board.add_piece(af_piece)
                        break
        for tf_piece in taskforces:
            tf = tf_piece.game_model
            for carrier in tf.get_carriers() if hasattr(tf, 'get_carriers') else []:
                base = getattr(carrier, 'base', None)
                if not base:
                    continue
                for air_target in air_targets:
                    dist = get_distance(tf_piece.position, air_target.position)
                    if dist <= 10:
                        interceptors = [ac for ac in base.air_operations_tracker.ready if getattr(ac, 'armament', None) is None or ac.type in ('Zero', 'Wildcat', 'P-38', 'P-39', 'P-40', 'Beaufighter')]
                        if interceptors:
                            af = base.create_air_formation(random.randint(1, 35), aircraft=interceptors)
                            if af:
                                af_piece = Piece(name=af.name, side=self.side, position=tf_piece.position, gameModel=af)
                                board.add_piece(af_piece)
                            break

        # 3. If no observed enemies, create search air formations (using best ready aircraft, 1-3 per formation, and only if ready/launch factors allow)
        if not observed_enemy_pieces:
            # Helper to select best ready aircraft (longest range)
            def select_best_ready_aircraft(ready_list, max_count):
                # Sort by range descending, then by count ascending (prefer small groups)
                sorted_ready = sorted(ready_list, key=lambda ac: (-getattr(ac, 'range', 0), ac.count))
                selected = []
                total = 0
                
                for ac in sorted_ready:
                    if total + ac.count > max_count:
                        # Split if too many
                        ac_copy = ac.copy()  # Create a copy to avoid modifying the original
                        ac_copy.count = max_count - total
                        #reduce the original count
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

            # For each base, try to create 1-2 search air formations (1-3 aircraft each, longest range)
            for base_piece in bases:
                base:Base = base_piece.game_model
                ready_aircraft = list(base.air_operations_tracker.ready)
                # Only create if launch factors allow
                launch_factors_left = base.air_operations_config.launch_factor_max - base.used_launch_factor
                if ready_aircraft and launch_factors_left > 0:
                    # Try to create up to 2 search formations
                    for _ in range(random.randint(1, 2)):
                        # Pick 1-3 best ready aircraft (longest range)
                        best = select_best_ready_aircraft(ready_aircraft, max_count=random.randint(1, 3))
                        if not best:
                            break
                        for ac in best:
                            af = base.create_air_formation(random.randint(1, 35), aircraft=[ac])
                            if af:
                                af_piece = Piece(name=af.name, side=self.side, position=base_piece.position, gameModel=af)
                                board.add_piece(af_piece)
                            else:
                                break

            # For each carrier, same logic as above
            for tf_piece in taskforces:
                tf = tf_piece.game_model
                for carrier in tf.get_carriers() if hasattr(tf, 'get_carriers') else []:
                    base = getattr(carrier, 'base', None)
                    if not base:
                        continue
                    ready_aircraft = list(base.air_operations_tracker.ready)
                    launch_factors_left = base.air_operations_config.launch_factors - base.used_launch_factor
                    if ready_aircraft and launch_factors_left > 0:
                        for _ in range(random.randint(1, 2)):
                            best = select_best_ready_aircraft(ready_aircraft, max_count=random.randint(1, 3))
                            if not best:
                                break
                            af = base.create_air_formation(random.randint(1, 35), aircraft=best)
                            if af:
                                af_piece = Piece(name=af.name, side=self.side, position=tf_piece.position, gameModel=af)
                                board.add_piece(af_piece)
                                for used in best:
                                    if used in ready_aircraft:
                                        ready_aircraft.remove(used)
                            else:
                                break

    def _perform_movement_phase(self, actionable, observed_enemy_pieces, move_type=None):
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
            from flattop.game_engine import get_actionable_pieces
            actionable = get_actionable_pieces(self.board, None)
        if not actionable:
            return
        # Only move pieces belonging to the computer side
        actionable = [p for p in actionable if p.side == self.side and p.can_move and not p.has_moved]
        # Determine which type of pieces to move this phase
        if move_type == "plane":
            actionable = [p for p in actionable if isinstance(getattr(p, 'game_model', None), AirFormation)]
        elif move_type == "taskforce":
            actionable = [p for p in actionable if isinstance(getattr(p, 'game_model', None), TaskForce)]
        if not actionable:
            return
        
        own_pieces = [p for p in self.board.pieces if p.side == self.side]
        bases = [p for p in own_pieces if isinstance(p.game_model, Base)]
        base_hexes = [b.position for b in bases]
        for piece in actionable:
            gm = getattr(piece, 'game_model', None)
            #handle running out of range
            # Range logic: if any aircraft in formation has just enough range to return to base, move toward nearest base
            if isinstance(gm, AirFormation):
                min_range_left = min((ac.range_remaining if hasattr(ac, 'range_remaining') else 0) for ac in gm.aircraft) if gm.aircraft else 0
                # Find nearest base
                nearest_base = None
                min_base_dist = float('inf')
                for base_hex in base_hexes:
                    dist = get_distance(piece.position, base_hex)
                    if dist < min_base_dist:
                        min_base_dist = dist
                        nearest_base = base_hex
                # If range is low (<= distance to base + 1), start moving back
                if nearest_base and min_range_left <= min_base_dist + 1:
                    # Move toward base in short hops (2-3 hexes)
                    hops = min(3, min_range_left, min_base_dist)
                    for _ in range(hops):
                        if get_distance(piece.position, nearest_base) > 0:
                            self._move_toward(piece, nearest_base, stop_distance=0)
                            # Optionally, call observation after each move
                            if hasattr(self, 'perform_observation'):
                                self.perform_observation()
                    # If air formation is at base, land it and remove from board
                    if piece.position == nearest_base:
                        # Land each aircraft in the air formation
                        for ac in gm.aircraft:
                            # Add aircraft back to base's tracker (simulate landing)
                            base_piece = next((b for b in bases if b.position == nearest_base), None)
                            if base_piece:
                                base:Base = base_piece.game_model
                                base.air_operations_tracker.set_operations_status(ac, AircraftOperationsStatus.JUST_LANDED)
                        # Remove air formation piece from board
                        if piece in self.board.pieces:
                            self.board.pieces.remove(piece)
                    continue


            if not observed_enemy_pieces or len(observed_enemy_pieces) == 0:
                # No observed enemies: move in a search pattern

                
                if isinstance(gm, AirFormation):
                    # Classify aircraft: if all are bombers, treat as bomber; else, treat as fighter/interceptor
                    is_bomber = any(ac.is_bomber for ac in gm.aircraft)

                    if not is_bomber:
                        # Fighters/interceptors: move close to nearest base (within 2-3 hexes)
                        if base_hexes:
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
                                hops = min(3, min_dist)
                                for _ in range(hops):
                                    if get_distance(piece.position, nearest_base) > 1:
                                        self._move_toward(piece, nearest_base, stop_distance=1)
                                        if hasattr(self, 'perform_observation'):
                                            self.perform_observation()
                            else:
                                # Already close, loiter or move randomly within 2 hexes
                                self._move_random_within_range(piece, max_range=1)
                        else:
                            # No base found, move randomly within 2 hexes
                            self._move_random_within_range(piece, max_range=2)
                    else:
                        # Bombers: search more widely (random within movement range)
                        move_range = getattr(gm, 'movement_factor', 4)
                        self._move_intelligent_search(piece, max_range=move_range)
                elif isinstance(gm, TaskForce):
                    # Task forces: do not move if no observed enemies (could add patrol logic here)
                    continue
            else:
                # Move each actionable piece toward the nearest observed enemy
                #Rules for moving toward enemy:
                # - If the enemy is an airformation then keep own interceptor formations a the nearest friendly base , This is the CAP for the base.
                # - If the enemy is a TaskForce, move toward it so that the computer opponent can attack it with its air formations.
                # - If the enemy is a Base, move toward it to attack with air formations.
                # - Computer opponent airformations with bombers should continue to follow the enemy TaskForce or Base, but not move into storm hexes.
                # - Air formations make multiple short moves (2-3 hexes) toward their destination
                # Gather friendly task force positions for stacking avoidance
                friendly_taskforce_hexes = [p.position for p in self.board.pieces if p.side == self.side and isinstance(getattr(p, 'game_model', None), TaskForce)]
                # Gather friendly bases for CAP prioritization
                own_pieces = [p for p in self.board.pieces if p.side == self.side]
                bases = [p for p in own_pieces if isinstance(p.game_model, Base)]
                base_hexes = [b.position for b in bases]
                # Gather all actionable bombers for coordination
                actionable_bombers = [p for p in actionable if isinstance(getattr(p, 'game_model', None), AirFormation) and all(ac.armament is not None for ac in p.game_model.aircraft)]
                # Track which bombers have already moved for coordination
                bombers_moved = set()
                for piece in actionable:
                    if not hasattr(piece, 'can_move') or not piece.can_move:
                        continue
                    gm = getattr(piece, 'game_model', None)
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
                        is_interceptor = False
                        if isinstance(gm, AirFormation):
                            is_interceptor = any(ac.type.value in ('Zero', 'Wildcat', 'P-38', 'P-39', 'P-40', 'Beaufighter') and  ac.armament is not None for ac in gm.aircraft)
                        if target_type == AirFormation and is_interceptor:
                            # Prioritize high-value base/carrier for CAP
                            high_value_bases = [b for b in bases if getattr(b.game_model, 'is_high_value', False)]
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
                        is_bomber = all(getattr(ac, 'is_bomber', False) for ac in gm.aircraft) if isinstance(gm, AirFormation) and gm.aircraft else False
                        if target_type in (TaskForce, Base) and is_bomber:
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
                        # Task forces: avoid moving into hexes with enemy air formations unless protected by CAP
                        if isinstance(gm, TaskForce):
                            enemy_air_hexes = [e.position for e in observed_enemy_pieces if isinstance(e.game_model, AirFormation)]
                            cap_present = any(
                                isinstance(p.game_model, AirFormation) and any(ac.type in ('Zero', 'Wildcat', 'P-38', 'P-39', 'P-40', 'Beaufighter') for ac in p.game_model.aircraft)
                                and get_distance(p.position, piece.position) <= 2
                                for p in self.board.pieces if p.side == self.side
                            )
                            for hex in enemy_air_hexes:
                                if get_distance(piece.position, hex) <= 1 and not cap_present:
                                    # Retreat or hold position
                                    continue
        # Additional rules to consider:
        # - Air formations should avoid moving into hexes with friendly task forces to prevent stacking.
        # - Bombers should coordinate attacks if multiple formations are available (strike together).
        # - Interceptors could prioritize defending high-value bases/carriers.
        # - Task forces should avoid moving into hexes with enemy air formations unless protected by CAP.
        # - Air formations should avoid moving into hexes with poor weather (clouds) unless necessary for attack.
        # - Implement fuel/range tracking for each aircraft and force landing if range is too low.
        # - Add logic for retreating if odds are unfavorable (e.g., outnumbered/intercepted).

    def _perform_combat_phase_for_piece_in_hex(self, piece, observed_enemy_pieces):
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
        # Group by side
        sides = set(p.side for p in hex_airformations)

        player_aircraft_pieces = [p.game_model for p in hex_airformations if p.side == piece.side]
        enemy_aircraft_pieces = [p.game_model for p in hex_enemies if isinstance(p.game_model, AirFormation) and p.position == piece.position]

        # Gather aircraft by role (interceptor, escort, bomber)
        player_interceptors, player_escorts, player_bombers = classify_aircraft(player_aircraft_pieces)
        enemy_interceptors, enemy_escorts, enemy_bombers = classify_aircraft(enemy_aircraft_pieces)

        pre_combat_count_player_interceptors = sum(ic.count for ic in player_interceptors)
        pre_combat_count_player_bombers = sum(b.count for b in player_bombers)
        pre_combat_count_player_escorts = sum(ec.count for ec in player_escorts)

        pre_combat_count_enemy_interceptors = sum(ic.count for ic in enemy_interceptors)
        pre_combat_count_enemy_bombers = sum(b.count for b in enemy_bombers)
        pre_combat_count_enemy_escorts = sum(ec.count for ec in enemy_escorts)

        player_taskforce_pieces = [p for p in self.board.pieces if isinstance(p.game_model, TaskForce) and p.side == piece.side and p.position == piece.position]
        enemy_taskforce_pieces = [p for p in self.board.pieces if isinstance(p.game_model, TaskForce) and p.side != piece.side and p.position == piece.position]

        player_taskforce_p:TaskForce = None
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

        if len(player_taskforce_pieces) > 0:
            player_taskforce_pieces = sorted(
            player_taskforce_pieces,
            key=lambda p: (
                len(p.game_model.get_carriers() if hasattr(p.game_model, 'get_carriers') else []),
                get_high_value_ship_count(p.game_model)
            ),
            reverse=True
            )
            player_taskforce_p = player_taskforce_pieces[:1][0]

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

        result_player_a2a = None
        result_enemy_a2a = None

        in_clouds = self.weather_manager.is_cloud_hex(piece.position)
        at_night = self.turn_manager.is_night()

        # For simplicity, assume two sides: Allied and Japanese
        #and there are two airformations

        # if no bombers on either side then convert interceptors to escorts 
        if not player_bombers and not enemy_bombers:
            # Convert interceptors to escorts for one side so that we have interceptor to interceptor combat
            enemy_escorts.extend(enemy_interceptors)
            enemy_interceptors = []

        result_player_a2a = resolve_air_to_air_combat(
            interceptors=player_interceptors,
            escorts=enemy_escorts,
            bombers=enemy_bombers,
            rf_expended=True,
            clouds=in_clouds,
            night=at_night
        )

        if not player_bombers and not enemy_bombers:
            # Convert interceptors to escorts for one side so that we have interceptor to interceptor combat
            player_escorts.extend(player_interceptors)
            player_interceptors = []

        result_enemy_a2a = resolve_air_to_air_combat(
            interceptors=enemy_interceptors,
            escorts=player_escorts,
            bombers=player_bombers,
            rf_expended=True,
            clouds=in_clouds,
            night=at_night
        )

        # need to update the air operations chart for each side
        # remove aircraft from air formations that have 0 or less count
        # removed airformations that have no aircraft left
        for af in player_aircraft_pieces:
            af.aircraft = [ac for ac in af.aircraft if ac.count > 0]
            if not af.aircraft:
                self.board.pieces.remove([p for p in hex_airformations if p.game_model == af][0])
        for af in enemy_aircraft_pieces:
            af.aircraft = [ac for ac in af.aircraft if ac.count > 0]
            if not af.aircraft:
                self.board.pieces.remove([p for p in hex_airformations if p.game_model == af][0])

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
        result_player_anti_aircraft = None
        result_enemy_anti_aircraft = None
        if player_taskforce_p:
            result_player_anti_aircraft = perform_taskforce_anti_aircraft_combat(enemy_bombers, player_taskforce_p.game_model, piece.position)
        if enemy_taskforce_p:
            result_enemy_anti_aircraft = perform_taskforce_anti_aircraft_combat(player_bombers, enemy_taskforce_p.game_model, piece.position)

        player_base_pieces = [p for p in self.board.pieces if isinstance(p.game_model, Base) and p.side == piece.side and p.position == piece.position]
        enemy_base_pieces = [p for p in self.board.pieces if isinstance(p.game_model, Base) and p.side != piece.side and p.position == piece.position]
        #assume there is only ever one base.  Also re-using the anti-aircraft results as assuming TF and Base won't be in same hex.
        if player_base_pieces:
            result_player_anti_aircraft = perform_base_anti_aircraft_combat(enemy_bombers,player_base_pieces[0].game_model)
        #assume there is only ever one base
        if enemy_base_pieces:
            result_enemy_anti_aircraft = perform_base_anti_aircraft_combat(player_bombers,enemy_base_pieces[0].game_model)

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

    
    
        #player attack ship
        # airplanes attacking ships need to select a taskforce
        result_player_ship_air_attack = None

        if enemy_taskforce_p:
            result_player_ship_air_attack = perform_air_to_ship_combat(player_bombers,enemy_taskforce_p.game_model)
        #enemy attack ship
        result_enemy_ship_air_attack = None
        if player_taskforce_p:
            result_enemy_ship_air_attack = perform_air_to_ship_combat(enemy_bombers,player_taskforce_p.game_model)


        result_player_base_air_attack = None
        if enemy_base_pieces:
            result_player_base_air_attack = resolve_air_to_base_combat(player_bombers, enemy_base_pieces[0].game_model, clouds=in_clouds, night=at_night)

        result_enemy_base_air_attack = None
        if player_base_pieces:
            result_enemy_base_air_attack = resolve_air_to_base_combat(enemy_bombers, player_base_pieces[0].game_model, clouds=in_clouds, night=at_night)


        combat_results = {
            "result_player_a2a": result_player_a2a,
            "result_enemy_a2a": result_enemy_a2a,
            "result_player_anti_aircraft": result_player_anti_aircraft,
            "result_enemy_anti_aircraft": result_enemy_anti_aircraft,
            "result_player_ship_air_attack": result_player_ship_air_attack,
            "result_enemy_ship_air_attack": result_enemy_ship_air_attack,
            "result_player_base_air_attack": result_player_base_air_attack,
            "result_enemy_base_air_attack": result_enemy_base_air_attack,
            "pre_combat_count_player_interceptors": pre_combat_count_player_interceptors,
            "pre_combat_count_player_bombers": pre_combat_count_player_bombers,
            "pre_combat_count_player_escorts": pre_combat_count_player_escorts,
            "pre_combat_count_enemy_interceptors": pre_combat_count_enemy_interceptors,
            "pre_combat_count_enemy_bombers": pre_combat_count_enemy_bombers,
            "pre_combat_count_enemy_escorts": pre_combat_count_enemy_escorts
        }

        return combat_results
    
    def _perform_combat_phase(self, pieces, observed_enemy_pieces):
        """
        For each piece that can attack, attempt to attack an observed enemy in the same hex.
        Only attack observed enemies.
        """
        #loop through all pieces that can attack
        #combat_results = {}
        #for piece in pieces:
        #    if not piece.can_attack:
        #       continue
        #    # Check if the piece is in a hex with observed enemy pieces
        #    combat_results[piece.name] = self._perform_combat_phase_for_piece_in_hex(piece, observed_enemy_pieces)
        combat_results = None
        if len(pieces)>0:
            #only need the first piece as the combat finds all combat pieces that can be actioned    
            combat_results = self._perform_combat_phase_for_piece_in_hex(pieces[0], observed_enemy_pieces)
            
        # TaskForce attacks (surface combat not implemented)
        # Could add surface combat logic here

        return combat_results


            

    def _create_search_airformations(self, board):
        """
        During Air Operations phase: create air formations for search from available bases/carriers, but do not move them yet.
        """
        own_pieces = [p for p in board.pieces if p.side == self.side]
        bases = [p for p in own_pieces if isinstance(p.game_model, Base)]
        taskforces = [p for p in own_pieces if isinstance(p.game_model, TaskForce)]
        for base_piece in bases:
            base = base_piece.game_model
            if hasattr(base, 'create_air_formation') and base.air_operations_tracker.ready:
                af = base.create_air_formation(random.randint(1, 35))
                if af:
                    af_piece = Piece(name=af.name, side=self.side, position=base_piece.position, gameModel=af)
                    board.add_piece(af_piece)
        for tf_piece in taskforces:
            tf = tf_piece.game_model
            carriers = tf.get_carriers() if hasattr(tf, 'get_carriers') else []
            for carrier in carriers:
                base = getattr(carrier, 'base', None)
                if base and hasattr(base, 'create_air_formation') and base.air_operations_tracker.ready:
                    af = base.create_air_formation(random.randint(1, 35))
                    if af:
                        af_piece = Piece(name=af.name, side=self.side, position=tf_piece.position, gameModel=af)
                        board.add_piece(af_piece)

    def _move_search_airformations(self, board):
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
                    board.move_piece(piece, dest)

    def perform_observation(self):
        """
        Perform observation for all pieces of this side.
        """
        return perform_observation_for_side(self.side, self.board, self.weather_manager, self.turn_manager)