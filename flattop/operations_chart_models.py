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
        self.can_observe = True
        self.observed_condition = 0
        self.has_radar = False  # Indicates if this Task Force has radar capabilities

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
    
    def reset_for_new_turn(self):
        """
        Resets the Task Force for a new turn.
        This can include resetting observed conditions, etc.
        """
        self.observed_condition = 0
        # Reset any other state as needed
        carrier_list = self.get_carriers()
        cv:Carrier
        for cv in carrier_list:
            cv.base.reset_for_new_turn()

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

    @property
    def can_attack(self):
        """
        Checks if any ship in the Task Force can attack.
        A ship can attack if it has an attack factor greater than 0.
        """
        #TODO: consider if there needs to be a setter to set if an attack has taken place
        for ship in self.ships:
            if getattr(ship, "attack_factor", 0) > 0:
                return True
        return False

    def __repr__(self):
        str_value = f"TaskForce : "
        if not self.ships:
            str_value += "(No ships assigned)"
            return str_value
        str_value += "\n".join(f" |{ship.name}" for ship in self.ships)
        if len(str_value) > 60:
            str_value = str_value[:57] + "..."
        return str_value

    def summary_str(self):
        header = f"Task Force {self.number}: {self.name}\n"
        if not self.ships:
            return header + "(No ships assigned)"
        table = "Name           Type   Status      Attack  AA      Move\n"
        table += "-" * 55 + "\n"
        for ship in self.ships:
            table += f"{ship.name:<15} {ship.type:<6} {ship.status:<10} {ship.attack_factor:<7} {ship.anti_air_factor:<8} {ship.move_factor:<4}\n"
        return header + table

