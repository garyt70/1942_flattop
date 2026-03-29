"""Surface combat engine — rule-accurate implementation of Section 19.

This module resolves TaskForce-vs-TaskForce Surface Attack Combat and is
intentionally separate from the air combat engine.

Key rules implemented (game_requirements.txt §19):
- Three ship positions: Gunnery Attack, Torpedo Attack, Screen
- Crippled / anchored ships forced to Screen
- BHT = sum of two secret dice (one per player)
- Gunnery combat: simultaneous; only BB/CA/CAV factors may target enemy BBs
- Torpedo combat: only when BHT ≥ 10 (day) or ≥ 7 (night); Japanese BHT=15,
  Allied BHT=10; torpedo supply is a one-game resource (torpedo_factor_used)
- Ammunition tracking: each gunnery turn expends BHT ammo; if BHT > remaining
  ammo, gunnery halved; DD may fire once regardless of BHT then flip
- Breakthrough combat: 3:1 surviving gunnery ratio → winner hits screened ships
- Modifiers: crippled target +1 BHT, anchored target +1 BHT
- Ships sunk in gunnery phase do NOT fire torpedoes
"""

import random
from typing import Callable

from flattop.aircombat_engine import get_hits_from_table, resolve_die_roll
from flattop.operations_chart_models import Carrier, Ship, TaskForce

# Position string constants
POSITION_GUNNERY = "gunnery"
POSITION_TORPEDO = "torpedo"
POSITION_SCREEN   = "screen"

# Ship types whose gunnery is allowed to target enemy BBs (rule 19.5.1)
BB_KILLER_TYPES = {"BB", "BBS", "CA", "CAS", "CAV"}
BB_TYPES = {"BB", "BBS"}

# Side identifier for torpedo BHT rule
JAPANESE = "Japanese"


def assign_default_positions(ships: list[Ship], side: str = "Allied") -> dict[Ship, str]:
    """Build a default position map: crippled/anchored → Screen, else Gunnery."""
    positions: dict[Ship, str] = {}
    for ship in ships:
        if ship.status in ("Crippled", "Anchored", "Sunk"):
            positions[ship] = POSITION_SCREEN
        elif ship.torpedo_factor > 0 and not getattr(ship, "torpedo_factor_used", False):
            positions[ship] = POSITION_TORPEDO
        else:
            positions[ship] = POSITION_GUNNERY
    return positions


def _hits_from_bht(bht: int, factors: int, die_roll_fn: Callable[[], int]) -> tuple[str, int, int]:
    """Roll attack using bht and factors. Returns (table_name, die_rolled, hits)."""
    result_number = max(1, min(15, bht))
    die = die_roll_fn()
    table = resolve_die_roll(result_number, die)
    hits = get_hits_from_table(table, max(1, factors))
    return table, die, hits


