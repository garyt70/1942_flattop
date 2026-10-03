"""
Server-authoritative game session used by the web API.

A GameSession owns one authoritative HexBoardModel/TurnManager built from a
validated scenario, and exposes side-filtered projections plus a small set of
commands. This is a functional prototype of the command/projection boundary
described in docs/design/WEB_ARCHITECTURE.md: it keeps rules in the domain
layer (flattop package) and only formats/validates requests here.
"""

from __future__ import annotations

from typing import Any

from flattop.game_engine import perform_turn_start_actions
from flattop.hex_board_game_model import Hex, HexBoardModel, Piece, TurnManager, get_distance
from flattop.operations_chart_models import (
    AircraftFactory,
    AircraftOperationsStatus,
    AircraftType,
    AirFormation,
    Base,
    Carrier,
    TaskForce,
)
from flattop.scenarios import build_game_from_scenario, new_game_id

_AIRCRAFT_TYPE_BY_VALUE = {member.value: member for member in AircraftType}

VALID_SIDES = ("Allied", "Japanese")


class CommandError(Exception):
    """Raised for an invalid command; carries a stable machine-readable code."""

    def __init__(self, code: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


def _normalize_side(side: str) -> str:
    label = "Allied" if side.lower().startswith("allied") else "Japanese" if side.lower().startswith("japanese") else None
    if label is None:
        raise CommandError("UNKNOWN_SIDE", f"Unknown side '{side}'")
    return label


class GameSession:
    def __init__(self, scenario: dict[str, Any], player_side: str, opponent: str):
        self.id = new_game_id()
        self.scenario = scenario
        self.player_side = _normalize_side(player_side)
        self.opponent = opponent
        self.board, self.turn_manager = build_game_from_scenario(scenario)
        self.event_log: list[str] = []
        self._log(f"Game created from scenario '{scenario['name']}' ({scenario['version']}).")

    # -- logging -----------------------------------------------------
    def _log(self, message: str):
        self.event_log.append(message)

    # -- lookups -------------------------------------------------------
    def _find_piece(self, piece_id: str) -> Piece:
        for piece in self.board.pieces:
            if getattr(piece, "id", None) == piece_id:
                return piece
        raise CommandError("UNKNOWN_UNIT", f"No unit with id '{piece_id}'")

    # -- commands --------------------------------------------------------
    def advance_phase(self) -> None:
        previous_turn = self.turn_manager.turn_number
        self.turn_manager.next_phase(self.board)
        self._log(f"Advanced to phase '{self.turn_manager.current_phase}' (turn {self.turn_manager.turn_number}).")
        if self.turn_manager.turn_number != previous_turn:
            perform_turn_start_actions(self.board, _weather_manager_for(self), self.turn_manager)
            self._log(f"Turn {self.turn_manager.turn_number} started.")

    def move_piece(self, piece_id: str, q: int, r: int) -> None:
        piece = self._find_piece(piece_id)
        target = Hex(q, r)
        if not self.board.is_valid_tile(target):
            raise CommandError("OUT_OF_BOUNDS", f"Hex ({q}, {r}) is outside the board")
        distance = get_distance(piece.position, target)
        if distance > piece.movement_factor:
            raise CommandError(
                "INSUFFICIENT_MOVEMENT",
                f"{piece.name} has {piece.movement_factor} movement factor, requested {distance}",
                {"requested": distance, "available": piece.movement_factor},
            )
        if not self.board.move_piece(piece, target):
            raise CommandError("ILLEGAL_MOVE", f"{piece.name} cannot move to ({q}, {r})")
        self._log(f"{piece.name} moved to ({q}, {r}).")

    def _odd_q_neighbors(self, hex_coord):
        # Must match get_distance() and the web map, which use odd-q offset coordinates.
        if hex_coord.q % 2 == 0:
            deltas = [(1, -1), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 0)]
        else:
            deltas = [(1, 0), (1, 1), (0, -1), (0, 1), (-1, 0), (-1, 1)]
        neighbors = []
        for dq, dr in deltas:
            neighbor = self.board.get_hex(hex_coord.q + dq, hex_coord.r + dr)
            if neighbor:
                neighbors.append(neighbor)
        return neighbors

    def reachable_hexes(self, piece_id: str) -> list[list[int]]:
        """BFS flood-fill of hexes within the piece's remaining movement factor.

        TaskForce pieces cannot cross land hexes; other movable pieces are unrestricted.
        """
        piece = self._find_piece(piece_id)
        if not piece.can_move or piece.has_moved:
            return []

        max_range = piece.movement_factor
        sea_only = isinstance(piece.game_model, TaskForce)
        start = piece.position
        visited = {(start.q, start.r): 0}
        frontier = [start]
        while frontier:
            next_frontier = []
            for current in frontier:
                current_distance = visited[(current.q, current.r)]
                if current_distance >= max_range:
                    continue
                for neighbor in self._odd_q_neighbors(current):
                    key = (neighbor.q, neighbor.r)
                    if key in visited:
                        continue
                    if sea_only and self.board.get_terrain(neighbor) == "land":
                        continue
                    visited[key] = current_distance + 1
                    next_frontier.append(neighbor)
            frontier = next_frontier

        return [[q, r] for (q, r) in visited if (q, r) != (start.q, start.r)]

    def readiness_move(self, base_id: str, aircraft_type: str, from_status: str, to_status: str, count: int) -> None:
        base = self._resolve_base(base_id)
        tracker = base.air_operations_tracker
        source_list = _status_list(tracker, from_status)
        aircraft_type_enum = _AIRCRAFT_TYPE_BY_VALUE.get(aircraft_type)
        if aircraft_type_enum is None:
            raise CommandError("UNKNOWN_AIRCRAFT", f"Unknown aircraft type '{aircraft_type}'")

        source_entry = next((ac for ac in source_list if _aircraft_type_value(ac.type) == aircraft_type_enum.value), None)
        if source_entry is None or source_entry.count < count:
            available = source_entry.count if source_entry else 0
            raise CommandError(
                "INSUFFICIENT_AIRCRAFT",
                f"Only {available} {aircraft_type} available in {from_status}",
                {"requested": count, "available": available},
            )

        remaining_rf = base.available_ready_factor - base.used_ready_factor
        if count > remaining_rf:
            raise CommandError(
                "INSUFFICIENT_RF",
                f"Only {remaining_rf} Readying Factor remains.",
                {"requested": count, "available": remaining_rf},
            )

        moving = source_entry.copy()
        moving.count = count
        tracker.set_operations_status(moving, to_status, from_aircraft=source_entry)
        self._log(f"{base.name}: moved {count} {aircraft_type} from {from_status} to {to_status}.")

    def set_armament(self, base_id: str, aircraft_type: str, armament: str | None) -> None:
        """Sets the armament of a Readying aircraft factor (REQ-08.02b: armament is only editable in Readying)."""
        base = self._resolve_base(base_id)
        tracker = base.air_operations_tracker
        aircraft_type_enum = _AIRCRAFT_TYPE_BY_VALUE.get(aircraft_type)
        if aircraft_type_enum is None:
            raise CommandError("UNKNOWN_AIRCRAFT", f"Unknown aircraft type '{aircraft_type}'")

        entry = next((ac for ac in tracker.readying if _aircraft_type_value(ac.type) == aircraft_type_enum.value), None)
        if entry is None:
            raise CommandError("NOT_READYING", f"{aircraft_type} is not in Readying and cannot have its armament changed")

        entry.armament = armament or None
        self._log(f"{base.name}: set {aircraft_type} armament to {entry.armament or 'None'}.")

    def create_air_formation(self, base_id: str, aircraft: list[dict[str, Any]]) -> str:
        base = self._resolve_base(base_id)
        piece = self._find_piece(base_id)
        if not aircraft:
            raise CommandError("EMPTY_FORMATION", "At least one aircraft entry is required to create a formation")
        used_numbers = {
            board_piece.game_model.number
            for board_piece in self.board.pieces
            if board_piece.side == piece.side and isinstance(board_piece.game_model, AirFormation)
        }
        formation_number = 1
        while formation_number in used_numbers:
            formation_number += 1
        requested = []
        for entry in aircraft:
            aircraft_type_enum = _AIRCRAFT_TYPE_BY_VALUE.get(entry["type"])
            if aircraft_type_enum is None:
                raise CommandError("UNKNOWN_AIRCRAFT", f"Unknown aircraft type '{entry['type']}'")
            requested.append(AircraftFactory.create(aircraft_type_enum, entry["count"]))

        formation = base.create_air_formation(formation_number, aircraft=requested)
        if formation is None:
            raise CommandError("LAUNCH_FACTOR_EXCEEDED", "No aircraft available or launch factor exceeded")

        formation_piece = Piece(formation.name, side=piece.side, position=piece.position, gameModel=formation)
        formation_piece.id = f"{base_id}-formation-{formation_number}"
        self.board.add_piece(formation_piece)
        self._log(f"{base.name}: created Air Formation {formation_number}.")
        return formation_piece.id

    def _resolve_base(self, base_id: str) -> Base:
        piece = self._find_piece(base_id)
        if isinstance(piece.game_model, Base):
            return piece.game_model
        if isinstance(piece.game_model, TaskForce):
            carriers = piece.game_model.get_carriers()
            if carriers:
                return carriers[0].base
        raise CommandError("NOT_AN_AIRBASE", f"Unit '{base_id}' has no air operations")

    # -- projections -------------------------------------------------------
    def to_projection(self, side: str) -> dict[str, Any]:
        side = _normalize_side(side)
        board_def = self.scenario["board"]
        pieces = [self._piece_projection(piece, side) for piece in self.board.pieces]
        pieces = [p for p in pieces if p is not None]
        vp = self.turn_manager.victory_points
        return {
            "game_id": self.id,
            "scenario": {
                "id": self.scenario["id"],
                "name": self.scenario["name"],
                "version": self.scenario["version"],
            },
            "viewing_side": side,
            "board": {
                "width": board_def["width"],
                "height": board_def["height"],
                "land_hexes": board_def.get("land_hexes", []),
            },
            "turn": {
                "turn_number": self.turn_manager.turn_number,
                "day": self.turn_manager.current_day,
                "hour": self.turn_manager.current_hour,
                "is_night": self.turn_manager.is_night(),
                "phase": self.turn_manager.current_phase,
                "phases": self.turn_manager.PHASES,
                "initiative": self.turn_manager.side_with_initiative,
            },
            "score": {
                "allied": vp.get_points("Allied"),
                "japanese": vp.get_points("Japanese"),
            },
            "units": pieces,
            "log": self.event_log[-50:],
        }

    def _piece_projection(self, piece: Piece, viewing_side: str) -> dict[str, Any] | None:
        is_friendly = piece.side == viewing_side
        is_observed = piece.observed_condition and piece.observed_condition > 0
        if piece.side == "Weather":
            return {
                "id": id(piece),
                "kind": "Weather",
                "side": "Weather",
                "position": [piece.position.q, piece.position.r],
            }
        # Airbases are fixed installations whose location is always known; only their
        # aircraft contents (added below, friendly-only) are hidden from the enemy.
        is_base = isinstance(piece.game_model, Base)
        if not is_friendly and not is_observed and not is_base:
            return None

        piece_id = getattr(piece, "id", None) or str(id(piece))
        base_info = {
            "id": piece_id,
            "name": piece.name,
            "side": piece.side,
            "position": [piece.position.q, piece.position.r],
            "friendly": is_friendly,
            "observed_condition": piece.observed_condition,
            "movement_factor": piece.movement_factor,
            "has_moved": piece.has_moved,
        }

        model = piece.game_model
        if isinstance(model, Base):
            base_info["kind"] = "Base"
            base_info["damage"] = model.damage
            if is_friendly:
                base_info["air_operations"] = _air_operations_projection(model)
        elif isinstance(model, TaskForce):
            base_info["kind"] = "TaskForce"
            if is_friendly:
                base_info["ships"] = [_ship_projection(ship) for ship in model.ships]
            else:
                base_info["ship_count"] = len(model.ships)
        elif isinstance(model, AirFormation):
            base_info["kind"] = "AirFormation"
            base_info["altitude"] = model.height
            if is_friendly:
                base_info["aircraft"] = [_aircraft_projection(ac) for ac in model.aircraft]
            else:
                base_info["aircraft_count"] = sum(ac.count for ac in model.aircraft)
        else:
            base_info["kind"] = "Unknown"

        return base_info