class Base:
    def __init__(self, name=None, side="Allied", air_operations_config=None, air_operations_tracker=None):
        """
        Args:
            name (str, optional): Optional name for the Base.
        """
        self.name = name or "Base"
        self._air_operations_config = air_operations_config or AirOperationsConfiguration(name=f"{self.name} Air Operations Configuration", description=f"Configuration for {self.name} base")
        self.air_operations_tracker:AirOperationsTracker = air_operations_tracker or AirOperationsTracker(name=f"{self.name} Operations Chart", description=f"Operations chart for {self.name}", op_config=self._air_operations_config)
        self.side = side  # "Allied" or "Japanese"
        #self.used_ready_factor = 0
        #self.used_launch_factor = 0
        #TODO: consider refactor Base to become Runway and then Base and Carrier have a runway. A Base can then have damage and anti-aircraft
        self.damage = 0
        self.can_observe = True  # Base can observe air units at high altitude
        self.has_radar = False  # Base has no radar capabilities by default
        self.attacked_this_turn = False  # Track if the base has been attacked this turn
        self.observed_condition = 0


    """
    #create a AirFormation for this base. To create an AirFormation the AirOperationsTracker status for the aircraft must be set to READY.
    - AirCraft must be in the READY status to be assigned to an AirFormation.
    - The AirFormation can be assigned to a specific AirFormation number (1–35).
    - The number of AirCraft, by type, in the AirFormation is determined by the count of each type of aircraft in the READY status.
    - The number of AirCraft, allocated to the AirFormation, is subtracted from the READY status in the AirOperationsTracker for the plane type.
    """
    def create_air_formation(self, number, aircraft=None):
        """
        Creates an AirFormation for this base, adhering to ready/launch factor rules.

        Args:
            number (int): Air Formation counter number (1–35).
            aircraft (list, optional): List of aircraft to include in the formation.

        Returns:
            AirFormation: The created AirFormation with aircraft from the READY status.

        Rules:
            - Only aircraft in READY status can be assigned to an AirFormation.
            - The number of aircraft moved cannot exceed available ready/launch factors for this turn.
            - used_ready_factor and used_launch_factor are incremented accordingly.
            - If not enough ready/launch factors remain, only as many aircraft as allowed are moved.
        """
        if number < 1 or number > 35:
            raise ValueError("Air Formation number must be between 1 and 35.")

        # Determine how many aircraft can be launched this turn
        allowed = self.available_launch_factor_max - self.used_launch_factor
        moved = 0
        if allowed < 0 or not self.air_operations_tracker.ready:
            return None  # Cannot launch any more aircraft this turn
        
        # if aircraft is provided, use it and remove the appropriate aircraft from READY
        if aircraft:
            air_formation = AirFormation(number, name=f"{self.name} Air Formation {number}", side=self.side)
            for ac in aircraft:
                # Find all ready aircraft of the same type as ac
                ready_same_type = [r for r in self.air_operations_tracker.ready if r.type == ac.type]
                for r in ready_same_type:
                    to_move = min(ac.count, r.count, allowed)
                    if to_move > 0:
                        ac_to_add = ac.copy()
                        ac_to_add.count = to_move
                        air_formation.add_aircraft(ac_to_add)
                        r.count -= to_move
                        allowed -= to_move
                        if r.count <=0:
                            self.air_operations_tracker.ready.remove(r)
                        if allowed <= 0:
                            break
                        moved += to_move
                if allowed <= 0:
                    break
            
        else:


            # Using all the available Ready. Move up to 'allowed' aircraft from READY to the new AirFormation
            moved = 0
            to_remove = []
            for ac in self.air_operations_tracker.ready:
                if moved >= allowed:
                    break
                # Move the whole stack if possible, or partial if needed
                ac_to_add = ac.copy()
                if ac.count + moved > allowed:
                    ac_to_add.count = allowed - moved
                    ac.count -= ac_to_add.count
                else:
                    ac_to_add.count = ac.count
                    ac.count = 0
                air_formation.add_aircraft(ac_to_add)
                moved += ac_to_add.count
                if ac.count == 0:
                    to_remove.append(ac)
            # Remove aircraft with count 0 from READY
            for ac in to_remove:
                self.air_operations_tracker.ready.remove(ac)

        # Update base status
        self.used_launch_factor += moved

        if moved == 0:
            return None
        return air_formation

    @property
    def air_operations_config(self):
        return self._air_operations_config

    @property
    def anti_aircraft_factor(self):
        if self.air_operations_config.aaf > 0:
            return self.air_operations_config.aaf
        return 4 #default value

    @air_operations_config.setter
    def air_operations_config(self, value):
        self.air_operations_tracker.air_op_config = value
        self._air_operations_config = value

    @property   
    def used_ready_factor(self):
        return self.air_operations_tracker.used_ready_factor

    @used_ready_factor.setter
    def used_ready_factor(self, value):
        self.air_operations_tracker.used_ready_factor = value

    @property
    def used_launch_factor(self):
        return self.air_operations_tracker.used_launch_factor

    @used_launch_factor.setter
    def used_launch_factor(self, value):
        self.air_operations_tracker.used_launch_factor = value

    @property
    def available_ready_factor(self):
        return self._air_operations_config.ready_factors - self.damage
    
    @property
    def available_launch_factor_min(self):
        return self._air_operations_config.launch_factor_min - self.damage

    @property
    def available_launch_factor_max(self):
        return self._air_operations_config.launch_factor_max - self.damage * 4

    @property
    def available_launch_factor_normal(self):
        return self._air_operations_config.launch_factor_normal - self.damage * 2

    def reset_for_new_turn(self):
        self.used_ready_factor = 0
        self.used_launch_factor = 0
        self.attacked_this_turn = False

    def __repr__(self):
        return f"Base({self.name}, side={self.side})"

    def summary_str(self):
        return f"Base(name={self.name}, side={self.side} \n {self.air_operations_tracker}, \n {self._air_operations_config})"
    

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
        plane_handling_type="CV",  # e.g., "CV", "AV", "Base", "SP", "LP"
        aaf=5,
    ):
        self.name = name or "Air Operations Configuration"
        self.description = description or ""
        self.maximum_capacity = maximum_capacity  # Use property setter
        self.launch_factor_min = launch_factor_min
        self.launch_factor_normal = launch_factor_normal
        self.launch_factor_max = launch_factor_max
        self.ready_factors = ready_factors
        self.plane_handling_type = plane_handling_type
        self.aaf = aaf  # Anti-Aircraft Factor

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
        self.can_observe = True
        self.observed_condition = 0

    """
    Each turn reduces the range available for each aircraft type in the formation.
    If the available range for an aircraft reduces to zero then the aircraft have run out of fuel and are lost.
    """


    def add_aircraft(self, aircraft):
        if not isinstance(aircraft, Aircraft):
            raise TypeError("Expected an Aircraft instance")
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
    
    @property
    def range_remaining(self):
        """
        Returns the remaining range for the AirFormation,
        which is the lowest remaining range among all aircraft in the formation.
        Returns 0 if there are no aircraft.
        """
        min_range = float('inf')
        if self.aircraft:
            min_range = min(ac.range_remaining for ac in self.aircraft)
        return min_range

    @property
    def can_attack(self):
        """
        loop through the aircraft in the formation and check if any of them can attack.
        If they are bomber formation, they can attack if they have armament
        if they are an interceptor they can always attack other aircraft
        """
        for ac in self.aircraft:
            if ac.armament or ac.is_interceptor:
                return True
        return False
    
    def reset_for_new_turn(self):
        self.observed_condition = 0

    def __repr__(self):
        str_value = "AirFormation : "
        if not self.aircraft:
            return str_value + "(No aircraft assigned)"
        for ac in self.aircraft:
            str_value += f" |{ac.type.value}({ac.count})"
        return str_value
    
    def summary_str(self):
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
        self.armament = None  # Placeholder for any armament data, GP, AP, Torpedo, etc.
        self.height = "Low"  # Default height, can be "High" or "Low"
        self.attack_type = "Level"  # Default attack type


    def __repr__(self):
        return f"Aircraft(type={self.type.value}, count={self.count}, move_factor={self.move_factor})"
    
    def copy(self):
        ac = Aircraft(self.type, self.count, self.move_factor, self.range_factor, self.combat_data)
        ac.armament = self.armament  # Copy armament if it exists
        ac.range_remaining = self.range_remaining  # Copy remaining range
        return ac
    
    @property
    def is_bomber(self):
        """
        Returns True if the aircraft is a bomber, False otherwise.
        """
        if self.armament:
            return True

        if not self.is_interceptor:
            return True
        
        return False
    
    @property
    def is_interceptor(self):
        """
        Returns True if the aircraft is an interceptor, False otherwise.
        """
        return self.type in {AircraftType.ZERO, 
                             AircraftType.P40, 
                             AircraftType.BEAUFIGHTER, 
                             AircraftType.WILDCAT,
                             AircraftType.P39,
                             AircraftType.P40,
                             AircraftType.P38,}

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
    
    def __init__(self, name, type, status, gunnery_factor=0, anti_air_factor=0, move_factor=2, damage_factor=1):
        self.name = name
        self.type = type
        self.status = status
        self.attack_factor = gunnery_factor
        self.anti_air_factor = anti_air_factor
        self.move_factor = move_factor  # Default move factor for ships
        self.damage_factor = damage_factor
        self.damage = 0

    def __repr__(self):
        return f"Ship(name={self.name}, type={self.type}, status={self.status}, damage={self.damage}" \
               f"attack_factor={self.attack_factor}, aa_factor={self.anti_air_factor}, move_factor={self.move_factor})\n"


