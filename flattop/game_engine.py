"""
Game engine logic for Flattop. This module contains all non-UI game logic and actions, so it can be used by both human and computer players.
"""
from flattop.hex_board_game_model import Piece, get_distance
from flattop.operations_chart_models import AirFormation, TaskForce, Base, Carrier, AircraftOperationsStatus
from flattop.weather_model import WeatherManager, CloudMarker
from flattop.observation_rules import attempt_observation, TURN_DAY, TURN_NIGHT, set_game_model_observed


def perform_observation_for_piece(piece: Piece, board, weather_manager, turn_manager):
    """
    Perform observation for a single piece (can be used by AI or UI).
    Returns a list of observed targets.
    """
    turn_type = TURN_NIGHT if turn_manager.is_night() else TURN_DAY
    observed_targets = []
    for target in board.pieces:
        if target.side != piece.side and not isinstance(target, CloudMarker):
            target_location = target.position
            distance = get_distance(piece.position, target.position)
            result = attempt_observation(
                piece.game_model, target.game_model, weather_manager,
                target_location, distance, turn_type
            )
            if result:
                set_game_model_observed(target.game_model, True)
                observed_targets.append(target)
            else:
                set_game_model_observed(target.game_model, False)
    return observed_targets


def perform_observation_for_side(side: str, board, weather_manager, turn_manager):
    """
    Perform observation for all pieces of a given side.
    Returns a dict mapping observer piece to list of observed targets.
    """
    observed = {}
    for piece in board.pieces:
        if piece.side == side and hasattr(piece, 'can_observe') and piece.can_observe:
            observed[piece] = perform_observation_for_piece(piece, board, weather_manager, turn_manager)
    return observed


def perform_observation_phase(board, weather_manager, turn_manager):
    """
    Perform the observation phase for both sides.
    Returns a dict with keys 'Allied' and 'Japanese', each mapping to observer->targets.
    """
    return {
        'Allied': perform_observation_for_side('Allied', board, weather_manager, turn_manager),
        'Japanese': perform_observation_for_side('Japanese', board, weather_manager, turn_manager)
    }


def get_actionable_pieces(board, turn_manager):
    """
    Move phase = get all pieces that can move but have not moved yet.
    Combat phase = get all pieces that can attack but have not attacked yet.
    Air Operations phase = get all bases that have available Launch or Ready Factor count.
    Returns a list of pieces that can perform actions in the current phase.
    """
    all_pieces:list[Piece] = board.pieces
    action_available_pieces = []
    if turn_manager.current_phase == "Plane Movement":
        action_available_pieces = [p for p in all_pieces if p.can_move and not p.has_moved and isinstance(p.game_model, AirFormation)]
    elif turn_manager.current_phase == "Task Force Movement":
        action_available_pieces = [p for p in all_pieces if p.can_move and not p.has_moved and isinstance(p.game_model, TaskForce)]
    elif turn_manager.current_phase == "Combat":
        action_available_pieces = [p for p in all_pieces if p.can_attack]
    elif turn_manager.current_phase == "Air Operations":
        
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


# Additional game logic (AI, combat, movement validation, etc.) can be added here.
