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

from dataclasses import dataclass, field
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "type": self.__class__.__name__,
            "attacker_side": self.attacker_side,
            "defender_side": self.defender_side
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CombatResult':
        """Create instance from dictionary."""
        raise NotImplementedError("Subclasses must implement from_dict")


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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = super().to_dict()
        result.update({
            "interceptor_losses": self.interceptor_losses,
            "escort_losses": self.escort_losses,
            "bomber_losses": self.bomber_losses,
            "story_lines": self.story_lines,
            "summary": self.summary
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AirToAirCombatResult':
        """Create instance from dictionary."""
        return cls(
            attacker_side=data["attacker_side"],
            defender_side=data["defender_side"],
            interceptor_losses=data.get("interceptor_losses", []),
            escort_losses=data.get("escort_losses", []),
            bomber_losses=data.get("bomber_losses", []),
            story_lines=data.get("story_lines", []),
            summary=data.get("summary", "")
        )


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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = super().to_dict()
        result.update({
            "bomber_losses": self.bomber_losses,
            "defender_name": self.defender_name,
            "story_lines": self.story_lines,
            "summary": self.summary
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AntiAircraftCombatResult':
        """Create instance from dictionary."""
        return cls(
            attacker_side=data["attacker_side"],
            defender_side=data["defender_side"],
            bomber_losses=data.get("bomber_losses", []),
            defender_name=data.get("defender_name", ""),
            story_lines=data.get("story_lines", []),
            summary=data.get("summary", "")
        )


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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = super().to_dict()
        result.update({
            "ships_hit": [{"name": getattr(s, "name", ""), "type": getattr(s, "type", "")} for s in self.ships_hit],
            "ships_sunk": [{"name": getattr(s, "name", ""), "type": getattr(s, "type", ""), 
                           "damage_factor": getattr(s, "damage_factor", 1)} for s in self.ships_sunk],
            "carrier_aircraft_lost": self.carrier_aircraft_lost,
            "story_lines": self.story_lines,
            "summary": self.summary
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AirToShipCombatResult':
        """Create instance from dictionary (note: ship objects not fully restored)."""
        return cls(
            attacker_side=data["attacker_side"],
            defender_side=data["defender_side"],
            ships_hit=[],  # Ship objects require full reconstruction
            ships_sunk=[],
            carrier_aircraft_lost=data.get("carrier_aircraft_lost", []),
            story_lines=data.get("story_lines", []),
            summary=data.get("summary", "")
        )


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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = super().to_dict()
        result.update({
            "base_name": self.base_name,
            "base_aircraft_lost": self.base_aircraft_lost,
            "base_damage": self.base_damage,
            "story_lines": self.story_lines,
            "summary": self.summary
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AirToBaseCombatResult':
        """Create instance from dictionary."""
        return cls(
            attacker_side=data["attacker_side"],
            defender_side=data["defender_side"],
            base_name=data.get("base_name", ""),
            base_aircraft_lost=data.get("base_aircraft_lost", []),
            base_damage=data.get("base_damage", 0),
            story_lines=data.get("story_lines", []),
            summary=data.get("summary", "")
        )


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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = super().to_dict()
        result.update({
            "attacker_ships_sunk": [{"name": getattr(s, "name", ""), "type": getattr(s, "type", ""),
                                     "damage_factor": getattr(s, "damage_factor", 1)} for s in self.attacker_ships_sunk],
            "defender_ships_sunk": [{"name": getattr(s, "name", ""), "type": getattr(s, "type", ""),
                                     "damage_factor": getattr(s, "damage_factor", 1)} for s in self.defender_ships_sunk],
            "attacker_carrier_aircraft_lost": self.attacker_carrier_aircraft_lost,
            "defender_carrier_aircraft_lost": self.defender_carrier_aircraft_lost,
            "bht": self.bht,
            "attacker_die": self.attacker_die,
            "defender_die": self.defender_die,
            "story_lines": self.story_lines,
            "summary": self.summary
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SurfaceCombatResult':
        """Create instance from dictionary (note: ship objects not fully restored)."""
        return cls(
            attacker_side=data["attacker_side"],
            defender_side=data["defender_side"],
            attacker_ships_sunk=[],  # Ship objects require full reconstruction
            defender_ships_sunk=[],
            attacker_carrier_aircraft_lost=data.get("attacker_carrier_aircraft_lost", []),
            defender_carrier_aircraft_lost=data.get("defender_carrier_aircraft_lost", []),
            bht=data.get("bht", 0),
            attacker_die=data.get("attacker_die", 3),
            defender_die=data.get("defender_die", 3),
            story_lines=data.get("story_lines", []),
            summary=data.get("summary", "")
        )


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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "attacker_side": self.attacker_side,
            "defender_side": self.defender_side,
            "air_to_air": self.air_to_air.to_dict() if self.air_to_air else None,
            "taskforce_anti_aircraft": self.taskforce_anti_aircraft.to_dict() if self.taskforce_anti_aircraft else None,
            "base_anti_aircraft": self.base_anti_aircraft.to_dict() if self.base_anti_aircraft else None,
            "air_to_ship": [r.to_dict() for r in self.air_to_ship] if self.air_to_ship else None,
            "air_to_base": self.air_to_base.to_dict() if self.air_to_base else None,
            "surface_combat": self.surface_combat.to_dict() if self.surface_combat else None,
            "pre_combat_counts": self.pre_combat_counts
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BattleResults':
        """Create instance from dictionary."""
        return cls(
            attacker_side=data["attacker_side"],
            defender_side=data["defender_side"],
            air_to_air=AirToAirCombatResult.from_dict(data["air_to_air"]) if data.get("air_to_air") else None,
            taskforce_anti_aircraft=AntiAircraftCombatResult.from_dict(data["taskforce_anti_aircraft"]) if data.get("taskforce_anti_aircraft") else None,
            base_anti_aircraft=AntiAircraftCombatResult.from_dict(data["base_anti_aircraft"]) if data.get("base_anti_aircraft") else None,
            air_to_ship=[AirToShipCombatResult.from_dict(r) for r in data["air_to_ship"]] if data.get("air_to_ship") else None,
            air_to_base=AirToBaseCombatResult.from_dict(data["air_to_base"]) if data.get("air_to_base") else None,
            surface_combat=SurfaceCombatResult.from_dict(data["surface_combat"]) if data.get("surface_combat") else None,
            pre_combat_counts=data.get("pre_combat_counts", {})
        )
