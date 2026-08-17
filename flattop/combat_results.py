"""
Combat Results classes for tracking combat outcomes with explicit attacker/defender sides.

This module defines typed combat result classes that explicitly track which side
is the attacker (initiated combat) and which is the defender. This simplifies
victory point awarding and makes combat logic clearer.

Key principle: 
- Attacker = side that initiated combat
- Defender = side that was attacked
- VP awards: opponent gets points when you lose units
"""

from dataclasses import dataclass, field, asdict
from typing import List, Tuple, Optional, Dict, Any


@dataclass
class CombatResult:
    """Base class for all combat results with attacker/defender tracking."""
    attacker_side: str  # "Allied" or "Japanese" - who initiated combat
    defender_side: str  # "Japanese" or "Allied" - who was attacked
    
    def get_opponent_side(self, side: str) -> str:
        """Get the opponent's side."""
        if side == self.attacker_side:
            return self.defender_side
        elif side == self.defender_side:
            return self.attacker_side
        else:
            raise ValueError(f"Invalid side: {side}")


@dataclass
class AirToAirCombatResult(CombatResult):
    """
    Result of air-to-air combat.
    
    Attacker = side with interceptors that initiated combat
    Defender = side with escorts/bombers being intercepted
    
    Victory Points:
    - Defender gets points for attacker's interceptor losses
    - Attacker gets points for defender's escort/bomber losses
    """
    # Aircraft eliminated (aircraft_type, count) tuples
    interceptor_losses: List[Tuple[str, int]] = field(default_factory=list)  # Attacker's losses
    escort_losses: List[Tuple[str, int]] = field(default_factory=list)       # Defender's losses
    bomber_losses: List[Tuple[str, int]] = field(default_factory=list)       # Defender's losses
    
    # Story lines for UI display
    story_lines: List[str] = field(default_factory=list)
    summary: str = ""


@dataclass
class AntiAircraftCombatResult(CombatResult):
    """
    Result of anti-aircraft combat (taskforce or base AA fire).
    
    Attacker = side with bombers attacking
    Defender = side with AA defenses (taskforce or base)
    
    Victory Points:
    - Defender gets points for attacker's bomber losses
    """
    bomber_losses: List[Tuple[str, int]] = field(default_factory=list)  # Attacker's losses
    defender_name: str = ""  # Name of defending taskforce or base
    
    story_lines: List[str] = field(default_factory=list)
    summary: str = ""


@dataclass
class AirToShipCombatResult(CombatResult):
    """
    Result of air attack on ships.
    
    Attacker = side with bombers attacking
    Defender = side with ships being attacked
    
    Victory Points:
    - Attacker gets points for defender's ships sunk/damaged
    - Attacker gets points for defender's carrier aircraft lost (on sunk carriers)
    """
    ships_hit: List[Any] = field(default_factory=list)  # Ship objects that were hit
    ships_sunk: List[Any] = field(default_factory=list)  # Ship objects that were sunk
    carrier_aircraft_lost: List[Tuple[str, int]] = field(default_factory=list)  # Defender's aircraft
    
    story_lines: List[str] = field(default_factory=list)
    summary: str = ""


@dataclass
class AirToBaseCombatResult(CombatResult):
    """
    Result of air attack on a base.
    
    Attacker = side with bombers attacking
    Defender = side with base being attacked
    
    Victory Points:
    - Attacker gets points for defender's base aircraft lost
    - Points for base damage awarded at end-of-turn (not during combat)
    """
    base_name: str = ""
    base_aircraft_lost: List[Tuple[str, int]] = field(default_factory=list)  # Defender's aircraft
    base_damage: int = 0  # Hits on base
    
    story_lines: List[str] = field(default_factory=list)
    summary: str = ""


@dataclass
class SurfaceCombatResult(CombatResult):
    """
    Result of surface combat between taskforces.
    
    Attacker = side that initiated surface combat
    Defender = side that was attacked
    
    Victory Points:
    - Each side gets points for opponent's ships sunk
    - Each side gets points for opponent's carrier aircraft lost
    """
    attacker_ships_sunk: List[Any] = field(default_factory=list)  # Ship objects
    defender_ships_sunk: List[Any] = field(default_factory=list)  # Ship objects
    attacker_carrier_aircraft_lost: List[Tuple[str, int]] = field(default_factory=list)
    defender_carrier_aircraft_lost: List[Tuple[str, int]] = field(default_factory=list)
    
    # Additional combat details for display
    bht: int = 0
    attacker_die: int = 3
    defender_die: int = 3
    
    story_lines: List[str] = field(default_factory=list)
    summary: str = ""


@dataclass
class BattleResults:
    """
    Container for all combat results from a battle (all combat in one hex).
    
    Attacker = side that initiated the battle (piece that moved into hex)
    """
    attacker_side: str
    defender_side: str
    
    # Combat phases in order
    air_to_air: Optional[AirToAirCombatResult] = None
    taskforce_anti_aircraft: Optional[AntiAircraftCombatResult] = None
    base_anti_aircraft: Optional[AntiAircraftCombatResult] = None
    air_to_ship: Optional[List[AirToShipCombatResult]] = None
    air_to_base: Optional[AirToBaseCombatResult] = None
    surface_combat: Optional[SurfaceCombatResult] = None
    
    # Pre-combat counts for display
    pre_combat_counts: Dict[str, int] = field(default_factory=dict)
