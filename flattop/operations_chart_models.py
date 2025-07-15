from enum import Enum
from enum import Enum, auto

"""
Requirements Overview:

- A Task Force can have multiple ships, but at most one carrier.
- A Carrier can have multiple aircraft.
- A Base can have multiple aircraft.
- An Air Formation can have multiple aircraft and can be flying at either high or low altitude.
- An Air Operations Chart has 35 Air Formations and 14 Task Forces.

Rules Reference (from game_requirements.txt):
- 3.3.1: Air Formation counters (numbered 1–35) are placed in the Air Formation boxes on the Air Operation Charts with the corresponding numbers.
- 3.3.2: Task Force counters (numbered 1–14) are placed in the Task Force boxes on the Air Operations Charts with the corresponding numbers.
- 3.3.3: Ship counters are placed in the Task Force boxes in any manner within the dictates of rule 4.1 and the scenario OB.
- 3.3.4: Plane counters are placed in the Task Force boxes and base boxes in any manner within the dictates of rule 4.2 and the scenario OB.
"""


class AirOperationsChart:
    """
    Represents an Air Operations Chart containing Air Formations and Task Forces.

    Attributes:
        air_formations (dict): Mapping from number (1–35) to AirFormation.
        task_forces (dict): Mapping from number (1–14) to TaskForce.
        name (str): Optional name for the chart.
        description (str): Optional description for the chart.
    """
    def __init__(self, name=None, description=None, side="Allied"):
        self.name = name or "Air Operations Chart"
        self.description = description or ""
        self.side = side
        self.air_formations = {i: AirFormation(i, side=side) for i in range(1, 36)}
        self.task_forces = {i: TaskForce(i, side=side) for i in range(1, 15)}
        self.bases = dict()  # Mapping from base name to Base instance

    def get_air_formation(self, number):
        return self.air_formations.get(number)

    def get_task_force(self, number):
        return self.task_forces.get(number)

    def get_empty_formation_number(self):
        """
        Returns the number of the first AirFormation that has no aircraft assigned,
        or None if all are occupied.
        """
        for num, formation in self.air_formations.items():
            if not formation.aircraft:
                return num
        return None

    def get_all_empty_formation_numbers(self):
        """
        Returns a list of all AirFormation numbers that have no aircraft assigned.
        """
        return [num for num, formation in self.air_formations.items() if not formation.aircraft]

    def __repr__(self):
        return (f"AirOperationsChart(name={self.name}, "
                f"air_formations={list(self.air_formations.keys())}, "
                f"task_forces={list(self.task_forces.keys())})")