class Carrier(Ship):
    """
    Represents a carrier ship in the game.

    Attributes:
        type (str): The type of the carrier (e.g., "Aircraft Carrier").
        status (str): The status of the carrier (e.g., "operational", "damaged").
    """
    
    def __init__(self, name, type, status, attack_factor=0, anti_air_factor=0, move_factor=2, damage_factor=4):
        #a carrier is in effect a ship with a base  
        self.base = Base(name=f"{name} Base")
        self.has_radar = False  # Carriers do not have radar by default 
        super().__init__(name, "CV", status, attack_factor, anti_air_factor, move_factor, damage_factor)
        
        

    
    @property
    def air_operations(self):
        return self.base.air_operations_tracker
    
    @property
    def air_operations_config(self):
        return self.base.air_operations_config

    @air_operations_config.setter
    def air_operations_config(self, value : AirOperationsConfiguration):
        self.base.air_operations_config = value

    @property
    def damage(self):
        return self.base.damage
    
    @damage.setter
    def damage(self, value):
        self.base.damage = value  # Sync damage with the base


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
        self.used_ready_factor = 0  # Used to track how many ready factors have been used this turn
        self.used_launch_factor = 0  # Used to track how many launch factors have been used this turn

    def __repr__(self):
         return f"AirOperationsTracker(owner={self.name}, position={self.description})"
    
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
    
    def _operation_status_add_aircraft(self, to_aircraft:Aircraft, status_list:list[Aircraft]):
        append_rather_than_add = True
        for ac in status_list:
            if ac.type == to_aircraft.type:
                ac.count += to_aircraft.count
                append_rather_than_add = False
                break
        if append_rather_than_add:
            status_list.append(to_aircraft)

    def set_operations_status(self, to_aircraft: Aircraft, status, from_aircraft: Aircraft = None):
        """
        Sets an aircraft to the appropriate flight status list based on its status.
        Args:
            aircraft (AirCraft): The aircraft to update.
            status (AircraftStatus or str): The new status for the aircraft.
        """
        if not isinstance(to_aircraft, Aircraft):
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

        #landing doesn't use ready factors and so can go ahead.
        if status_value == AircraftOperationsStatus.JUST_LANDED.value:
            # Check if an aircraft of the same type already exists in just_landed
            self._operation_status_add_aircraft(to_aircraft, self.just_landed)

        if self.used_ready_factor > self.air_op_config.ready_factors:
            # Handle exceeding ready factors (e.g., by limiting the number of ready aircraft)
            print("Exceeded ready factors")
            return

        if from_aircraft:
            from_aircraft.count -= to_aircraft.count
            self.used_ready_factor += to_aircraft.count

        # Add to the appropriate status list
        if status_value == AircraftOperationsStatus.IN_FLIGHT.value:
            self.in_flight.append(to_aircraft)
        elif status_value == AircraftOperationsStatus.READYING.value:
            self._operation_status_add_aircraft(to_aircraft, self.readying)

            if from_aircraft and from_aircraft in self.just_landed and from_aircraft.count <= 0:
                # If moving from just landed, remove from just landed
                self.just_landed.remove(from_aircraft)
        elif status_value == AircraftOperationsStatus.READY.value:
            to_aircraft.range_remaining = to_aircraft.range_factor  # Reset range remaining when aircraft is ready
            self._operation_status_add_aircraft(to_aircraft, self.ready)
            if from_aircraft and from_aircraft in self.readying and from_aircraft.count <= 0:
                self.readying.remove(from_aircraft)
        