def _status_list(tracker, status: str):
    mapping = {
        AircraftOperationsStatus.JUST_LANDED.value: tracker.just_landed,
        AircraftOperationsStatus.READYING.value: tracker.readying,
        AircraftOperationsStatus.READY.value: tracker.ready,
        AircraftOperationsStatus.IN_FLIGHT.value: tracker.in_flight,
    }
    if status not in mapping:
        raise CommandError("UNKNOWN_STATUS", f"Unknown aircraft status '{status}'")
    return mapping[status]


def _air_operations_projection(base: Base) -> dict[str, Any]:
    tracker = base.air_operations_tracker
    return {
        "launch_factor_min": base.available_launch_factor_min,
        "launch_factor_normal": base.available_launch_factor_normal,
        "launch_factor_max": base.available_launch_factor_max,
        "used_launch_factor": base.used_launch_factor,
        "ready_factor": base.available_ready_factor,
        "used_ready_factor": base.used_ready_factor,
        "ready": [_aircraft_projection(ac) for ac in tracker.ready],
        "readying": [_aircraft_projection(ac) for ac in tracker.readying],
        "just_landed": [_aircraft_projection(ac) for ac in tracker.just_landed],
        "in_flight": [_aircraft_projection(ac) for ac in tracker.in_flight],
    }