class TaskForce:
    """
    Represents a Task Force, which can contain multiple ships (including at most one carrier, one AV/CAV, and special handling for Japanese BBs with air factors).

    Rules enforced:
    - Allied TFs: max 15 ships; Japanese TFs: max 10 ships.
    - At most one carrier (CV/CVL) per TF.
    - At most one AV (or CAV) per TF.
    - Plane-carrying ships (CV, CVL, AV, CAV) must be in TFs 1–9.
    - TFs 10+ cannot contain plane-carrying ships.
    - Japanese BBs may carry one air factor, tracked separately.

Text from rule book
**4.1** Ships are placed in Task Forces (TFs) in any manner within the following rules:

- **4.1.1** Allied TFs can contain fifteen or fewer ships. Japanese TFs can contain ten or fewer ships. Even one ship is considered, and must be, a TF. Any ship types may be combined in any TF except for special restrictions on plane-carrying ships (see 4.1.3–4.1.6). All plane-carrying ships must be placed in TFs 1–9. TFs 10+ are for TFs that do not contain plane-carrying ships.
- **4.1.2** If a player has more than fourteen TFs, they can create others by drawing TF boxes on a separate piece of paper, labelling them as TFs fifteen and up, and placing ships in them.
- **4.1.3** No more than one CV (or CVL) can be placed in any one TF box. If a TF has more than one CV, the second CV is placed in a second TF box and the second TF counter is placed in the first TF box to show that the second CV is actually part of the first TF (and is not a TF by itself).
- **4.1.4** No more than one AV (or CAV) can be placed in any one TF box. If a TF has more than one AV, use the same procedure as in 4.1.3.
- **4.1.5** A TF box can have one CV (or CAV) in it, since the plane types they handle are different and it will be obvious which planes are on which ship.
- **4.1.6** Japanese BBs can each carry one Air Factor. They may be in any TF box, regardless of whether there is also a CV (or CVL), AV (or CAV), or combination of these ships in the same TF box. The Japanese player should keep track of an Air Factor on a BB in the Notes Section of the Air Record Sheet.

    """

    MAX_SHIPS_ALLIED = 15
    MAX_SHIPS_JAPANESE = 10
    PLANE_CARRYING_SHIP_TYPES = {"CV", "CVL", "AV", "CAV"}

    def __init__(self, number, name=None, side="Allied"):
        """
        Args:
            number (int): Task Force counter number (1–14).
            name (str, optional): Optional name for the Task Force.
            side (str): "Allied" or "Japanese".
        """
        self.number = number
        self.name = name or f"Task Force {number}"
        self.side = side
        self.ships = []
        self.japanese_bb_air_factors = {}  # {ship: air_factor_count}

    def add_ship(self, ship):
        if not isinstance(ship, Ship):
            raise TypeError("Expected a Ship instance")

        # Determine max ships based on side
        max_ships = self.MAX_SHIPS_ALLIED if self.side == "Allied" else self.MAX_SHIPS_JAPANESE
        if len(self.ships) >= max_ships:
            raise ValueError(f"{self.side} Task Force cannot have more than {max_ships} ships.")

        # Plane-carrying ship restrictions
        is_plane_carrier = getattr(ship, "type", None) in self.PLANE_CARRYING_SHIP_TYPES
        if is_plane_carrier and self.number > 9:
            raise ValueError("Plane-carrying ships must be placed in Task Forces 1–9.")

        # Only one carrier (CV or CVL)
        if getattr(ship, "type", None) in {"CV", "CVL"}:
            if any(getattr(s, "type", None) in {"CV", "CVL"} for s in self.ships):
                raise ValueError("A Task Force can only have one carrier (CV or CVL).")

        # Only one AV or CAV
        if getattr(ship, "type", None) in {"AV", "CAV"}:
            if any(getattr(s, "type", None) in {"AV", "CAV"} for s in self.ships):
                raise ValueError("A Task Force can only have one AV (or CAV).")

        # Prevent adding the same ship twice
        if ship in self.ships:
            raise ValueError("This ship is already in the Task Force.")

        self.ships.append(ship)

    def remove_ship(self, ship):
        """
        Removes a ship from the Task Force.

        Args:
            ship (Ship): The ship to remove.

        Raises:
            ValueError: If the ship is not in the Task Force.
        """
        if ship not in self.ships:
            raise ValueError("This ship is not in the Task Force.")
        self.ships.remove(ship)
        # Remove from Japanese BB air factors if present
        if ship in self.japanese_bb_air_factors:
            del self.japanese_bb_air_factors[ship]

    def assign_japanese_bb_air_factor(self, ship, air_factor_count=1):
        """
        Assigns air factors to a Japanese BB in this TF.
        """
        if self.side != "Japanese":
            raise ValueError("Only Japanese BBs can be assigned air factors.")
        if getattr(ship, "type", None) != "BB":
            raise ValueError("Only BBs can be assigned air factors.")
        if ship not in self.ships:
            raise ValueError("Ship must be part of this Task Force.")
        self.japanese_bb_air_factors[ship] = air_factor_count

    def get_carriers(self):
        return [ship for ship in self.ships if getattr(ship, "type", None) in {"CV", "CVL"}]

    def get_av_cav(self):
        return [ship for ship in self.ships if getattr(ship, "type", None) in {"AV", "CAV"}]

    @property
    def movement_factor(self):
        """
        Returns the movement factor of the Task Force, which is the lowest movement factor among all ships.
        Returns None if there are no ships in the Task Force.
        """
        max_move = 0
        if self.ships:
            max_move = min(getattr(ship, "move_factor", 0) for ship in self.ships)
        return max_move

    def __repr__(self):
        header = f"Task Force {self.number}: {self.name}\n"
        if not self.ships:
            return header + "(No ships assigned)"
        table = "Name           Type   Status      Attack  Defense  Move\n"
        table += "-" * 55 + "\n"
        for ship in self.ships:
            table += f"{ship.name:<15} {ship.type:<6} {ship.status:<10} {ship.attack_factor:<7} {ship.defense_factor:<8} {ship.move_factor:<4}\n"
        return header + table

