import os
import json
import datetime
from flattop.operations_chart_models import AirFormation,  Aircraft, Base, TaskForce, Carrier

def save_game_state(board, turn_manager, weather_manager=None, filename_prefix="save"):
    """
    Save the full game state (board, pieces, turn manager, weather, air operations, etc.) to a JSON file in ~/flattop_1942/.
    """
    import os, json, datetime
    home_dir = os.path.expanduser("~")
    save_dir = os.path.join(home_dir, "flattop_1942")
    os.makedirs(save_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.json"
    save_path = os.path.join(save_dir, filename)

    def serialize_air_operations_config(cfg):
        if cfg is None:
            return None
        return {
            "name": cfg.name,
            "description": cfg.description,
            "maximum_capacity": cfg.maximum_capacity,
            "launch_factor_min": cfg.launch_factor_min,
            "launch_factor_normal": cfg.launch_factor_normal,
            "launch_factor_max": cfg.launch_factor_max,
            "ready_factors": cfg.ready_factors,
            "plane_handling_type": cfg.plane_handling_type,
            "aaf": getattr(cfg, "aaf", 0)
        }

    def serialize_air_operations_tracker(tracker):
        if tracker is None:
            return None
        def ac_list(lst):
            return [
                {
                    "type": str(ac.type),
                    "count": ac.count,
                    "move_factor": ac.move_factor,
                    "range_factor": ac.range_factor,
                    "range_remaining": ac.range_remaining,
                    "armament": ac.armament,
                    "height": ac.height,
                    "attack_type": ac.attack_type
                } for ac in lst
            ]
        return {
            "name": tracker.name,
            "description": tracker.description,
            "in_flight": ac_list(tracker.in_flight),
            "just_landed": ac_list(tracker.just_landed),
            "readying": ac_list(tracker.readying),
            "ready": ac_list(tracker.ready),
            "used_ready_factor": tracker.used_ready_factor,
            "used_launch_factor": tracker.used_launch_factor,
            "air_op_config": serialize_air_operations_config(tracker.air_op_config)
        }
    
    def serialize_game_model(gm):
        if gm is None:
            return None
        if isinstance(gm, AirFormation):
            return {
                "type": "AirFormation",
                "number": getattr(gm, "number", None),
                "name": getattr(gm, "name", None),
                "side": getattr(gm, "side", None),
                "launch_hour": getattr(gm, "launch_hour", None),
                "height": getattr(gm, "height", None),
                "aircraft": [
                    {
                        "type": str(ac.type),
                        "count": ac.count,
                        "move_factor": ac.move_factor,
                        "range_factor": ac.range_factor,
                        "range_remaining": ac.range_remaining,
                        "armament": ac.armament,
                        "height": ac.height,
                        "attack_type": ac.attack_type
                    } for ac in gm.aircraft
                ],
                "observed_condition": getattr(gm, "observed_condition", 0)
            }
        elif isinstance(gm, TaskForce):
            return {
                "type": "TaskForce",
                "number": getattr(gm, "number", None),
                "name": getattr(gm, "name", None),
                "side": getattr(gm, "side", None),
                "ships": [
                    {
                        "name": s.name,
                        "type": s.type,
                        "status": s.status,
                        "attack_factor": s.attack_factor,
                        "anti_air_factor": s.anti_air_factor,
                        "move_factor": s.move_factor,
                        "damage_factor": s.damage_factor,
                        "damage": s.damage
                    } for s in gm.ships
                ],
                "observed_condition": getattr(gm, "observed_condition", 0)
            }
        elif isinstance(gm, Base):
            return {
                "type": "Base",
                "name": getattr(gm, "name", None),
                "side": getattr(gm, "side", None),
                "damage": getattr(gm, "damage", 0),
                "observed_condition": getattr(gm, "observed_condition", 0),
                "air_operations_config": serialize_air_operations_config(getattr(gm, "air_operations_config", None)),
                "air_operations_tracker": serialize_air_operations_tracker(getattr(gm, "air_operations_tracker", None))
            }
        return None

    def serialize_piece(piece):
        d = {
            "name": piece.name,
            "side": piece.side,
            "position": {"q": piece.position.q, "r": piece.position.r, "terrain": getattr(piece.position, "terrain", None)},
            "has_moved": piece.has_moved,
            "phase_move_count": piece.phase_move_count,
        }
        gm = piece.game_model
        if gm is not None:
             d["game_model"] = serialize_game_model(gm)
        return d

    def serialize_air_operations_chart(chart):
        if chart is None:
            return None
        return {
            "name": chart.name,
            "description": chart.description,
            "side": chart.side,
            "air_formations": {
                str(num): serialize_game_model(af) if af else None for num, af in chart.air_formations.items()
            },
            "task_forces": {
                str(num): serialize_game_model(tf) if tf else None for num, tf in chart.task_forces.items()
            },
            "bases": {name: serialize_game_model(base) for name, base in chart.bases.items()}
        }

    def serialize_weather(weather_manager):
        if weather_manager is None:
            return None
        weather_pieces = getattr(weather_manager, "get_weather_pieces", lambda: [])()
        result = []
        for piece in weather_pieces:
            d = {
                "type": type(piece).__name__,
                "position": {"q": piece.position.q, "r": piece.position.r},
            }
            if hasattr(piece, "is_storm"):
                d["is_storm"] = piece.is_storm
            if hasattr(piece, "direction"):
                d["direction"] = getattr(piece, "direction", None)
            if hasattr(piece, "sector"):
                d["sector"] = getattr(piece, "sector", None)
            result.append(d)
        return result

    def serialize_turn_manager(tm):
        return {
            "total_days": tm.total_days,
            "current_day": tm.current_day,
            "current_hour": tm.current_hour,
            "turn_number": tm.turn_number,
            "current_phase_index": tm.current_phase_index,
            "side_with_initiative": tm.side_with_initiative,
            "combat_results_history": tm.combat_results_history,
        }

    def serialize_board(board):
        return {
            "width": board.width,
            "height": board.height,
            "land_hexes": list([{"q": h[0], "r": h[1]} if isinstance(h, tuple) else {"q": h.q, "r": h.r} for h in board.land_hexes]),
            "tiles": list({"q": t.q, "r": t.r, "terrain": t.terrain} for t in board.tiles),
            "players": {side: serialize_air_operations_chart(chart) for side, chart in board.players.items()},
            "pieces": [serialize_piece(piece) for piece in board.pieces]  # Save all pieces on the board
        }

    data = {
        "turn_manager": serialize_turn_manager(turn_manager),
        "board": serialize_board(board),
        "pieces": [serialize_piece(piece) for piece in board.pieces],  # Also save all pieces at the top level for convenience
        "weather": serialize_weather(weather_manager)
    }
    with open(save_path, "w") as f:
        json.dump(data, f, indent=2)
    return save_path


def load_game_state(filename):
    pass

    """
    with open(filename, "r") as f:
        data = json.load(f)

    # Deserialize the game state
    turn_manager = deserialize_turn_manager(data.get("turn_manager"))
    board = deserialize_board(data.get("board"))
    weather_manager = deserialize_weather(data.get("weather"))

    # Restore pieces on the board
    pieces = [deserialize_piece(piece_data) for piece_data in data.get("pieces", [])]
    board.pieces.extend(pieces)

    return board, turn_manager, weather_manager

    """