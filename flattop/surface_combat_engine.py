"""Surface combat engine.

This module resolves TaskForce-vs-TaskForce combat and is intentionally separate
from the air combat engine.
"""

import random
from typing import Callable

from flattop.aircombat_engine import get_hits_from_table, resolve_die_roll
from flattop.operations_chart_models import Carrier, Ship, TaskForce


def _ship_priority(ship: Ship) -> tuple[int, int, int]:
    """Higher tuple values are higher-priority targets."""
    ship_type = getattr(ship, "type", "")
    if ship_type in ("CV", "CVL"):
        return (4, ship.attack_factor, -ship.damage)
    if ship_type in ("BBS", "BB"):
        return (3, ship.attack_factor, -ship.damage)
    if ship_type in ("CA", "CL", "CAS", "CLS"):
        return (2, ship.attack_factor, -ship.damage)
    return (1, ship.attack_factor, -ship.damage)


def _select_target_ship(ships: list[Ship]) -> Ship | None:
    valid = [s for s in ships if s.status != "Sunk"]
    if not valid:
        return None
    return max(valid, key=_ship_priority)


def _base_result_number(attacker: Ship, defender: Ship, clouds: bool, night: bool) -> int:
    # Start from a middle table and apply lightweight situational modifiers.
    result_number = 8
    if clouds:
        result_number -= 1
    if night:
        result_number -= 2
    if attacker.status == "Crippled":
        result_number -= 1
    if defender.status in ("Crippled", "Anchored"):
        result_number += 2
    return max(1, min(15, result_number))


def _apply_hits(target: Ship, hits: int, eliminated_aircraft: list[tuple[str, int]]) -> bool:
    """Apply hits to target and return True when the ship sinks."""
    target.damage += hits
    if target.damage >= target.damage_factor:
        target.status = "Sunk"
        if isinstance(target, Carrier):
            tracker = target.air_operations
            for ac in tracker.ready + tracker.readying + tracker.just_landed + tracker.in_flight:
                eliminated_aircraft.append((ac.type.value, ac.count))
            tracker.ready = []
            tracker.readying = []
            tracker.just_landed = []
            tracker.in_flight = []
        return True
    return False


def _resolve_one_direction(
    attacker_tf: TaskForce,
    defender_tf: TaskForce,
    clouds: bool,
    night: bool,
    die_roll_fn: Callable[[], int],
    attacker_target_allocation: dict[Ship, Ship] | None = None,
) -> dict:
    story_line: list[str] = []
    per_ship_hits: dict[str, int] = {}
    sunk_ships: list[str] = []
    eliminated_aircraft: list[tuple[str, int]] = []

    attackers = [s for s in attacker_tf.ships if s.status != "Sunk" and s.attack_factor > 0]
    defenders = [s for s in defender_tf.ships if s.status != "Sunk"]

    for attacker in attackers:
        target = None
        if attacker_target_allocation:
            allocated_target = attacker_target_allocation.get(attacker)
            if allocated_target in defenders and allocated_target.status != "Sunk":
                target = allocated_target
        if target is None:
            target = _select_target_ship(defenders)
        if target is None:
            break

        result_number = _base_result_number(attacker, target, clouds=clouds, night=night)
        die_roll = die_roll_fn()
        hit_table = resolve_die_roll(result_number, die_roll)
        hits = get_hits_from_table(hit_table, max(1, attacker.attack_factor))

        attacker.attacked_this_turn = True
        attacker.surface_combat_exhausted = True

        story_line.append(
            f"{attacker.name} fired on {target.name} (table {hit_table}, die {die_roll}) for {hits} hit(s)."
        )

        if hits <= 0:
            continue

        per_ship_hits[target.name] = per_ship_hits.get(target.name, 0) + hits
        if _apply_hits(target, hits, eliminated_aircraft):
            sunk_ships.append(target.name)
            story_line.append(f"{target.name} was sunk by surface fire.")
            defenders = [s for s in defender_tf.ships if s.status != "Sunk"]

    attacker_tf.attacked_this_turn = attacker_tf.attacked_this_turn or len(attackers) > 0

    return {
        "hits": per_ship_hits,
        "sunk_ships": sunk_ships,
        "story_line": story_line,
        "eliminated_aircraft": eliminated_aircraft,
    }


def resolve_surface_combat(
    attacker_taskforce: TaskForce,
    defender_taskforce: TaskForce,
    clouds: bool = False,
    night: bool = False,
    die_roll_fn: Callable[[], int] | None = None,
    attacker_target_allocation: dict[Ship, Ship] | None = None,
) -> dict | None:
    """Resolve bidirectional surface combat between two task forces.

    Returns a dict payload for combat logs, or None if combat cannot be resolved.
    """
    if attacker_taskforce is None or defender_taskforce is None:
        return None

    if not attacker_taskforce.ships or not defender_taskforce.ships:
        return None

    if die_roll_fn is None:
        die_roll_fn = lambda: random.randint(1, 6)

    attacker_report = _resolve_one_direction(
        attacker_taskforce,
        defender_taskforce,
        clouds=clouds,
        night=night,
        die_roll_fn=die_roll_fn,
        attacker_target_allocation=attacker_target_allocation,
    )

    defender_report = _resolve_one_direction(
        defender_taskforce,
        attacker_taskforce,
        clouds=clouds,
        night=night,
        die_roll_fn=die_roll_fn,
    )

    attacker_taskforce.ships = [s for s in attacker_taskforce.ships if s.status != "Sunk"]
    defender_taskforce.ships = [s for s in defender_taskforce.ships if s.status != "Sunk"]

    return {
        "attacker": attacker_report,
        "defender": defender_report,
        "attacker_destroyed": len(attacker_taskforce.ships) == 0,
        "defender_destroyed": len(defender_taskforce.ships) == 0,
    }