class Base:
    def __init__(self, name=None, side="Allied", air_operations_config=None, air_operations_tracker=None):
        """
        Args:
            name (str, optional): Optional name for the Base.
        """
        self.name = name or "Base"
        self.air_operations_config = air_operations_config or AirOperationsConfiguration(name=f"{self.name} Air Operations Configuration", description=f"Configuration for {self.name} base")
        self.air_operations_tracker = air_operations_tracker or AirOperationsTracker(name=f"{self.name} Operations Chart", description=f"Operations chart for {self.name}", op_config=self.air_operations_config)
        self.side = side  # "Allied" or "Japanese"
        self.used_ready_factor = 0
        self.used_launch_factor = 0


    """
    #create a AirFormation for this base. To create an AirFormation the AirOperationsTracker status for the aircraft must be set to READY.
    - AirCraft must be in the READY status to be assigned to an AirFormation.
    - The AirFormation can be assigned to a specific AirFormation number (1–35).
    - The number of AirCraft, by type, in the AirFormation is determined by the count of each type of aircraft in the READY status.
    - The number of AirCraft, allocated to the AirFormation, is subtracted from the READY status in the AirOperationsTracker for the plane type.
    """
    def create_air_formation(self, number):
        """
        Creates an AirFormation for this base.

        Args:
            number (int): Air Formation counter number (1–35).

        Returns:
            AirFormation: The created AirFormation with aircraft from the READY status.
        """
        if number < 1 or number > 35:
            raise ValueError("Air Formation number must be between 1 and 35.")

        air_formation = AirFormation(number, name=f"{self.name} Air Formation {number}", side=self.side)

        # Move aircraft from READY status to the new AirFormation
        for ac in self.air_operations_tracker.ready:
            air_formation.add_aircraft(ac)
        # Clear the READY status in the AirOperationsTracker
        self.air_operations_tracker.ready.clear()
        
        return air_formation

    def reset_for_new_turn(self):
        self.used_ready_factor = 0
        self.used_launch_factor = 0
        

    def __repr__(self):
        return f"Base(name={self.name}, side={self.side} \n {self.air_operations_tracker}, \n {self.air_operations_config})"
    

class AirOperationsConfiguration:
    """
    Represents configuration parameters for an air operations facility (e.g., carrier, base).

    Attributes:
        name (str): Name of the configuration.
        description (str): Description of the configuration.
        maximum_capacity (int): Maximum number of aircraft that can be handled.
        launch_factors (int): Number of aircraft that can be launched per turn.
        ready_factors (int): Number of aircraft that can be readied per turn.
        plane_handling_type (str): Type of plane handling (e.g., "deck", "hangar", "base").
    """

    def __init__(
        self,
        name=None,
        description=None,
        maximum_capacity=1,
        launch_factor_min=1,
        launch_factor_normal=1,
        launch_factor_max=1,
        ready_factors=1,
        plane_handling_type="CV"  # e.g., "CV", "AV", "Base", "SP", "LP"
    ):
        self.name = name or "Air Operations Configuration"
        self.description = description or ""
        self.maximum_capacity = maximum_capacity  # Use property setter
        self.launch_factor_min = launch_factor_min
        self.launch_factor_normal = launch_factor_normal
        self.launch_factor_max = launch_factor_max
        self.ready_factors = ready_factors
        self.plane_handling_type = plane_handling_type

    def __repr__(self):
        return (f"{self.name} Air Operations Configuration, "
                f"\n Max Capacity={self.maximum_capacity}, "
                f" Launch Factor={self.launch_factor_normal}, "
                f" Ready Factor={self.ready_factors}, "
                f" Planes Handled={self.plane_handling_type}")
  
