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

import random
from flattop.hex_board_game_model import HexBoardModel, Piece, TurnManager, get_distance
from flattop.operations_chart_models import AirFormation, TaskForce, Base
from flattop.aircombat_engine import (
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
        actionable = get_actionable_pieces(self.board, self.turn_manager)
        observed_enemy_pieces = [p for p in self.board.pieces if p.side != self.side and getattr(p, 'observed_condition', 0) > 0]
        if phase == "Air Operations":
            self._perform_air_operations_phase(self.board, observed_enemy_pieces)
        elif not observed_enemy_pieces and phase == "Plane Movement":
            self._move_search_airformations(self.board)
        elif phase == "Plane Movement":
            self._perform_movement_phase(actionable, observed_enemy_pieces, move_type="plane")
        elif phase == "Task Force Movement":
            self._perform_movement_phase(actionable, observed_enemy_pieces, move_type="taskforce")
        elif phase == "Combat":
            self._perform_combat_phase(actionable, observed_enemy_pieces)


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
                base = base_piece.game_model
                readying = base.air_operations_tracker.readying
                ready_factors_left = base.air_operations_config.ready_factors - base.used_ready_factor
                
                for ac in readying:
                    # Only arm if not already armed with AP
                    if getattr(ac, 'armament', None) != 'AP' and ready_factors_left > 0:
                        ac.armament = 'AP'
                        base.air_operations_tracker.set_operations_status(ac, 'ready')
                        ready_factors_left -= ac.count
                    

            for tf_piece in taskforces:
                tf = tf_piece.game_model
                for carrier in tf.get_carriers() if hasattr(tf, 'get_carriers') else []:
                    base = getattr(carrier, 'base', None)
                    if not base:
                        continue
                    readying = base.air_operations_tracker.readying
                    ready_factors_left = base.air_operations_config.ready_factors - base.used_ready_factor
                    for ac in readying:
                        if getattr(ac, 'armament', None) != 'AP' and ready_factors_left > 0:
                            ac.armament = 'AP'
                            base.air_operations_tracker.set_operations_status(ac, 'ready')
                            ready_factors_left -= ac.count
                    
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
        actionable = [p for p in actionable if p.side == self.side]
        # Determine which type of pieces to move this phase
        if move_type == "plane":
            actionable = [p for p in actionable if isinstance(getattr(p, 'game_model', None), AirFormation)]
        elif move_type == "taskforce":
            actionable = [p for p in actionable if isinstance(getattr(p, 'game_model', None), TaskForce)]
        if not actionable:
            return
        if not observed_enemy_pieces:
            # No observed enemies: move in a search pattern
            own_pieces = [p for p in self.board.pieces if p.side == self.side]
            bases = [p for p in own_pieces if isinstance(p.game_model, Base)]
            base_hexes = [b.position for b in bases]
            for piece in actionable:
                if not hasattr(piece, 'can_move') or not piece.can_move:
                    continue
                gm = getattr(piece, 'game_model', None)
                if isinstance(gm, AirFormation):
                    # Classify aircraft: if all are bombers, treat as bomber; else, treat as fighter/interceptor
                    aircraft_types = [ac.type for ac in gm.aircraft]
                    is_bomber = all(getattr(ac, 'is_bomber', False) for ac in gm.aircraft) if gm.aircraft else False
                    # Range logic: if any aircraft in formation has just enough range to return to base, move toward nearest base
                    min_range_left = min([getattr(ac, 'range_left', getattr(ac, 'range', 0)) for ac in gm.aircraft]) if gm.aircraft else 0
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
                                    base.air_operations_tracker.set_operations_status(ac, 'just_landed')
                            # Remove air formation piece from board
                            if piece in self.board.pieces:
                                self.board.pieces.remove(piece)
                        continue
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
                        move_range = getattr(gm, 'move_factor', 4)
                        self._move_random_within_range( piece, max_range=move_range)
                elif isinstance(gm, TaskForce):
                    # Task forces: do not move if no observed enemies (could add patrol logic here)
                    continue
            return
        # Move each actionable piece toward the nearest observed enemy
        for piece in actionable:
            if not hasattr(piece, 'can_move') or not piece.can_move:
                continue
            gm = getattr(piece, 'game_model', None)
            min_dist = float('inf')
            target = None
            for enemy in observed_enemy_pieces:
                dist = get_distance(piece.position, enemy.position)
                if dist < min_dist:
                    min_dist = dist
                    target = enemy
            if target:
                # Make multiple short moves (2-3 hexes) toward target
                hops = min(3, min_dist)
                for _ in range(hops):
                    if get_distance(piece.position, target.position) > 0:
                        self._move_toward( piece, target.position)
                        if hasattr(self, 'perform_observation'):
                            self.perform_observation()

    def _perform_combat_phase(self, pieces, observed_enemy_pieces):
        """
        For each piece that can attack, attempt to attack an observed enemy in the same hex.
        Only attack observed enemies.
        """
        # If pieces is None, recompute actionable pieces
        if pieces is None:
            from flattop.game_engine import get_actionable_pieces
            pieces = get_actionable_pieces(self.board, self.turn_manager)
        for piece in pieces:
            if piece.side != self.side or not piece.can_attack:
                continue
            # Find observed enemy pieces in the same hex
            enemies = [p for p in observed_enemy_pieces if p.position == piece.position]
            if not enemies:
                continue
            # AirFormation attacks
            if isinstance(piece.game_model, AirFormation):
                # Air-to-air combat: find enemy air formations
                enemy_air = [p.game_model for p in enemies if isinstance(p.game_model, AirFormation)]
                if enemy_air:
                    # Simple: all vs all
                    resolve_air_to_air_combat(
                        interceptors=[ac for af in [piece.game_model] for ac in af.aircraft if ac.armament is None],
                        escorts=[],
                        bombers=[ac for af in enemy_air for ac in af.aircraft if ac.armament is not None],
                        rf_expended=True,
                        clouds=(self.weather_manager.get_weather_at_hex(piece.position) == "cloud"),
                        night=self.turn_manager.is_night()
                    )
                # Attack TaskForce or Base if present
                enemy_tf = [p.game_model for p in enemies if isinstance(p.game_model, TaskForce)]
                enemy_base = [p.game_model for p in enemies if isinstance(p.game_model, Base)]
                if enemy_tf:
                    # Attack first enemy TF
                    resolve_taskforce_anti_aircraft_combat(piece.game_model.aircraft, enemy_tf[0])
                    resolve_air_to_ship_combat(piece.game_model.aircraft, random.choice(enemy_tf[0].ships))
                elif enemy_base:
                    resolve_base_anti_aircraft_combat(piece.game_model.aircraft, enemy_base[0])
                    resolve_air_to_base_combat(piece.game_model.aircraft, enemy_base[0])
            # TaskForce attacks (surface combat not implemented)
            # Could add surface combat logic here

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