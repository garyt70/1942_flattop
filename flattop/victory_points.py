"""
Victory Points tracking system for 1942 Flat Top.

Based on game requirements section 25:
- 25.1: Players gain points according to the Victory Points Table
- 25.2: Automatic Victory at certain point levels
- 25.3: Winner is player with most points (min 50 to win)
- 25.4: Aircraft losses worth 2 points (10 if unnecessary)
- 25.5: Transport unloading worth 3 points per turn (8 turns max)
- 12.6: Damage to ships that exit scored at game end
- 21.5: Victory Points for bases with LF <= 0 per turn
"""

from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


# Victory Points Table - Based on ship type and damage factor
# Format: {ship_type: points_per_damage_factor}
SHIP_VICTORY_POINTS = {
    "CV": 24,   # Carriers are most valuable (damage_factor=4, so 24*4=96 points when sunk)
    "CVL": 18,  # Light carriers (damage_factor=3, so 18*3=54 points when sunk)
    "BB": 20,   # Battleships (damage_factor=10, so 20*10=200 points when sunk)
    "CA": 12,   # Heavy cruisers (damage_factor=3, so 12*3=36 points when sunk)
    "CL": 8,    # Light cruisers (damage_factor=3, so 8*3=24 points when sunk)
    "DD": 6,    # Destroyers (damage_factor=1-2, so 6-12 points when sunk)
    "AV": 15,   # Seaplane tenders
    "CAV": 12,  # Seaplane cruisers
    "AP": 24,   # Transports (start at 24, reduced by 3 each turn unloading)
    "APD": 18,  # Fast transports
    "AO": 10,   # Oilers
    "PG": 5,    # Patrol gunboats
    "SS": 8,    # Submarines
}

# Aircraft victory points
AIRCRAFT_ELIMINATED_POINTS = 2
AIRCRAFT_UNNECESSARY_LOSS_POINTS = 10

# Base victory points per turn with LF <= 0
BASE_DAMAGED_POINTS_PER_TURN = 5

# Transport unloading
TRANSPORT_UNLOAD_POINTS = 3
TRANSPORT_MAX_UNLOAD_TURNS = 8