class AirFormation:
    """
    Represents an Air Formation, which can contain multiple aircraft.
    """
    def __init__(self, number, name=None, side="Allied", launch_hour=0, height="High"):
        """
        Args:
            number (int): Air Formation counter number (1–35).
            name (str, optional): Optional name for the Air Formation.
            side
            launch_time = 1-24, represents 24 hour clock.
        """
        self.number = number
        self.name = name or f"Air Formation {number}"
        self.aircraft = []
        self.side = side  # "Allied" or "Japanese"
        self.launch_hour = launch_hour
        self.height = "High"  # Default height, can be "High" or "Low"

    """
    Each turn reduces the range available for each aircraft type in the formation.
    If the available range for an aircraft reduces to zero then the aircraft have run out of fuel and are lost.
    """


    def add_aircraft(self, aircraft):
        if not isinstance(aircraft, Aircraft):
            raise TypeError("Expected an AirCraft instance")
        self.aircraft.append(aircraft)

    def remove_aircraft(self, aircraft):
        """
        Removes an aircraft from the Air Formation.

        Args:
            aircraft (AirCraft): The aircraft to remove.

        Raises:
            ValueError: If the aircraft is not in the Air Formation.
        """
        if aircraft not in self.aircraft:
            raise ValueError("This aircraft is not in the Air Formation.")
        self.aircraft.remove(aircraft)

    @property
    def movement_factor(self):
        """
        Returns the maximum movement factor for the AirFormation,
        which is the lowest movement factor among all aircraft in the formation.
        Returns 0 if there are no aircraft.
        """
        max_move = 0
        if self.aircraft:
            max_move = min(ac.move_factor for ac in self.aircraft)
        return max_move

    def __repr__(self):
        header = f"Air Formation {self.number}: {self.name}\n"
        if not self.aircraft:
            return header + "(No aircraft assigned)"
        table = "Type           Count\n"
        table += "-" * 22 + "\n"
        for ac in self.aircraft:
            table += f"{ac.type:<15} {ac.count}\n"
        return header + table

class AircraftCombatData:
    """
    An aircraft combat data class that holds information about aircraft combat capabilities.
    The combat types are air-to-air, level_bombing_high, level_bombing_low, dive_bombing and torpedo_bombing.
    Further, there are different attributes for attacks against ships and bases.
    Finally, there are general purpose bombs and armour piercing bombs.
    """

    def __init__(
        self,
        air_to_air=0,
        level_bombing_high_base_gp=0,
        level_bombing_high_base_ap=0,
        level_bombing_low_base_gp=0,
        level_bombing_low_base_ap=0,
        dive_bombing_base_gp=0,
        dive_bombing_base_ap=0,
        level_bombing_high_ship_gp=0,
        level_bombing_high_ship_ap=0,
        level_bombing_low_ship_gp=0,
        level_bombing_low_ship_ap=0,
        dive_bombing_ship_gp=0,
        dive_bombing_ship_ap=0,
        torpedo_bombing_ship=0
    ):
        self.air_to_air = air_to_air

        # Level bombing (high altitude)
        self.level_bombing_high_ship_gp = level_bombing_high_ship_gp
        self.level_bombing_high_ship_ap = level_bombing_high_ship_ap
        self.level_bombing_high_base_gp = level_bombing_high_base_gp
        self.level_bombing_high_base_ap = level_bombing_high_base_ap

        # Level bombing (low altitude)
        self.level_bombing_low_ship_gp = level_bombing_low_ship_gp
        self.level_bombing_low_ship_ap = level_bombing_low_ship_ap
        self.level_bombing_low_base_gp = level_bombing_low_base_gp
        self.level_bombing_low_base_ap = level_bombing_low_base_ap

        # Dive bombing
        self.dive_bombing_ship_gp = dive_bombing_ship_gp
        self.dive_bombing_ship_ap = dive_bombing_ship_ap
        self.dive_bombing_base_gp = dive_bombing_base_gp
        self.dive_bombing_base_ap = dive_bombing_base_ap

        # Torpedo bombing (ships only)
        self.torpedo_bombing_ship = torpedo_bombing_ship

    def __repr__(self):
        return (
            f"AircraftCombatData("
            f"air_to_air={self.air_to_air}, "
            f"level_bombing_high_ship_gp={self.level_bombing_high_ship_gp}, "
            f"level_bombing_high_ship_ap={self.level_bombing_high_ship_ap}, "
            f"level_bombing_high_base={self.level_bombing_high_base}, "
            f"level_bombing_low_ship_gp={self.level_bombing_low_ship_gp}, "
            f"level_bombing_low_ship_ap={self.level_bombing_low_ship_ap}, "
            f"level_bombing_low_base={self.level_bombing_low_base}, "
            f"dive_bombing_ship_gp={self.dive_bombing_ship_gp}, "
            f"dive_bombing_ship_ap={self.dive_bombing_ship_ap}, "
            f"dive_bombing_base={self.dive_bombing_base}, "
            f"torpedo_bombing_ship={self.torpedo_bombing_ship})"
        )


