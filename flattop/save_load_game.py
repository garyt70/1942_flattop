import os
import json
import datetime
from flattop.operations_chart_models import AirFormation,  Aircraft, Base, TaskForce, Carrier

def save_game_state(board, turn_manager, weather_manager=None, filename_prefix="save"):
    """
    Save the full game state (board, pieces, turn manager, weather, air operations, etc.) to a JSON file in ~/flattop_1942/.
    """
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
            ships_data = []
            for s in gm.ships:
                ship_dict = {
                    "name": s.name,
                    "type": s.type,
                    "status": s.status,
                    "attack_factor": s.attack_factor,
                    "anti_air_factor": s.anti_air_factor,
                    "move_factor": s.move_factor,
                    "damage_factor": s.damage_factor,
                    "damage": s.damage
                }
                # If ship is a Carrier, serialize its base
                from flattop.operations_chart_models import Carrier
                if isinstance(s, Carrier):
                    ship_dict["base"] = serialize_game_model(s.base)
                ships_data.append(ship_dict)
            return {
                "type": "TaskForce",
                "number": getattr(gm, "number", None),
                "name": getattr(gm, "name", None),
                "side": getattr(gm, "side", None),
                "ships": ships_data,
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
    home_dir = os.path.expanduser("~")
    save_dir = os.path.join(home_dir, "flattop_1942")
    load_path = os.path.join(save_dir, filename)

    import json
    from flattop.hex_board_game_model import Hex, Piece, HexBoardModel, TurnManager
    from flattop.operations_chart_models import AirFormation, TaskForce, Base, Aircraft, AircraftType, AirOperationsConfiguration
    # Read JSON
    with open(load_path, "r") as f:
        data = json.load(f)

    # --- TurnManager ---
    tm_data = data.get("turn_manager", {})
    turn_manager = TurnManager(total_days=tm_data.get("total_days", 1))
    turn_manager.current_day = tm_data.get("current_day", 1)
    turn_manager.current_hour = tm_data.get("current_hour", 0)
    turn_manager.turn_number = tm_data.get("turn_number", 1)
    turn_manager.current_phase_index = tm_data.get("current_phase_index", 0)
    turn_manager.side_with_initiative = tm_data.get("side_with_initiative", None)
    turn_manager.combat_results_history = tm_data.get("combat_results_history", [])

    # --- Board ---
    board_data = data.get("board", {})
    width = board_data.get("width", 10)
    height = board_data.get("height", 10)
    land_hexes = set((h["q"], h["r"]) for h in board_data.get("land_hexes", []))
    board = HexBoardModel(width, height, land_hexes)

    # --- AirOperationsChart (players) ---
    def deserialize_air_operations_config(cfg):
        if not cfg:
            return None
        return AirOperationsConfiguration(
            name=cfg.get("name"),
            description=cfg.get("description"),
            maximum_capacity=cfg.get("maximum_capacity", 1),
            launch_factor_min=cfg.get("launch_factor_min", 1),
            launch_factor_normal=cfg.get("launch_factor_normal", 1),
            launch_factor_max=cfg.get("launch_factor_max", 1),
            ready_factors=cfg.get("ready_factors", 1),
            plane_handling_type=cfg.get("plane_handling_type", "CV"),
            aaf=cfg.get("aaf", 5)
        )

    def deserialize_aircraft(ac):
        t = ac["type"]
        # AircraftType is Enum, so try to match by value
        atype = None
        for v in AircraftType:
            if str(v) == t or v.value == t or str(v.value) == t:
                atype = v
                break
        if atype is None:
            atype = t  # fallback to string
        aircraft = Aircraft(atype, ac.get("count", 1), ac.get("move_factor", 5), ac.get("range_factor", 5))
        aircraft.range_remaining = ac.get("range_remaining", aircraft.range_factor)
        aircraft.armament = ac.get("armament", None)
        aircraft.height = ac.get("height", "Low")
        aircraft.attack_type = ac.get("attack_type", "Level")
        return aircraft

    def deserialize_airformation(afd):
        af = AirFormation(
            afd.get("number", 1),
            name=afd.get("name"),
            side=afd.get("side", "Allied"),
            launch_hour=afd.get("launch_hour", 0),
            height=afd.get("height", "High")
        )
        af.aircraft = [deserialize_aircraft(ac) for ac in afd.get("aircraft", [])]
        af.observed_condition = afd.get("observed_condition", 0)
        return af

    def deserialize_taskforce(tfd):
        tf = TaskForce(
            tfd.get("number", 1),
            name=tfd.get("name"),
            side=tfd.get("side", "Allied")
        )
        from flattop.operations_chart_models import Ship, Carrier
        tf.ships = []
        for s in tfd.get("ships", []):
            if s.get("type") == "CV":
                # Carrier: reconstruct with base if present
                carrier = Carrier(
                    s.get("name"),
                    s.get("type"),
                    s.get("status"),
                    s.get("attack_factor", 0),
                    s.get("anti_air_factor", 0),
                    s.get("move_factor", 2),
                    s.get("damage_factor", 1)
                )
                if "base" in s and s["base"]:
                    carrier.base = deserialize_base(s["base"])
                carrier.damage = s.get("damage", 0)
                tf.ships.append(carrier)
            else:
                ship = Ship(
                    s.get("name"), s.get("type"), s.get("status"),
                    s.get("attack_factor", 0), s.get("anti_air_factor", 0),
                    s.get("move_factor", 2), s.get("damage_factor", 1)
                )
                ship.damage = s.get("damage", 0)
                tf.ships.append(ship)
        tf.observed_condition = tfd.get("observed_condition", 0)
        return tf

    def deserialize_base(bd):
        cfg = deserialize_air_operations_config(bd.get("air_operations_config", {}))
        tracker_data = bd.get("air_operations_tracker", None)
        base = Base(
            name=bd.get("name"),
            side=bd.get("side", "Allied"),
            air_operations_config=cfg
        )
        base.damage = bd.get("damage", 0)
        base.observed_condition = bd.get("observed_condition", 0)
        # Restore air_operations_tracker if present
        if tracker_data:
            from flattop.operations_chart_models import AirOperationsTracker
            tracker = AirOperationsTracker(
                name=tracker_data.get("name", ""),
                description=tracker_data.get("description", ""),
                op_config=deserialize_air_operations_config(tracker_data.get("air_op_config", {})) or cfg
            )
            def ac_list(lst):
                return [deserialize_aircraft(ac) for ac in lst]
            tracker.in_flight = ac_list(tracker_data.get("in_flight", []))
            tracker.just_landed = ac_list(tracker_data.get("just_landed", []))
            tracker.readying = ac_list(tracker_data.get("readying", []))
            tracker.ready = ac_list(tracker_data.get("ready", []))
            tracker.used_ready_factor = tracker_data.get("used_ready_factor", 0)
            tracker.used_launch_factor = tracker_data.get("used_launch_factor", 0)
            base.air_operations_tracker = tracker
        return base

    def deserialize_piece(pd):
        pos = pd["position"]
        hex_obj = Hex(pos["q"], pos["r"], pos.get("terrain", "sea"))
        gm = pd.get("game_model", None)
        game_model = None
        if gm:
            if gm.get("type") == "AirFormation":
                game_model = deserialize_airformation(gm)
            elif gm.get("type") == "TaskForce":
                game_model = deserialize_taskforce(gm)
            elif gm.get("type") == "Base":
                game_model = deserialize_base(gm)
        piece = Piece(
            name=pd.get("name"),
            side=pd.get("side", "Allied"),
            position=hex_obj,
            gameModel=game_model
        )
        piece.has_moved = pd.get("has_moved", False)
        piece.phase_move_count = pd.get("phase_move_count", 0)
        return piece

    # Players (AirOperationsChart)
    from flattop.operations_chart_models import AirOperationsChart
    board.players = {}
    for side, chart in (board_data.get("players", {})).items():
        aoc = AirOperationsChart(name=chart.get("name"), description=chart.get("description"), side=chart.get("side", side))
        # Air Formations
        for num, af in chart.get("air_formations", {}).items():
            if af:
                aoc.air_formations[int(num)] = deserialize_airformation(af)
        # Task Forces
        for num, tf in chart.get("task_forces", {}).items():
            if tf:
                aoc.task_forces[int(num)] = deserialize_taskforce(tf)
        # Bases
        for name, base in chart.get("bases", {}).items():
            if base:
                aoc.bases[name] = deserialize_base(base)
        board.players[side] = aoc

    # --- Pieces ---
    board.pieces = [deserialize_piece(pd) for pd in data.get("pieces", [])]

    # --- Weather ---
    weather_data = data.get("weather", [])
    weather_pieces = []
    if weather_data:
        from flattop.weather_model import CloudMarker, WindDirection
        for wd in weather_data:
            t = wd.get("type")
            if t == "CloudMarker":
                sector = wd.get("sector", 1)
                pos = wd.get("position", {})
                hex_obj = Hex(pos.get("q", 0), pos.get("r", 0))
                cloud_type = wd.get("cloud_type", "scattered") if "cloud_type" in wd else "scattered"
                is_storm = wd.get("is_storm", False)
                cloud = CloudMarker(sector, hex_obj, cloud_type)
                cloud.is_storm = is_storm
                weather_pieces.append(cloud)
            elif t == "Piece":
                # Possibly a wind marker as Piece with WindDirection as gameModel
                # Not used in serialization, but handle for completeness
                pass
            elif t == "WindDirection":
                # WindDirection is not a Piece, but we can reconstruct it if needed
                sector = wd.get("sector", 1)
                direction = wd.get("direction", 1)
                wind = WindDirection(sector, direction)
                weather_pieces.append(wind)

    return board, turn_manager, weather_pieces