class AircraftOperationsStatus(Enum):
        IN_FLIGHT = "in_flight"
        JUST_LANDED = "just_landed"
        READYING = "readying"
        READY = "ready"


class JapaneseShipFactory:
    def __init__(self):
        pass

    @staticmethod
    def create(name):
        ship: Ship = None
        match name:
            
            case "Akagi" | "Kaga":
                ship = Carrier(name, "CV", "operational", 1, 4, 2, 6)
            case "Soryu" | "Hiryu":
                ship = Carrier(name, "CV", "operational", 1, 4, 2, 5)
            case "Shokaku":
                ship = Carrier(name, "CV", "operational", 1, 3, 2, 4)
            case "Zuikaku" | "Shokaku":

                air_ops_config = AirOperationsConfiguration(
                    name=name,
                    description=f"Configuration for air operations on {name}",
                    maximum_capacity=28,
                    launch_factor_min=3,
                    launch_factor_normal=10,
                    launch_factor_max=20,
                    ready_factors=8,
                    plane_handling_type="CV"
                )
                ship = Carrier(name, "CV", "operational", 1, 4, 1, 5)   
                ship.air_operations_config = air_ops_config
                ship = Carrier(name, "CV", "operational", 1, 5, 2, 6)
            case "Hiyo" | "Junyo":
                air_ops_config = AirOperationsConfiguration(
                    name=name,
                    description=f"Configuration for air operations on {name}",
                    maximum_capacity=18,
                    launch_factor_min=3,
                    launch_factor_normal=7,
                    launch_factor_max=14,
                    ready_factors=6,
                    plane_handling_type="CV"
                )
                ship = Carrier(name, "CV", "operational", 1, 4, 1, 5)   
                ship.air_operations_config = air_ops_config
            case "Ryujo" | "Zuiho":
                air_ops_config = AirOperationsConfiguration(
                    name=name,
                    description=f"Configuration for air operations on {name}",
                    maximum_capacity=16,
                    launch_factor_min=2,
                    launch_factor_normal=5,
                    launch_factor_max=10,
                    ready_factors=4,
                    plane_handling_type="CV"
                )
                ship = Carrier(name, "CV", "operational", 1, 3, 2, 4)   
                ship.air_operations_config = air_ops_config
            case "Shoho" | "Hosho":
                air_ops_config = AirOperationsConfiguration(
                    name=name,
                    description=f"Configuration for air operations on {name}",
                    maximum_capacity=10,
                    launch_factor_min=2,
                    launch_factor_normal=4,
                    launch_factor_max=8,
                    ready_factors=4,
                    plane_handling_type="CV"
                )
                ship = Carrier(name, "CV", "operational", 1, 2, 2, 3)
                ship.air_operations_config = air_ops_config
            case "Yamato" | "Musashi":
                ship = Ship(name, "BB", "operational", 28, 4, 2, 18)
            case "Kirishima" | "Hiei" | "Haruna" | "Kongo" | "Fuso":
                ship = Ship(name, "BB", "operational", 12, 3, 2, 10)
            case  "Hyuga" | "Ise" | "Fuso" | "Yamashiro":
                ship = Ship(name, "BB", "operational", 15, 3, 1, 11)
            case "Nagato" | "Mutsu":
                ship = Ship(name, "BB", "operational", 18, 3, 1, 12)
            case "Yuru" | "Isuzu" | "Jintsu" | "Nagura" | "Sendai" | "Abukuma" | "Tama":
                ship = Ship(name, "CL", "operational", 2, 1, 2, 4)
            case "Takao" | "Atago" | "Maya" | "Chokai" | "Haguro" | "Kumano" | "Suzuya" | "Nachi" | "Myoko":
                ship = Ship(name, "CA", "operational", 6, 2, 2, 6)
            case "Kinugasa" | "Furutaka" | "Aoba" | "Kako" | "Ashigara" | "Mikuma" | "Aoba":
                ship = Ship(name, "CA", "operational", 4, 2, 2, 5)
            case "Chikuma" | "Tatsuta" | "Tone":
                ship = Ship(name, "CAV", "operational", 3, 2, 2, 6)
            case "Kamikawa" | "Chitose":
                ship = Ship(name, "AV", "operational", 1, 2, 2, 3)

        if ship is None:
            raise ValueError(f"Unknown Japanese ship name: {name}")
        return ship