class Aircraft:
    """
    Represents an aircraft in the game.

    Attributes:
        type (str): The type of the aircraft (e.g., "Fighter", "Bomber").
    """
    
    def __init__(self, type, count=1, move_factor=5, range_factor=5, acd=AircraftCombatData()):
        self.type = type
        self.count = count  # Number of aircraft of this type
        self.move_factor = move_factor  # Movement factor for the aircraft
        self.range_factor = range_factor # The number of hours a plan can stay in tha air for.
        self.combat_data = acd  # Aircraft Combat Data instance
        self.range_remaining = range_factor #this is the remaining in air time available. Each turn increment reduces this.

    def __repr__(self):
        return f"AirCraft(type={self.type}, count={self.count}, move_factor={self.move_factor})"
    
    def copy(self):
        return Aircraft(self.type, self.count, self.move_factor, self.range_factor, self.combat_data)

class AircraftFactory:
    def __init__(self):
        pass

    @staticmethod
    def create(type, count=1):
        aircraft: Aircraft = None
        acd: AircraftCombatData = None
        match type:
            case AircraftType.A20:
                acd = AircraftCombatData(
                    air_to_air=3,
                    level_bombing_high_base_gp=5,
                    level_bombing_high_base_ap=2,
                    level_bombing_low_base_gp=8,
                    level_bombing_low_base_ap=3,
                    dive_bombing_base_gp=0,
                    dive_bombing_base_ap=0,
                    level_bombing_high_ship_gp=0,
                    level_bombing_high_ship_ap=1,
                    level_bombing_low_ship_gp=2,
                    level_bombing_low_ship_ap=5,
                    dive_bombing_ship_gp=0,
                    dive_bombing_ship_ap=0,
                    torpedo_bombing_ship=0
                )
                aircraft = Aircraft(type, count, 9, 6, acd)
            case AircraftType.AVENGER:
                acd = AircraftCombatData(
                    air_to_air=3,
                    level_bombing_high_base_gp=4,
                    level_bombing_high_base_ap=2,
                    level_bombing_low_base_gp=6,
                    level_bombing_low_base_ap=2,
                    dive_bombing_base_gp=0,
                    dive_bombing_base_ap=0,
                    level_bombing_high_ship_gp=0,
                    level_bombing_high_ship_ap=1,
                    level_bombing_low_ship_gp=2,
                    level_bombing_low_ship_ap=5,
                    dive_bombing_ship_gp=0,
                    dive_bombing_ship_ap=0,
                    torpedo_bombing_ship=6
                )
                aircraft = Aircraft(type, count, 7, 8, acd)
            case AircraftType.BEAUFIGHTER:
                acd = AircraftCombatData(
                    air_to_air=6,
                    level_bombing_high_base_gp=0,
                    level_bombing_high_base_ap=0,
                    level_bombing_low_base_gp=5,
                    level_bombing_low_base_ap=0,
                    dive_bombing_base_gp=0,
                    dive_bombing_base_ap=0,
                    level_bombing_high_ship_gp=0,
                    level_bombing_high_ship_ap=0,
                    level_bombing_low_ship_gp=1,
                    level_bombing_low_ship_ap=3,
                    dive_bombing_ship_gp=0,
                    dive_bombing_ship_ap=0,
                    torpedo_bombing_ship=0
                )
                aircraft = Aircraft(type, count, 9, 6, acd)
            case AircraftType.BEUFORT:
                acd = AircraftCombatData(
                    air_to_air=3,
                    level_bombing_high_base_gp=4,
                    level_bombing_high_base_ap=2,
                    level_bombing_low_base_gp=6,
                    level_bombing_low_base_ap=2,
                    dive_bombing_base_gp=0,
                    dive_bombing_base_ap=0,
                    level_bombing_high_ship_gp=0,
                    level_bombing_high_ship_ap=1,
                    level_bombing_low_ship_gp=2,
                    level_bombing_low_ship_ap=6,
                    dive_bombing_ship_gp=0,
                    dive_bombing_ship_ap=0,
                    torpedo_bombing_ship=7
                )
                aircraft = Aircraft(type, count, 7, 8)
            case AircraftType.B17:
                acd= AircraftCombatData(8,13,5,0,0,0,0,0,2,0,0,0,0,0)
                # B-17 has high air-to-air and level bombing capabilities
                aircraft = Aircraft(type, count, 8, 12, acd)
            case AircraftType.B25:
                acd= AircraftCombatData(4,8,3,11,5,0,0,0,1,3,7,0,0,0)
                aircraft = Aircraft(type, count, 9, 7, acd)
            case AircraftType.B26:
                acd= AircraftCombatData(4,6,2,10,4,0,0,0,1,2,5,0,0,5)
                aircraft = Aircraft(type, count, 10, 6,acd)
            case AircraftType.CATALINA:
                acd= AircraftCombatData(4,6,2,9,3,0,0,0,1,2,7,0,0,10)
                aircraft = Aircraft(type, count, 6, 20, acd)
            case AircraftType.DAUNTLESS:
                acd= AircraftCombatData(3,3,1,5,1,6,2,0,0,2,5,2,7,0)
                aircraft = Aircraft(type, count, 9, 6, acd)
            case AircraftType.DEVASTATOR:
                acd= AircraftCombatData(2,3,1,5,2,0,0,0,0,1,5,0,0,6)
                aircraft = Aircraft(type, count, 6, 5, acd)
            case AircraftType.HUDESON:
                acd= AircraftCombatData(3,3,1,6,2,0,0,0,1,1,4,0,0,0)
                aircraft = Aircraft(type, count, 7, 10, acd)
            case AircraftType.P38:
                acd= AircraftCombatData(7,0,0,5,0,0,0,0,0,1,0,0,0,0)   
                aircraft = Aircraft(type, count, 12, 5, acd)
            case AircraftType.P39:
                acd= AircraftCombatData(6,0,0,5,0,0,0,0,0,1,0,0,0,0)  
                aircraft = Aircraft(type, count, 11, 5, acd)
            case AircraftType.P40:
                acd= AircraftCombatData(7,0,0,4,0,0,0,0,0,1,0,0,0,0)  
                aircraft = Aircraft(type, count, 11, 5, acd)
            case AircraftType.WILDCAT:
                acd= AircraftCombatData(9,0,0,4,0,0,0,0,0,1,0,0,0,0)  
                aircraft = Aircraft(type, count, 8, 6, acd)
            #japanese
            # Betty is a bomber, so it has a different range factor)
            case AircraftType.BETTY:
                acd= AircraftCombatData(3,4,2,6,2,0,0,0,1,2,5,0,0,9)
                aircraft = Aircraft(type, count, 9, 10 , acd)
            # Dave is a float plane, so it has a different range factor)
            case AircraftType.DAVE:
                acd= AircraftCombatData(1,0,0,1,0,0,0,0,0,0,0,0,0,0)
                aircraft = Aircraft(type, count, 4, 6, acd)
            # Emily is a flying boat, so it has a different range factor)
            case AircraftType.EMILY:
                acd= AircraftCombatData(6,8,3,9,4,0,0,0,1,3,7,0,0,15)
                aircraft = Aircraft(type, count, 9, 24, acd)
            # Judy is a dive bomber)
            case AircraftType.JUDY:
                acd= AircraftCombatData(3,2,1,3,1,4,2,0,0,1,5,2,7,0)
                aircraft = Aircraft(type, count, 11, 6, acd)
            # Jake is a float plane, 
            case AircraftType.JAKE:
                acd= AircraftCombatData(1,0,0,1,0,0,0,0,0,0,0,0,0,0)
                aircraft = Aircraft(type, count, 5, 9, acd)
            # Kate is a torpedo bomber
            case AircraftType.KATE:
                acd= AircraftCombatData(2,4,2,6,2,0,0,0,1,2,6,0,0,10)
                aircraft = Aircraft(type, count, 7, 7, acd)
            # Mavis is a flying boat, 
            case AircraftType.MAVIS:
                acd= AircraftCombatData(5,6,2,7,3,0,0,0,1,2,6,0,0,15)
                aircraft = Aircraft(type, count, 8, 23, acd)
            # Nell is a bomber, 
            case AircraftType.NELL:
                acd= AircraftCombatData(3,4,2,6,2,0,0,0,1,2,4,0,0,9)
                aircraft = Aircraft(type, count, 8, 8 , acd)
            # Pete is a float plane, 
            case AircraftType.PETE:
                acd= AircraftCombatData(1,0,0,1,0,0,0,0,0,0,0,0,0,0)
                aircraft = Aircraft(type, count, 4, 6, acd)
            # Rufe is a float plane,
            case AircraftType.RUFE:
                acd= AircraftCombatData(6,0,0,3,0,0,0,0,0,1,0,0,0,0)
                aircraft = Aircraft(type, count, 9, 6, acd)
            # Val is a dive bomber
            case AircraftType.VAL:
                acd= AircraftCombatData(2,2,1,3,1,4,2,0,0,1,5,2,7,0)
                aircraft = Aircraft(type, count, 9, 7, acd)
            # Zero is a fighter, 
            case AircraftType.ZERO:
                acd= AircraftCombatData(9,0,0,3,0,0,0,0,0,1,0,0,0,0)
                aircraft = Aircraft(type, count, 10, 8, acd)
        return aircraft
            