def _aircraft_type_value(aircraft_type) -> str:
    return aircraft_type.value if hasattr(aircraft_type, "value") else aircraft_type


def _aircraft_projection(aircraft) -> dict[str, Any]:
    cd = aircraft.combat_data
    return {
        "type": _aircraft_type_value(aircraft.type),
        "count": aircraft.count,
        "move_factor": aircraft.move_factor,
        "range_factor": aircraft.range_factor,
        "range_remaining": aircraft.range_remaining,
        "armament": aircraft.armament,
        "combat_data": {
            "air_to_air": cd.air_to_air,
            "level_bombing_high_base_gp": cd.level_bombing_high_base_gp,
            "level_bombing_high_base_ap": cd.level_bombing_high_base_ap,
            "level_bombing_low_base_gp": cd.level_bombing_low_base_gp,
            "level_bombing_low_base_ap": cd.level_bombing_low_base_ap,
            "dive_bombing_base_gp": cd.dive_bombing_base_gp,
            "dive_bombing_base_ap": cd.dive_bombing_base_ap,
            "level_bombing_high_ship_gp": cd.level_bombing_high_ship_gp,
            "level_bombing_high_ship_ap": cd.level_bombing_high_ship_ap,
            "level_bombing_low_ship_gp": cd.level_bombing_low_ship_gp,
            "level_bombing_low_ship_ap": cd.level_bombing_low_ship_ap,
            "dive_bombing_ship_gp": cd.dive_bombing_ship_gp,
            "dive_bombing_ship_ap": cd.dive_bombing_ship_ap,
            "torpedo_bombing_ship": cd.torpedo_bombing_ship,
        },
    }


def _ship_projection(ship) -> dict[str, Any]:
    info = {
        "name": ship.name,
        "type": ship.type,
        "status": ship.status,
        "damage": ship.damage,
        "damage_factor": ship.damage_factor,
        "gunnery_factor": ship.attack_factor,
        "torpedo_factor": ship.torpedo_factor,
        "anti_air_factor": ship.anti_air_factor,
        "move_factor": ship.move_factor,
    }
    if isinstance(ship, Carrier):
        info["air_operations"] = _air_operations_projection(ship.base)
    return info


def _weather_manager_for(session: GameSession):
    if not hasattr(session, "_weather_manager"):
        from flattop.weather_model import WeatherManager

        session._weather_manager = WeatherManager(session.board)
    return session._weather_manager