class AlliedShipFactory:
    def __init__(self):
        pass

    @staticmethod
    def create(name):
        ship: Ship = None
        match name:
            case "Lexington":
                air_ops_config = AirOperationsConfiguration(
                    name="Lexington",
                    description="Configuration for air operations on Lexington",
                    maximum_capacity=30,
                    launch_factor_min=3,
                    launch_factor_normal=12,
                    launch_factor_max=24,
                    ready_factors=8,
                    plane_handling_type="CV"
                )
                ship = Carrier("Lexington", "CV", "operational", 1, 4, 2, 6)
                ship.air_operations_config = air_ops_config
            case "Yorktown":
                air_ops_config = AirOperationsConfiguration(
                    name="Yorktown",
                    description="Configuration for air operations on Yorktown",
                    maximum_capacity=30,
                    launch_factor_min=3,
                    launch_factor_normal=11,
                    launch_factor_max=22,
                    ready_factors=9,
                    plane_handling_type="CV"
                )
                ship = Carrier("Yorktown", "CV", "operational", 1, 4, 2, 5)
                ship.air_operations_config = air_ops_config
            case "Enterprise":
                air_ops_config = AirOperationsConfiguration(
                    name="Enterprise",
                    description="Configuration for air operations on Enterprise",
                    maximum_capacity=33,
                    launch_factor_min=3,
                    launch_factor_normal=11,
                    launch_factor_max=22,
                    ready_factors=9,
                    plane_handling_type="CV"
                )
                ship = Carrier("Enterprise", "CV", "operational", 1, 7, 2, 7)
                ship.air_operations_config = air_ops_config
            case "Hornet":
                air_ops_config = AirOperationsConfiguration(
                    name="Hornet",
                    description="Configuration for air operations on Hornet",
                    maximum_capacity=33,
                    launch_factor_min=3,
                    launch_factor_normal=11,
                    launch_factor_max=22,
                    ready_factors=9,
                    plane_handling_type="CV"
                )
                ship = Carrier("Hornet", "CV", "operational", 1, 5, 2, 7)
                ship.air_operations_config = air_ops_config
            case "Saratoga":
                air_ops_config = AirOperationsConfiguration(
                    name="Saratoga",
                    description="Configuration for air operations on Saratoga",
                    maximum_capacity=32,
                    launch_factor_min=3,
                    launch_factor_normal=12,
                    launch_factor_max=24,
                    ready_factors=8,
                    plane_handling_type="CV"
                )
                ship = Carrier("Saratoga", "CV", "operational", 1, 5, 2, 8)
                ship.air_operations_config = air_ops_config

            case "Wasp":
                air_ops_config = AirOperationsConfiguration(
                    name="Wasp",
                    description="Configuration for air operations on Wasp",
                    maximum_capacity=28,
                    launch_factor_min=3,
                    launch_factor_normal=10,
                    launch_factor_max=20,
                    ready_factors=7,
                    plane_handling_type="CV"
                )
                ship = Carrier("Wasp", "CV", "operational", 1, 5, 2, 6)
                ship.air_operations_config = air_ops_config
            case "Ranger":
                ship = Ship("Ranger", "CVL", "operational", 1, 3, 2, 4)
            case "N. Carolina" | "Washington":
                ship = Ship(name, "BB", "operational", 25, 7, 2, 15)
            case "S. Dakota":
                ship = Ship("S. Dakota", "BB", "operational", 25, 9, 2, 15) 
            case "Colorado" | "Idaho" | "Maryland" | "Mississippi" | "Tennessee" | "New Mexico":
                ship = Ship(name, "BB", "operational", 20, 3, 1, 11)
            case "Indiana":
                ship = Ship(name, "BB", "operational", 25, 7, 2, 15)
            case "Arizona" | "Nevada" | "Oklahoma" | "Pennsylvania":
                ship = Ship(name, "BB", "operational", 18, 3, 1, 10)
            case "W. Virgina":
                ship = Ship(name, "BB", "operational", 22, 3, 1, 15)
            case "Vincennes" | "Houston" | "Quincy" | "Louisville" | "Portland" | "Astoria" | "Chicago" | "Northampton" | "New Orleans" | "Chester" | "Nashville":
                ship = Ship(name, "CA", "operational", 4, 2, 2, 5)
            case "Pensacola" | "Indianapolis" | "Minneapolis" | "San Francisco":
                ship = Ship(name, "CA", "operational", 3, 2, 2, 3)
            case "Helena" | "Nashville" | "Honolulu" | "St. Louis":
                ship = Ship(name, "CL", "operational", 4, 2, 2, 5)
            case "Hobart":
                ship = Ship(name, "CL", "operational", 3, 1, 2, 4)
            case "San Diego" | "San Juan" | "Juneau" | "Atlanta":
                ship = Ship(name, "CL", "operational", 2, 3, 2, 4)
            case "Detroit" | "Raleigh":
                ship = Ship(name, "CL", "operational", 2, 1, 2, 4)
            case "Australia":
                ship = Ship(name, "CA", "operational", 4, 1, 2, 5)
            case "Salt Lake City":
                ship = Ship(name, "CA", "operational", 5, 2, 2, 5)
            
        if ship is None:
            raise ValueError(f"Unknown Allied ship name: {name}")

        return ship