class AircraftType(Enum):
    #Allied
    A20 = "A-20"
    AVENGER = "Avenger"
    BEAUFIGHTER = "Beaufigher"
    BEUFORT = "Beaufort"
    B17 = "B-17"
    B25 ="B-25"
    B26 = "B-26"
    CATALINA = "Catalina"
    DAUNTLESS = "Dauntless"
    DEVASTATOR = "Devastator"
    HUDESON = "Hudson"
    P38 = "P-38"
    P39 = "P-39"
    P40 = "P-40"
    WILDCAT = "Wildcat"
    #Japanese
    BETTY = "Betty"
    DAVE = "Dave"
    EMILY = "Emily"
    JUDY = "Judy"
    JAKE = "Jake"
    KATE = "Kate"
    MAVIS = "Mavis"
    NELL = "Nell"
    PETE = "Pete"
    RUFE = "Rufe"
    VAL = "Val"
    ZERO = "Zero"


class Ship:
    
    def __init__(self, name, type, status, attack_factor=0, defense_factor=0, move_factor=2):
        self.name = name
        self.type = type
        self.status = status
        self.attack_factor = attack_factor
        self.defense_factor = defense_factor
        self.move_factor = move_factor  # Default move factor for ships

    def __repr__(self):
        return f"Ship(name={self.name}, type={self.type}, status={self.status}, " \
               f"attack_factor={self.attack_factor}, defense_factor={self.defense_factor}, move_factor={self.move_factor})\n"


