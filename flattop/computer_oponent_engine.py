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
from flattop.hex_board_game_model import Piece, get_distance
from flattop.operations_chart_models import AirFormation, TaskForce, Base
from flattop.aircombat_engine import (
    resolve_air_to_air_combat,
    resolve_taskforce_anti_aircraft_combat,
    resolve_base_anti_aircraft_combat,
    resolve_air_to_ship_combat,
    resolve_air_to_base_combat
)
from flattop.game_engine import get_actionable_pieces, perform_observation_for_side

class ComputerOpponent:
    # Implementation notes:
    # - Only observed enemy pieces (observed_condition > 0) are considered for movement/attack
    # - Air formations are created and launched if no enemies are observed, to simulate search/recon
    # - Movement is toward the nearest observed enemy, avoiding land for task forces
    # - Combat is resolved using the existing aircombat_engine functions
    # - Surface combat for task forces is not implemented, but can be added
    # - The AI does not currently coordinate multiple air formations or optimize search patterns
    # - This class is designed for turn-based invocation from the main game loop
    def __init__(self, side:str):
        self.side = side  # 'Allied' or 'Japanese'

    def perform_turn(self, board, weather_manager, turn_manager):
        """
        Perform all actions for the computer opponent for the current phase.
        Only move/attack observed enemy pieces. If no enemies are observed, create/search with air formations.
        """
        phase = turn_manager.current_phase
        actionable = get_actionable_pieces(board, turn_manager)
        observed_enemy_pieces = [p for p in board.pieces if p.side != self.side and getattr(p, 'observed_condition', 0) > 0]
        if not observed_enemy_pieces and phase == "Plane Movement":
            self._create_and_search_with_airformations(board, weather_manager, turn_manager)
        elif phase in ("Plane Movement", "Task Force Movement"):
            self._perform_movement_phase(actionable, board, observed_enemy_pieces)
        elif phase == "Combat":
            self._perform_combat_phase(actionable, board, weather_manager, turn_manager, observed_enemy_pieces)
        # Air Operations phase can be added as needed

    def _perform_movement_phase(self, pieces, board, observed_enemy_pieces):
        """
        Move each piece towards the nearest observed enemy piece, avoiding land for TFs.
        """
        for piece in pieces:
            if piece.side != self.side or not piece.can_move or piece.has_moved:
                continue
            if not observed_enemy_pieces:
                continue
            # Find nearest observed enemy
            nearest_enemy = min(observed_enemy_pieces, key=lambda p: get_distance(piece.position, p.position))
            min_dist = get_distance(piece.position, nearest_enemy.position)
            # Get all possible hexes within movement range
            possible_hexes = [tile for tile in board.tiles
                              if get_distance(piece.position, tile) <= piece.movement_factor]
            # For TaskForces, avoid land
            if isinstance(piece.game_model, TaskForce):
                possible_hexes = [h for h in possible_hexes if board.get_terrain(h) != "land"]
            # Exclude current position
            possible_hexes = [h for h in possible_hexes if h != piece.position]
            # Move to hex that minimizes distance to nearest enemy
            if possible_hexes:
                dest = min(possible_hexes, key=lambda h: get_distance(h, nearest_enemy.position))
                board.move_piece(piece, dest)

    def _perform_combat_phase(self, pieces, board, weather_manager, turn_manager, observed_enemy_pieces):
        """
        For each piece that can attack, attempt to attack an observed enemy in the same hex.
        Only attack observed enemies.
        """
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
                        clouds=(weather_manager.get_weather_at_hex(piece.position) == "cloud"),
                        night=turn_manager.is_night()
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

    def _create_and_search_with_airformations(self, board, weather_manager, turn_manager):
        """
        If no enemies are observed, create air formations from available bases/carriers and send them to search random locations.
        """
        # Find all bases and carriers for this side
        own_pieces = [p for p in board.pieces if p.side == self.side]
        bases = [p for p in own_pieces if isinstance(p.game_model, Base)]
        taskforces = [p for p in own_pieces if isinstance(p.game_model, TaskForce)]
        # Try to create/search with air formations from bases
        for base_piece in bases:
            base = base_piece.game_model
            # Try to create an air formation if there are ready aircraft
            if hasattr(base, 'create_air_formation') and base.air_operations_tracker.ready:
                af = base.create_air_formation(random.randint(1, 35))
                # Place the new air formation piece on the board at the base's location
                af_piece = Piece(name=af.name, side=self.side, position=base_piece.position, gameModel=af)
                board.add_piece(af_piece)
                # Move the air formation to a random tile to search
                possible_hexes = [tile for tile in board.tiles if tile != base_piece.position]
                if possible_hexes:
                    dest = random.choice(possible_hexes)
                    board.move_piece(af_piece, dest)
        # Try to create/search with air formations from carriers in taskforces
        for tf_piece in taskforces:
            tf = tf_piece.game_model
            carriers = tf.get_carriers() if hasattr(tf, 'get_carriers') else []
            for carrier in carriers:
                base = getattr(carrier, 'base', None)
                if base and hasattr(base, 'create_air_formation') and base.air_operations_tracker.ready:
                    af = base.create_air_formation(random.randint(1, 35))
                    af_piece = Piece(name=af.name, side=self.side, position=tf_piece.position, gameModel=af)
                    board.add_piece(af_piece)
                    possible_hexes = [tile for tile in board.tiles if tile != tf_piece.position]
                    if possible_hexes:
                        dest = random.choice(possible_hexes)
                        board.move_piece(af_piece, dest)

    def perform_observation(self, board, weather_manager, turn_manager):
        """
        Perform observation for all pieces of this side.
        """
        return perform_observation_for_side(self.side, board, weather_manager, turn_manager)