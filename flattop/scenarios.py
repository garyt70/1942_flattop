"""
Scenario catalog loading and validation.

Scenario definitions are versioned YAML files stored in the repository under
``scenarios/``. This module loads, validates, and exposes them to the web API,
and builds the initial game board/turn manager from a scenario's setup data.

See docs/design/SCENARIO_CATALOG_DESIGN.md for the design this implements.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any

import yaml

from flattop.hex_board_game_model import Hex, HexBoardModel, Piece, TurnManager
from flattop.operations_chart_models import (
    AircraftFactory,
    AircraftOperationsStatus,
    AircraftType,
    AirFormation,
    AirOperationsConfiguration,
    AlliedShipFactory,
    Base,
    Carrier,
    JapaneseShipFactory,
    Ship,
    TaskForce,
)

logger = logging.getLogger(__name__)

SCENARIOS_DIR = Path(__file__).resolve().parent.parent / "scenarios"

_AIRCRAFT_TYPE_BY_VALUE = {member.value: member for member in AircraftType}


class ScenarioError(Exception):
    """Raised when a scenario file is missing or fails validation."""


def _load_yaml_file(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _validate_scenario_document(document: dict[str, Any], path: Path) -> dict[str, Any]:
    if not isinstance(document, dict) or "scenario" not in document:
        raise ScenarioError(f"{path}: missing top-level 'scenario' key")

    scenario = document["scenario"]
    required_fields = ["id", "version", "name", "status", "ruleset", "board", "sides", "setup"]
    for field in required_fields:
        if field not in scenario:
            raise ScenarioError(f"{path}: scenario is missing required field '{field}'")

    board = scenario["board"]
    for field in ("width", "height"):
        if field not in board:
            raise ScenarioError(f"{path}: board is missing required field '{field}'")

    side_ids = {side["id"] for side in scenario["sides"]}
    if "allied" not in side_ids or "japanese" not in side_ids:
        raise ScenarioError(f"{path}: scenario sides must include 'allied' and 'japanese'")

    width, height = board["width"], board["height"]
    for q, r in board.get("land_hexes", []):
        if not (0 <= q < width and 0 <= r < height):
            raise ScenarioError(f"{path}: land hex ({q}, {r}) is outside board bounds")

    setup = scenario["setup"]
    known_ids = set()
    for base in setup.get("bases", []):
        if base["side"] not in side_ids:
            raise ScenarioError(f"{path}: base '{base['id']}' has unknown side '{base['side']}'")
        if base["id"] in known_ids:
            raise ScenarioError(f"{path}: duplicate setup id '{base['id']}'")
        known_ids.add(base["id"])
        _validate_position(base["position"], width, height, path, base["id"])

    for tf in setup.get("task_forces", []):
        if tf["side"] not in side_ids:
            raise ScenarioError(f"{path}: task force '{tf['id']}' has unknown side '{tf['side']}'")
        if tf["id"] in known_ids:
            raise ScenarioError(f"{path}: duplicate setup id '{tf['id']}'")
        known_ids.add(tf["id"])
        _validate_position(tf["position"], width, height, path, tf["id"])

    for formation in setup.get("air_formations", []):
        if formation["side"] not in side_ids:
            raise ScenarioError(f"{path}: air formation '{formation['id']}' has unknown side '{formation['side']}'")
        if formation["id"] in known_ids:
            raise ScenarioError(f"{path}: duplicate setup id '{formation['id']}'")
        known_ids.add(formation["id"])
        _validate_position(formation["position"], width, height, path, formation["id"])

    return scenario


def _validate_position(position, width, height, path, unit_id):
    if len(position) != 2 or not (0 <= position[0] < width and 0 <= position[1] < height):
        raise ScenarioError(f"{path}: unit '{unit_id}' position {position} is outside board bounds")


def load_all_scenarios() -> list[dict[str, Any]]:
    """Loads and validates every published scenario in the scenario catalog."""
    scenarios = []
    if not SCENARIOS_DIR.exists():
        return scenarios

    for path in sorted(SCENARIOS_DIR.glob("*.yaml")):
        document = _load_yaml_file(path)
        scenario = _validate_scenario_document(document, path)
        if scenario.get("status") == "published":
            scenarios.append(scenario)
    return scenarios


def get_scenario(scenario_id: str) -> dict[str, Any]:
    for scenario in load_all_scenarios():
        if scenario["id"] == scenario_id:
            return scenario
    raise ScenarioError(f"Unknown or unpublished scenario '{scenario_id}'")


def scenario_catalog_summary(scenario: dict[str, Any]) -> dict[str, Any]:
    """Read-only metadata suitable for the new-game screen (no hidden setup detail)."""
    board = scenario["board"]
    setup = scenario["setup"]
    return {
        "id": scenario["id"],
        "version": scenario["version"],
        "name": scenario["name"],
        "description": scenario.get("description", "").strip(),
        "status": scenario["status"],
        "ruleset": scenario["ruleset"],
        "board": {"width": board["width"], "height": board["height"]},
        "sides": scenario["sides"],
        "setup_summary": {
            "bases": len(setup.get("bases", [])),
            "task_forces": len(setup.get("task_forces", [])),
        },
    }


def _side_label(side_id: str) -> str:
    return "Allied" if side_id == "allied" else "Japanese"


_AIRCRAFT_STATE_TO_STATUS = {
    "ready": AircraftOperationsStatus.READY,
    "readying": AircraftOperationsStatus.READYING,
    "just_landed": AircraftOperationsStatus.JUST_LANDED,
}


def _add_aircraft_to_tracker(tracker, aircraft_entries: list[dict[str, Any]]):
    for entry in aircraft_entries:
        type_value = entry["type"]
        count = entry.get("count", 0)
        state = entry.get("state", "ready")
        aircraft_type = _AIRCRAFT_TYPE_BY_VALUE.get(type_value)
        if aircraft_type is None:
            raise ScenarioError(f"Unknown aircraft type '{type_value}' in scenario setup")
        aircraft = AircraftFactory.create(aircraft_type, count)
        status = _AIRCRAFT_STATE_TO_STATUS.get(state)
        if status is None:
            raise ScenarioError(f"Unknown aircraft state '{state}' in scenario setup")
        tracker.set_operations_status(aircraft, status)


def _build_base(entry: dict[str, Any]) -> Base:
    side = _side_label(entry["side"])
    air_ops = entry.get("air_operations")
    config = None
    if air_ops:
        config = AirOperationsConfiguration(
            name=entry["name"],
            description=f"Configuration for {entry['name']} base",
            maximum_capacity=air_ops.get("maximum_capacity", 1),
            launch_factor_min=air_ops.get("launch_factor_min", 1),
            launch_factor_normal=air_ops.get("launch_factor_normal", 1),
            launch_factor_max=air_ops.get("launch_factor_max", 1),
            ready_factors=air_ops.get("ready_factors", 1),
            plane_handling_type="Base",
        )
    base = Base(name=entry["name"], side=side, air_operations_config=config)
    _add_aircraft_to_tracker(base.air_operations_tracker, entry.get("aircraft", []))
    return base


def _build_task_force(entry: dict[str, Any]) -> TaskForce:
    side = _side_label(entry["side"])
    tf = TaskForce(entry.get("number", 1), name=entry.get("name"), side=side)
    factory = AlliedShipFactory if side == "Allied" else JapaneseShipFactory
    for ship_entry in entry.get("ships", []):
        if "class" in ship_entry:
            # Generic escort/support ship (e.g. destroyer, transport) with explicit stats.
            ship = Ship(
                ship_entry["name"],
                ship_entry["class"],
                "operational",
                ship_entry.get("gunnery_factor", 0),
                ship_entry.get("anti_air_factor", 0),
                ship_entry.get("move_factor", 2),
                ship_entry.get("damage_factor", 1),
                ship_entry.get("torpedo_factor", 0),
            )
        else:
            try:
                ship = factory.create(ship_entry["name"])
            except ValueError as error:
                raise ScenarioError(f"Unknown ship '{ship_entry['name']}' for side '{side}'") from error
        if isinstance(ship, Carrier) and ship_entry.get("aircraft"):
            _add_aircraft_to_tracker(ship.air_operations, ship_entry["aircraft"])
        tf.add_ship(ship)
    return tf


def _build_air_formation(entry: dict[str, Any]) -> AirFormation:
    side = _side_label(entry["side"])
    formation = AirFormation(entry.get("number", 1), name=entry.get("name"), side=side, height=entry.get("height", "High"))
    for aircraft_entry in entry.get("aircraft", []):
        type_value = aircraft_entry["type"]
        aircraft_type = _AIRCRAFT_TYPE_BY_VALUE.get(type_value)
        if aircraft_type is None:
            raise ScenarioError(f"Unknown aircraft type '{type_value}' in scenario setup")
        aircraft = AircraftFactory.create(aircraft_type, aircraft_entry.get("count", 0))
        if aircraft_entry.get("armament"):
            aircraft.armament = aircraft_entry["armament"]
        formation.add_aircraft(aircraft)
    return formation


def build_game_from_scenario(scenario: dict[str, Any]) -> tuple[HexBoardModel, TurnManager]:
    """Builds the initial authoritative board and turn manager for a validated scenario."""
    board_def = scenario["board"]
    land_hexes = {(q, r) for q, r in board_def.get("land_hexes", [])}
    board = HexBoardModel(board_def["width"], board_def["height"], land_hexes=land_hexes)
    turn_manager = TurnManager()

    setup = scenario["setup"]
    for base_entry in setup.get("bases", []):
        base = _build_base(base_entry)
        position = Hex(*base_entry["position"])
        piece = Piece(base_entry["name"], side=_side_label(base_entry["side"]), position=position, gameModel=base)
        piece.id = base_entry["id"]
        board.add_piece(piece)

    for tf_entry in setup.get("task_forces", []):
        tf = _build_task_force(tf_entry)
        position = Hex(*tf_entry["position"])
        piece = Piece(tf_entry.get("name", tf.name), side=_side_label(tf_entry["side"]), position=position, gameModel=tf)
        piece.id = tf_entry["id"]
        board.add_piece(piece)

    for formation_entry in setup.get("air_formations", []):
        formation = _build_air_formation(formation_entry)
        position = Hex(*formation_entry["position"])
        piece = Piece(
            formation_entry.get("name", formation.name),
            side=_side_label(formation_entry["side"]),
            position=position,
            gameModel=formation,
        )
        piece.id = formation_entry["id"]
        board.add_piece(piece)

    return board, turn_manager


def new_game_id() -> str:
    return uuid.uuid4().hex