def _apply_hits(target: Ship, hits: int, eliminated_aircraft: list) -> bool:
    """Apply hits; return True when ship sinks."""
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
    elif target.damage >= (target.damage_factor // 2) and target.status not in ("Crippled", "Sunk"):
        target.status = "Crippled"
    return False


# ─────────────────────────────── Target selection ────────────────────────────

def _ship_priority(ship: Ship) -> tuple[int, int, int]:
    """Higher tuple values are higher-priority targets (CV first, then BBs, etc.)."""
    t = getattr(ship, "type", "")
    if t in ("CV", "CVL"):
        return (4, ship.attack_factor, -ship.damage)
    if t in ("BB", "BBS"):
        return (3, ship.attack_factor, -ship.damage)
    if t in ("CA", "CL", "CAS", "CLS", "CAV"):
        return (2, ship.attack_factor, -ship.damage)
    return (1, ship.attack_factor, -ship.damage)


def _select_target(ships: list[Ship], _side: str = "") -> Ship | None:
    valid = [s for s in ships if s.status != "Sunk"]
    if not valid:
        return None
    return max(valid, key=_ship_priority)


def _target_modifiers(target: Ship) -> int:
    """Return BHT modifier for the target's condition (rule 19.10)."""
    mod = 0
    if target.status == "Crippled":
        mod += 1
    if target.status == "Anchored":
        mod += 1
    return mod


# ─────────────────────────────── Gunnery phase ───────────────────────────────

def _resolve_gunnery(
    firing_ships: list[Ship],
    target_ships: list[Ship],
    firing_side: str,
    bht: int,
    die_roll_fn: Callable[[], int],
    gunnery_targets: dict[Ship, Ship] | None,
    enemy_bb_types: set[str],
) -> dict:
    """Resolve gunnery combat (rule 19.5).

    gunnery_targets: optional {attacker_ship: target_ship} allocation from UI.
    Returns per-round result dict.
    """
    story: list[str] = []
    per_target_hits: dict[str, int] = {}
    sunk: list[str] = []
    eliminated_aircraft: list = []

    # Accumulate damage separately — combat is simultaneous (rule 19.5.2)
    pending_damage: dict[Ship, int] = {}

    for ship in firing_ships:
        if ship.status == "Sunk":
            continue
        if ship.attack_factor <= 0:
            continue

        # Ammunition check (rule 19.8.1)
        available_ammo = getattr(ship, "ammunition_factor", 99)
        is_dd = ship.type in ("DD", "APD")
        if not is_dd and available_ammo <= 0:
            story.append(f"{ship.name} has no ammunition — cannot fire.")
            continue

        factors = ship.attack_factor

        if not is_dd and available_ammo < bht:
            factors = max(1, factors // 2)
            story.append(
                f"{ship.name} running low on ammo ({available_ammo}); halving gunnery to {factors}."
            )

        # Choose target
        target = None
        if gunnery_targets and ship in gunnery_targets:
            candidate = gunnery_targets[ship]
            if candidate and candidate.status != "Sunk" and candidate in target_ships:
                target = candidate

        if target is None:
            target = _select_target(target_ships, firing_side)
        if target is None:
            continue

        # BB restriction (rule 19.5.1): only BB_KILLER_TYPES may target enemy BBs
        if target.type in enemy_bb_types and ship.type not in BB_KILLER_TYPES:
            story.append(
                f"{ship.name} ({ship.type}) cannot target BB {target.name}; re-targeting."
            )
            fallback = _select_target(
                [s for s in target_ships if s.type not in enemy_bb_types], firing_side
            )
            if fallback is None:
                continue
            target = fallback

        effective_bht = bht + _target_modifiers(target)
        table, die, hits = _hits_from_bht(effective_bht, factors, die_roll_fn)
        story.append(
            f"{ship.name} ({factors} GF) fires at {target.name} "
            f"[table {table}, die {die}] → {hits} hit(s)."
        )

        pending_damage[target] = pending_damage.get(target, 0) + hits

        # Consume ammo
        if not is_dd:
            ship.ammunition_factor = max(0, available_ammo - bht)
        ship.attacked_this_turn = True
        ship.surface_combat_exhausted = True

    # Apply accumulated damage simultaneously
    for target, total_hits in pending_damage.items():
        per_target_hits[target.name] = per_target_hits.get(target.name, 0) + total_hits
        if _apply_hits(target, total_hits, eliminated_aircraft):
            sunk.append(target.name)
            story.append(f"{target.name} sinks from gunnery fire!")

    return {
        "hits": per_target_hits,
        "sunk_ships": sunk,
        "story_line": story,
        "eliminated_aircraft": eliminated_aircraft,
    }


# ─────────────────────────────── Torpedo phase ───────────────────────────────

def _resolve_torpedoes(
    firing_ships: list[Ship],
    target_ships: list[Ship],
    firing_side: str,
    bht: int,
    night: bool,
    die_roll_fn: Callable[[], int],
    torpedo_targets: dict[Ship, Ship] | None,
) -> dict:
    """Resolve torpedo attacks (rule 19.6).

    Threshold: BHT ≥ 10 (day) or ≥ 7 (night).
    Japanese torpedo BHT = 15; Allied = 10.
    Torpedo supply permanently expended after use.
    """
    story: list[str] = []
    threshold = 7 if night else 10
    if bht < threshold:
        story.append(f"BHT {bht} < {threshold} — torpedo attacks blocked (rule 19.6.1).")
        return {
            "hits": {}, "sunk_ships": [], "story_line": story,
            "eliminated_aircraft": [], "torpedoes_blocked": True,
        }

    torpedo_bht = 15 if firing_side == JAPANESE else 10
    pending_damage: dict[Ship, int] = {}
    per_target_hits: dict[str, int] = {}
    sunk: list[str] = []
    eliminated_aircraft: list = []

    for ship in firing_ships:
        if ship.status == "Sunk":
            continue
        if ship.torpedo_factor <= 0 or getattr(ship, "torpedo_factor_used", False):
            continue

        target = None
        if torpedo_targets and ship in torpedo_targets:
            candidate = torpedo_targets[ship]
            if candidate and candidate.status != "Sunk" and candidate in target_ships:
                target = candidate
        if target is None:
            target = _select_target(target_ships, firing_side)
        if target is None:
            continue

        effective_bht = torpedo_bht + _target_modifiers(target)
        table, die, hits = _hits_from_bht(effective_bht, ship.torpedo_factor, die_roll_fn)
        story.append(
            f"{ship.name} fires torpedoes ({ship.torpedo_factor} TF) at {target.name} "
            f"[torp-BHT {effective_bht}, die {die}] → {hits} hit(s)."
        )

        ship.torpedo_factor_used = True
        ship.surface_combat_exhausted = True
        pending_damage[target] = pending_damage.get(target, 0) + hits

    for target, total_hits in pending_damage.items():
        per_target_hits[target.name] = per_target_hits.get(target.name, 0) + total_hits
        if _apply_hits(target, total_hits, eliminated_aircraft):
            sunk.append(target.name)
            story.append(f"{target.name} sinks from torpedo attack!")

    return {
        "hits": per_target_hits,
        "sunk_ships": sunk,
        "story_line": story,
        "eliminated_aircraft": eliminated_aircraft,
        "torpedoes_blocked": False,
    }


# ──────────────────────────── Breakthrough phase ─────────────────────────────

def _calc_surviving_gunnery(ships: list[Ship], positions: dict[Ship, str]) -> int:
    return sum(
        s.attack_factor for s in ships
        if s.status != "Sunk" and positions.get(s) in (POSITION_GUNNERY, POSITION_TORPEDO)
    )


def _resolve_breakthrough(
    attacker_ships: list[Ship],
    attacker_positions: dict[Ship, str],
    defender_ships: list[Ship],
    defender_positions: dict[Ship, str],
    attacker_side: str,
    bht: int,
    die_roll_fn: Callable[[], int],
) -> dict | None:
    """Resolve breakthrough combat (rule 19.7).

    Returns None if no 3:1 ratio exists.
    """
    att_gf = _calc_surviving_gunnery(attacker_ships, attacker_positions)
    def_gf = _calc_surviving_gunnery(defender_ships, defender_positions)

    if att_gf == 0 and def_gf == 0:
        return None

    if def_gf > 0 and att_gf / def_gf >= 3:
        breakthrough_side = "attacker"
        firing = [
            s for s in attacker_ships
            if s.status != "Sunk" and attacker_positions.get(s) in (POSITION_GUNNERY, POSITION_TORPEDO)
        ]
        targets = [
            s for s in defender_ships
            if s.status != "Sunk" and defender_positions.get(s) == POSITION_SCREEN
        ]
    elif att_gf > 0 and def_gf / att_gf >= 3:
        breakthrough_side = "defender"
        firing = [
            s for s in defender_ships
            if s.status != "Sunk" and defender_positions.get(s) in (POSITION_GUNNERY, POSITION_TORPEDO)
        ]
        targets = [
            s for s in attacker_ships
            if s.status != "Sunk" and attacker_positions.get(s) == POSITION_SCREEN
        ]
    else:
        return None

    story: list[str] = [f"BREAKTHROUGH by {breakthrough_side}!"]
    if not targets:
        story.append("No screened targets to attack.")
        return {"side": breakthrough_side, "hits": {}, "sunk_ships": [], "story_line": story, "eliminated_aircraft": []}

    pending_damage: dict[Ship, int] = {}
    per_hits: dict[str, int] = {}
    sunk: list[str] = []
    eliminated_aircraft: list = []

    for ship in firing:
        if ship.attack_factor <= 0:
            continue
        target = _select_target(targets, breakthrough_side)
        if target is None:
            break
        effective_bht = bht + _target_modifiers(target)
        table, die, hits = _hits_from_bht(effective_bht, ship.attack_factor, die_roll_fn)
        story.append(
            f"Breakthrough: {ship.name} fires at screened {target.name} "
            f"[table {table}, die {die}] → {hits} hit(s)."
        )
        pending_damage[target] = pending_damage.get(target, 0) + hits

    for target, total_hits in pending_damage.items():
        per_hits[target.name] = per_hits.get(target.name, 0) + total_hits
        if _apply_hits(target, total_hits, eliminated_aircraft):
            sunk.append(target.name)
            story.append(f"{target.name} sinks during breakthrough!")

    return {
        "side": breakthrough_side,
        "hits": per_hits,
        "sunk_ships": sunk,
        "story_line": story,
        "eliminated_aircraft": eliminated_aircraft,
    }


# ──────────────────────────────── Main entry ─────────────────────────────────

def resolve_surface_combat(
    attacker_taskforce: TaskForce,
    defender_taskforce: TaskForce,
    clouds: bool = False,
    night: bool = False,
    die_roll_fn: Callable[[], int] | None = None,
    # Position maps from UI (None = auto-assigned)
    attacker_positions: dict[Ship, str] | None = None,
    defender_positions: dict[Ship, str] | None = None,
    # Secret dice values 1-6 (default = 3)
    attacker_die: int = 3,
    defender_die: int = 3,
    # Gunnery target allocation {ship → target_ship}
    attacker_gunnery_targets: dict[Ship, Ship] | None = None,
    defender_gunnery_targets: dict[Ship, Ship] | None = None,
    # Torpedo target allocation {ship → target_ship}
    attacker_torpedo_targets: dict[Ship, Ship] | None = None,
    defender_torpedo_targets: dict[Ship, Ship] | None = None,
    # Legacy simple allocation kept for backward compat
    attacker_target_allocation: dict[Ship, Ship] | None = None,
) -> dict | None:
    """Resolve full Surface Attack Combat (§19) between two task forces.

    Returns a structured result dict, or None if combat cannot occur.
    """
    if attacker_taskforce is None or defender_taskforce is None:
        return None
    if not attacker_taskforce.ships or not defender_taskforce.ships:
        return None

    if die_roll_fn is None:
        die_roll_fn = lambda: random.randint(1, 6)

    # Build default positions when not supplied
    if attacker_positions is None:
        attacker_positions = assign_default_positions(
            attacker_taskforce.ships, attacker_taskforce.side
        )
    if defender_positions is None:
        defender_positions = assign_default_positions(
            defender_taskforce.ships, defender_taskforce.side
        )

    # Back-compat: treat legacy attacker_target_allocation as gunnery targets
    if attacker_target_allocation and not attacker_gunnery_targets:
        attacker_gunnery_targets = attacker_target_allocation

    bht = max(2, min(12, attacker_die + defender_die))

    att_side = getattr(attacker_taskforce, "side", "Allied")
    def_side = getattr(defender_taskforce, "side", "Allied")

    # Categorise ships by position (excluding sunk)
    att_gunnery  = [s for s in attacker_taskforce.ships if s.status != "Sunk" and attacker_positions.get(s) == POSITION_GUNNERY]
    att_torpedo  = [s for s in attacker_taskforce.ships if s.status != "Sunk" and attacker_positions.get(s) == POSITION_TORPEDO]
    def_gunnery  = [s for s in defender_taskforce.ships if s.status != "Sunk" and defender_positions.get(s) == POSITION_GUNNERY]
    def_torpedo  = [s for s in defender_taskforce.ships if s.status != "Sunk" and defender_positions.get(s) == POSITION_TORPEDO]

    # Targetable = not in screen
    att_targetable = [s for s in attacker_taskforce.ships if s.status != "Sunk" and attacker_positions.get(s) != POSITION_SCREEN]
    def_targetable = [s for s in defender_taskforce.ships if s.status != "Sunk" and defender_positions.get(s) != POSITION_SCREEN]

    if not att_targetable and not def_targetable:
        return None

    # ── Gunnery (simultaneous) ────────────────────────────────────────────────
    att_gunnery_result = _resolve_gunnery(
        att_gunnery, def_targetable, att_side, bht, die_roll_fn,
        attacker_gunnery_targets, BB_TYPES,
    )
    def_gunnery_result = _resolve_gunnery(
        def_gunnery, att_targetable, def_side, bht, die_roll_fn,
        defender_gunnery_targets, BB_TYPES,
    )

    attacker_taskforce.attacked_this_turn = bool(att_gunnery)
    defender_taskforce.attacked_this_turn = bool(def_gunnery)

    # ── Torpedo (ships sunk in gunnery cannot fire) ───────────────────────────
    att_torp_eligible = [
        s for s in att_torpedo
        if s.status != "Sunk" and not getattr(s, "torpedo_factor_used", False)
    ]
    def_torp_eligible = [
        s for s in def_torpedo
        if s.status != "Sunk" and not getattr(s, "torpedo_factor_used", False)
    ]

    att_torpedo_result = _resolve_torpedoes(
        att_torp_eligible, def_targetable, att_side, bht, night, die_roll_fn,
        attacker_torpedo_targets,
    )
    def_torpedo_result = _resolve_torpedoes(
        def_torp_eligible, att_targetable, def_side, bht, night, die_roll_fn,
        defender_torpedo_targets,
    )

    # ── Breakthrough ──────────────────────────────────────────────────────────
    breakthrough_result = _resolve_breakthrough(
        list(attacker_taskforce.ships),
        attacker_positions,
        list(defender_taskforce.ships),
        defender_positions,
        att_side,
        bht,
        die_roll_fn,
    )

    # ── Prune sunk ships ──────────────────────────────────────────────────────
    attacker_taskforce.ships = [s for s in attacker_taskforce.ships if s.status != "Sunk"]
    defender_taskforce.ships = [s for s in defender_taskforce.ships if s.status != "Sunk"]

    return {
        "bht": bht,
        "attacker_die": attacker_die,
        "defender_die": defender_die,
        "attacker_gunnery": att_gunnery_result,
        "defender_gunnery": def_gunnery_result,
        "attacker_torpedo": att_torpedo_result,
        "defender_torpedo": def_torpedo_result,
        "breakthrough": breakthrough_result,
        "attacker_destroyed": len(attacker_taskforce.ships) == 0,
        "defender_destroyed": len(defender_taskforce.ships) == 0,
        # Legacy keys for backward compat with existing combat results display
        "attacker": att_gunnery_result,
        "defender": def_gunnery_result,
    }