class Carrier(Ship):
    """
    Represents a carrier ship in the game.

    Attributes:
        type (str): The type of the carrier (e.g., "Aircraft Carrier").
        status (str): The status of the carrier (e.g., "operational", "damaged").
    """
    
    def __init__(self, name, type, status, attack_factor=0, defense_factor=0, move_factor=2):
        super().__init__(name, "CV", status, attack_factor, defense_factor, move_factor)
        #a carrier is in effect a ship with a base  
        self.base = Base(name=f"{name} Base")

    
    @property
    def air_operations(self):
        return self.base.air_operations_tracker
    
    @property
    def air_operations_config(self):
        return self.base.air_operations_config
    
    @air_operations_config.setter
    def air_operations_config(self, value : AirOperationsConfiguration):
        self.base.air_operations_config = value

               


class AirOperationsTracker:
    """
    The AirOperationTracker is used to manage planes at a Base.
    """
   
    def __init__(self, name , description, op_config):
        """
        Initializes an AirOperationsChart object.

        Args:
            name (str): The name of the chart.
            description (str): A brief description of the chart. e.g. Allied or Axis operations chart.
            op_config: AirOperationsConfiguration for the Tracker.
                """
        self.name = name
        self.description = description
        self.in_flight = []
        self.just_landed = []
        self.readying = []
        self.ready = [] 
        self.air_op_config=op_config

    def __repr__(self):
         return f"Piece(owner={self.name}, position={self.description})"
    
    def __str__(self):
        header = f"{self.name}\n{self.description}\n"
        table = "-" * 50 + "\n"
        
        # Add each status section
        table += "IN FLIGHT:\n"
        for ac in self.in_flight:
            table += f"  {ac.type:<15} Count: {ac.count}\n"
            
        table += "\nJUST LANDED:\n" 
        for ac in self.just_landed:
            table += f"  {ac.type:<15} Count: {ac.count}\n"
            
        table += "\nREADYING:\n"
        for ac in self.readying:
            table += f"  {ac.type:<15} Count: {ac.count}\n"
            
        table += "\nREADY:\n"
        for ac in self.ready:
            table += f"  {ac.type:<15} Count: {ac.count}\n"
            
        return header + table
    
    def total_aircraft_count(self):
        """
        Returns the total number of aircraft in all status arrays.
        """
        return (
            sum(ac.count for ac in self.in_flight) +
            sum(ac.count for ac in self.just_landed) +
            sum(ac.count for ac in self.readying) +
            sum(ac.count for ac in self.ready)
        )
        
    def set_operations_status(self, aircraft, status):
        """
        Sets an aircraft to the appropriate flight status list based on its status.
        Args:
            aircraft (AirCraft): The aircraft to update.
            status (AircraftStatus or str): The new status for the aircraft.
        """
        if not isinstance(aircraft, Aircraft):
            raise TypeError("Expected an AirCraft instance")

        # Accept both enum and string for status
        if isinstance(status, AircraftOperationsStatus):
            status_value = status.value
        elif isinstance(status, str):
            try:
                status_value = AircraftOperationsStatus(status).value
            except ValueError:
                raise ValueError(f"Invalid status string: {status}")
        else:
            raise TypeError("status must be an AircraftStatus or str")

        # Remove aircraft from all status lists before adding to the new one
        for status_list in [self.in_flight, self.just_landed, self.readying, self.ready]:
            if aircraft in status_list:
                status_list.remove(aircraft)

        # Add to the appropriate status list
        if status_value == AircraftOperationsStatus.IN_FLIGHT.value:
            self.in_flight.append(aircraft)
        elif status_value == AircraftOperationsStatus.JUST_LANDED.value:
            self.just_landed.append(aircraft)
        elif status_value == AircraftOperationsStatus.READYING.value:
            self.readying.append(aircraft)
        elif status_value == AircraftOperationsStatus.READY.value:
            self.ready.append(aircraft)
        else:
            raise ValueError("Invalid status. Must be one of: 'in_flight', 'just_landed', 'readying', 'ready'.")
    
class AircraftOperationsStatus(Enum):
        IN_FLIGHT = "in_flight"
        JUST_LANDED = "just_landed"
        READYING = "readying"
        READY = "ready"

   