class VictoryPointsTracker:
    """Tracks victory points for both sides throughout the game."""
    
    def __init__(self):
        self.allied_points = 0
        self.japanese_points = 0
        self.point_history = []  # List of (turn, side, reason, points) tuples
        self.transport_unload_count = {}  # Maps transport name to unload count
    
    def get_points(self, side: str) -> int:
        """Get total victory points for a side."""
        if side == "Allied":
            return self.allied_points
        elif side == "Japanese":
            return self.japanese_points
        else:
            raise ValueError(f"Invalid side: {side}")
    
    def get_opponent_side(self, side: str) -> str:
        """Get the opponent's side."""
        return "Japanese" if side == "Allied" else "Allied"
    
    def award_points(self, side: str, points: int, reason: str, turn_number: int = None):
        """
        Award victory points to a side.
        
        Args:
            side: "Allied" or "Japanese"
            points: Number of points to award
            reason: Description of why points were awarded
            turn_number: Current turn number (optional)
        """
        if side == "Allied":
            self.allied_points += points
        elif side == "Japanese":
            self.japanese_points += points
        else:
            raise ValueError(f"Invalid side: {side}")
        
        self.point_history.append((turn_number, side, reason, points))
        logger.info(f"Awarded {points} VP to {side}: {reason}")
    
    def award_aircraft_eliminated(self, side: str, aircraft_type: str, count: int, 
                                  unnecessary: bool = False, turn_number: int = None):
        """
        Award points for aircraft eliminated.
        
        Args:
            side: Side that gets the points (opponent of aircraft owner)
            aircraft_type: Type of aircraft eliminated
            count: Number of aircraft eliminated
            unnecessary: True if aircraft lost unnecessarily (10 points each instead of 2)
            turn_number: Current turn number
        """
        points_per_aircraft = AIRCRAFT_UNNECESSARY_LOSS_POINTS if unnecessary else AIRCRAFT_ELIMINATED_POINTS
        total_points = count * points_per_aircraft
        reason = f"{count} {aircraft_type} eliminated" + (" (unnecessary loss)" if unnecessary else "")
        self.award_points(side, total_points, reason, turn_number)
    
    def award_ship_sunk(self, side: str, ship_name: str, ship_type: str, 
                       damage_factor: int, turn_number: int = None):
        """
        Award points for a ship sunk.
        
        Args:
            side: Side that gets the points (opponent of ship owner)
            ship_name: Name of the ship
            ship_type: Type of ship (CV, BB, CA, etc.)
            damage_factor: Ship's damage factor
            turn_number: Current turn number
        """
        base_points = SHIP_VICTORY_POINTS.get(ship_type, 10)
        total_points = base_points * damage_factor
        reason = f"Sunk {ship_type} {ship_name} (DF={damage_factor})"
        self.award_points(side, total_points, reason, turn_number)
    
    def award_ship_damaged(self, side: str, ship_name: str, ship_type: str, 
                          damage: int, damage_factor: int, turn_number: int = None):
        """
        Award points for ship damage (used when ship exits map).
        
        Args:
            side: Side that gets the points (opponent of ship owner)
            ship_name: Name of the ship
            ship_type: Type of ship
            damage: Current damage on ship
            damage_factor: Ship's damage factor
            turn_number: Current turn number
        """
        if damage <= 0:
            return
        
        base_points = SHIP_VICTORY_POINTS.get(ship_type, 10)
        # Points proportional to damage
        damage_ratio = damage / damage_factor
        total_points = int(base_points * damage_factor * damage_ratio)
        reason = f"Damaged {ship_type} {ship_name} ({damage}/{damage_factor} hits)"
        self.award_points(side, total_points, reason, turn_number)
    
    def award_base_damaged(self, side: str, base_name: str, turn_number: int = None):
        """
        Award points for a base with LF <= 0 for one turn.
        
        Args:
            side: Side that gets the points (opponent of base owner)
            base_name: Name of the base
            turn_number: Current turn number
        """
        self.award_points(side, BASE_DAMAGED_POINTS_PER_TURN, 
                         f"Base {base_name} inoperative (LF <= 0)", turn_number)
    
    def award_transport_unload(self, side: str, transport_name: str, 
                               turn_number: int = None) -> bool:
        """
        Award points for a transport unloading (max 8 turns).
        
        Args:
            side: Side that owns the transport (gets the points)
            transport_name: Name of the transport
            turn_number: Current turn number
            
        Returns:
            True if points were awarded, False if max turns reached
        """
        if transport_name not in self.transport_unload_count:
            self.transport_unload_count[transport_name] = 0
        
        if self.transport_unload_count[transport_name] >= TRANSPORT_MAX_UNLOAD_TURNS:
            logger.info(f"Transport {transport_name} has already unloaded max {TRANSPORT_MAX_UNLOAD_TURNS} turns")
            return False
        
        self.transport_unload_count[transport_name] += 1
        count = self.transport_unload_count[transport_name]
        self.award_points(side, TRANSPORT_UNLOAD_POINTS,
                         f"Transport {transport_name} unloading (turn {count}/{TRANSPORT_MAX_UNLOAD_TURNS})",
                         turn_number)
        return True
    
    def get_transport_remaining_value(self, transport_name: str, 
                                     transport_type: str = "AP") -> int:
        """
        Get remaining victory point value of a transport if sunk.
        Value decreases as it unloads.
        
        Args:
            transport_name: Name of the transport
            transport_type: Type (AP or APD)
            
        Returns:
            Victory point value if sunk
        """
        unload_count = self.transport_unload_count.get(transport_name, 0)
        base_value = SHIP_VICTORY_POINTS.get(transport_type, 24)
        
        # Reduce by 3 points per unload turn (proportional)
        remaining_ratio = 1.0 - (unload_count / TRANSPORT_MAX_UNLOAD_TURNS)
        return int(base_value * remaining_ratio)
    
    def check_automatic_victory(self, automatic_victory_level: int) -> Tuple[bool, str]:
        """
        Check if either side has achieved automatic victory.
        
        Args:
            automatic_victory_level: Point difference required for automatic victory
            
        Returns:
            (has_auto_victory, winning_side) tuple
        """
        point_diff = abs(self.allied_points - self.japanese_points)
        
        if point_diff >= automatic_victory_level:
            winner = "Allied" if self.allied_points > self.japanese_points else "Japanese"
            return True, winner
        
        return False, None
    
    def determine_winner(self, min_points_to_win: int = 50) -> str:
        """
        Determine the winner at game end.
        
        Args:
            min_points_to_win: Minimum points required to win (default 50)
            
        Returns:
            "Allied", "Japanese", or "Draw"
        """
        if self.allied_points < min_points_to_win and self.japanese_points < min_points_to_win:
            return "Draw"
        
        if self.allied_points > self.japanese_points:
            return "Allied"
        elif self.japanese_points > self.allied_points:
            return "Japanese"
        else:
            return "Draw"
    
    def get_point_summary(self) -> Dict[str, any]:
        """Get a summary of current victory points."""
        return {
            "allied_points": self.allied_points,
            "japanese_points": self.japanese_points,
            "point_difference": abs(self.allied_points - self.japanese_points),
            "leader": "Allied" if self.allied_points > self.japanese_points 
                     else "Japanese" if self.japanese_points > self.allied_points 
                     else "Tied",
            "history_count": len(self.point_history)
        }
    
    def get_recent_history(self, count: int = 10) -> List[Tuple]:
        """Get the most recent point awards."""
        return self.point_history[-count:]
    
    def to_dict(self) -> dict:
        """Serialize to dictionary for saving."""
        return {
            "allied_points": self.allied_points,
            "japanese_points": self.japanese_points,
            "point_history": self.point_history,
            "transport_unload_count": self.transport_unload_count
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'VictoryPointsTracker':
        """Deserialize from dictionary."""
        tracker = cls()
        tracker.allied_points = data.get("allied_points", 0)
        tracker.japanese_points = data.get("japanese_points", 0)
        tracker.point_history = data.get("point_history", [])
        tracker.transport_unload_count = data.get("transport_unload_count", {})
        return tracker
