"""Observation rules for the Flattop game.
This module contains the logic for observing units on the mapboard and determining their visibility.

To implement the observation rules, we follow the original board game rules from Avalon Hill's "Flat Top" game.
The rules cover how units can observe each other, the effects of weather conditions on observation, and
the conditions under which units must be placed on the mapboard.
The rules also specify how to handle different types of units, including Air Formations and Task Forces (TFs),
and how to report the observed units' details based on the Condition Numbers.

# Core logic to implement observation rules for Flattop

Display of Pieces on the mapboard (Desktop UI):
- Pieces are displayed on the mapboard when they are observed.
- Pieces are marked as observed when they are placed on the mapboard.
- Pieces that are no longer observed at the end of the turn are removed from the mapboard (Desktop UI).
- For debugging purposes, it should be possible to display all pieces on the mapboard, regardless of observation status.

# 1. Determine if a unit can attempt observation:
#    - Air Formations must declare intent and roll on the Search Table (with modifiers for weather).
#    - TFs, bases, and coastwatchers can always observe (no die roll needed).
#    - Units in Storm hexes cannot observe or be observed.

# 2. When a unit moves into a hex:
#    - Check if any enemy units (TFs, Air Formations, bases, coastwatchers) are within observation range.
#    - If so, apply the Observation Table to determine the Condition Number (1, 2, or 3).
#    - Report observed units' details according to the Condition Number.

# 3. Place observed units on the mapboard immediately. A Piece becomes visible on the desktop UI. The Piece is also marked as observed.
#    - Use generic counters (TF or Air Formation) as required.
#    - If a unit is no longer observed at end of turn, remove it from the mapboard (Desktop UI).

# 4. Radar-equipped units:
#    - May observe enemy air units at high altitude up to 3 hexes away, regardless of weather (except Storm).
#    - Radar does not reveal altitude unless Condition Number is 3.

# 5. Coastwatchers:
#    - Can observe planes over land/partial-land hexes of their island and adjacent sea hexes.
#    - Cannot observe planes in hexes with enemy bases.

# 6. Observation reporting (When "display" menu option selected the following rules apply):
#    - Condition 1: Only present and type (TF or Air Formation) is reported. 
#    - Condition 2: Number of units, classes, and total ships/planes (with ±50% fudge adjustment allowed).
#    - Condition 3: Exact numbers and classes of ships/planes, but not names (names are only possible when attack takes place).

# 7. Special cases:
#    - Planes in TF/base boxes only observed at Condition 3.
#    - Readying planes are never observed.
#    - Ship/plane names only revealed during combat, not movement.

# 8. All observation actions must follow the above rules each time a unit moves into a Hex or at the start/end of turn.

"""
"""Search Table
Die Roll | Result
---------|-------
1-5    | Successful observation
6+     | Unsuccessful observation

+1 to die roll if task force is in or moves into cloud.
+1 to die roll at night

"""

"""Observation table

Observing unit  | Unit being observed   | Weather condition | Hex Distance / Result
---             | ---                   | ---               | 0 | 1 | 2 | 3 | ---
----------------------------------------------------------------------------------
Day Turn
-----------------------------------------------------------------------------------
Base            | Air Formation         | Clear             | 3 | 2 | 1 |   |
Base            | Air Formation         | Cloud             | 2 | 1 |   |   |
Base            | Task Force            | Clear             | 3 | 2 | 1 |   |
Base            | Task Force            | Cloud             | 3 | 2 | 1 |   |
Task Force      | Air Formation         | Clear             | 3 | 2 | 1 |   |
Task Force      | Air Formation         | Cloud             | 2 | 1 |   |   |
Task Force      | Task Force            | Clear             | 3 | 2 | 1 |   |
Task Force      | Task Force            | Cloud             | 3 | 2 | 1 |   |
Air Formation   | Air Formation         | Clear             | 3 | 2 | 1 |   |
Air Formation   | Air Formation         | Cloud             | 2 | 1 |   |   |
Air Formation   | Task Force            | Clear             | 3 | 2 | 1 |   |
Air Formation   | Task Force            | Cloud             | 2 | 1 |   |   |
TF (Radar)      | Air Formation         | Clear             | 2 | 2 | 1 | 1 |
TF (Radar)      | Air Formation         | Cloud             | 2 | 2 | 1 | 1 |
TF (Radar)      | Task Force            | Clear             |   |   |   |   |
TF (Radar)      | Task Force            | Cloud             |   |   |   |   |
-----------------------------------------------------------------------------------
Night Turn
-----------------------------------------------------------------------------------
Base            | Air Formation         | Clear             | 1 |   |   |   |
Base            | Air Formation         | Cloud             |   |   |   |   |
Base            | Task Force            | Clear             | 1 |   |   |   |
Base            | Task Force            | Cloud             | 1 |   |   |   |
Task Force      | Air Formation         | Clear             | 1 |   |   |   |
Task Force      | Air Formation         | Cloud             |   |   |   |   |
Task Force      | Task Force            | Clear             | 1 |   |   |   |
Task Force      | Task Force            | Cloud             | 1 |   |   |   |
Air Formation   | Air Formation         | Clear             | 2 |   |   |   |
Air Formation   | Air Formation         | Cloud             | 1 |   |   |   |
Air Formation   | Task Force            | Clear             | 1 |   |   |   |
Air Formation   | Task Force            | Cloud             |   |   |   |   |
TF (Radar)      | Air Formation         | Clear             | 2 | 2 | 1 | 1 |
TF (Radar)      | Air Formation         | Cloud             | 2 | 2 | 1 | 1 |
TF (Radar)      | Task Force            | Clear             |   |   |   |   |
TF (Radar)      | Task Force            | Cloud             |   |   |   |   |


**6.7** Observation Effects of Weather Conditions

- The Observation Tables contain separate rows for different types of weather. If a unit is in a hex with a Cloud marker, one is added to the Search Table die roll. A unit may not observe anything in a Storm hex under any circumstances. A unit that begins a turn in a Storm hex may not observe anything that turn.



## 7. OBSERVATION. (Original board game rule 7 from Avalon Hill's "Flat Top" game)

**7.1** Players keep track of the positions of hidden units (units that can not currently be observed) on the Plot Map. Units must be observed by the opponent before they are required to be placed on the mapboard. A player may, at his discretion, place unobserved units on the mapboard at any time.

**7.2** Observed units must immediately be placed on the mapboard.

**7.3** During the Plane Movement Phase, before a player moves each Air Formation that is on the mapboard, he must state whether the Air Formation will attempt to observe or not. If an Air Formation will attempt to observe, the player rolls one die and consults the Search Table. Each turn, a player must consult the Search Table once for each Air Formation that attempts to observe.

- **7.3.1** If the result is a 'S', the Air Formation may observe during that turn.
- **7.3.2** If the result is a 'U', the Air Formation may not observe during that turn, though it may move normally.
- **7.3.3** If an Air Formation begins the turn in a hex with a Cloud marker, one is added to the Search Table die roll.
- **7.3.4** If a unit begins the turn in a Storm hex, it may not consult the Search Table or observe anything this turn,

**7.4** A player is never required to use an Air Formation to observe. If he does not wish to consult the Search Table, the Air Formation may not observe that turn but may still move normally. Whether a unit can observe or not has nothing to do with whether it may be observed or not.

**7.5** TFs may always observe. A player is never required to consult the Search Table for a TF.

**7.6** One unit (a TF or an Air Formation that can observe) can observe all enemy units within range in the hex it begins its movement in, each hex it moves into, and the hex it ends its movement in. All units (including bases and coastwatchers) can observe all enemy units that move within their range at any point during either player's portion of the turn.

**7.7** Units on the mapboard at the end of the turn that can no longer be observed may be removed from the mapboard.

**7.8** As a unit (that can observe) enters each hex during its movement, the non-moving player must state if any of his units can be observed. At the same time, units of the non-moving player which are on the mapboard can observe the moving unit as it enters a hex.

Example: The Japanese player states that Air Formation 5 (in hex 
BB14) will attempt to observe. He rolls a '1' so the attempt is suc- 
cessful. The weather in the area is clear. Japanese Air Formation 5 
(10 Betty Air Factors with GP Bombs and S Zero Air Factors) at 
low altitude moves into hex BB15. Allied T F 3 (CV Enterprise, BB 
South Dakota, CA San Francisco, and IODD) is in hex BB17 but is 
not on the mapboard because it has been unobserved (hidden) un- 
til now. The Allied player must tell the Japanese player that he has 
observed T FS (the Condition Number being 1), and then place a 
T F counter on the mapboard in the hex BB17. The Allied player 
places TF6 in hex BB17. Since Allied T F 3 (as shown by the TF6 
counter) is now on the mapboard, it may be used for observation. 
The Japanese player must tell the Allied player that he has ob- 
served Air Formations (the Condition Number being 1), even 
though it may seem obvious since Air Formation 5 is already on 
the mapboard and is itself searching. The Japanese player then 
continues the movement of Air Formation 5 by moving it into hex 
BB16. The Allied player must tell the Japanese player that he has 
observed one T F with from 7-20 ships (even though the maximum 
he could have is 15 due to the T F limit) including carriers, capital 
ships, and small ships (the Condition Number being 2). At the 
same time the Japanese player must tell the Allied player that he 
has observed one Air Formation with from 8-22 planes, some 
armed and some unarmed. The Japanese player then continues 
the movement of Air Formation 5 by moving it into hex BB17. 
The Allied player must tell the Japanese player that he has ob- 
served one T F with 13 ships including one carrier, two capital 
ships, and ten small ships (the Condition Number being 3). At the 
same time the Japanese player must tell the Allied player that he 
has observed one Air Formation with 15 planes, 10 armed and 5 
unarmed. 

**7.9** Only units that themselves are on the mapboard can be used to observe other units. Bases and coastwatchers are always considered to be on the mapboard, and thus can always be used for observation. Coastwatchers can observe planes over any all-land or partial-land hex of the island their symbol appears in and all-sea hexes adjacent to partial-land hexes of the island. However, Coastwatchers cannot observe planes in a hex with an enemy base.

EXCEPTION: The Japanese Coastwatcher symbol on New Guinea only affects hexes inside the Japanese Coast- 
watcher Perimeter Line shown on the inapboard by a dot- 
ted line. The Allied Coastwatcher symbol on New Guinea 
affects all hexes on the island.

**7.10** Some units (ships and bases) carry radar which in some cases improves observation (in both day and night turns). Radar is unaffected by Cloud markers. However, radar can only observe air units at high altitude; it canno observe planes at low altitude or ships. In addition, al bases and ships with radar may observe enemy air units a high altitude at a distance of three hexes (in both day am night turns); the Condition Number is l, (See 7.13) 

**7.11** To use the Observation Tables, players should find the type of observing unit, the type of unit being observed and the weather condition of the hex being observed, an cross index this with the distance between the observing unit and the unit being observed. The distance betwee two is measured by counting the hex occupied by the unit being observed but not the hex the observing unit and the unit being observed are in the same hex. Note that there is one table for day turns and one for night turns. 

**7.12** The Condition Numbers.

- **7.12.1** Condition One—The is that something is there, and it is either a plane or TF. He is not told how many Air of 'IT's are present.
- **7.12.2** Condition Two—The observing player is told how many Air Formations or TFs are present, every class of plane or ship and the total number of ships or Air Factors pttscnt. However, the player with the units being observed may lie about the total number of ships or Air Factors Fy inflating or deflating the number by 500/0 One Air Formation or TF may be reported as one or two. He does not give any specifics about how many of each ship or plane class are there or how many of each ship or plane class are in each TF or Air Formation.
- **7.12.3** Condition Three—The observing player is told the exact number of Air Formations and T FS present, and the exact number and classes of planes and ships in them, in- cluding how many of each class. He does not disclose ship or plane names.

Important Note: for observation purposes ship and plane classes are as follows:

CVs, CVLs = Carriers
AVs, CAVs, BBS, CAS, CLS = Capital Ships
DDS, PGs, AOs, APS, APDs = small Ships
SSs = Submarines
Armed planes—Bombers
Unarmed planes—interceptors

**7.13** When the observing unit does not have radar, planes altitudes are revealed only when the Condition Number is 3, or at the beginning of any type of Air Combat. When the observing unit has radar, the Condition is I or 2, and the observed units include planes at high altitude, the observing player is told only that there are planes at high altitude (he is not told whether there are planes at low altitude as well or how many planes are at each altitude). When the Condition Number is 3, the observing player is told the exact number and class of each plane at each altitude.

**7.14** Planes in TF boxes and base boxes may only be observed if the Condition Number is 3. Only planes in Just Landed boxes or Ready boxes can be observed (planes in Readying boxes can never be observed) and the player doing the observation is then only told that planes are present on the ship.

**7.15** Exact ship and plane names are never revealed dur- ing movement. Ship names and types are only revealed if planes attack them, and then only if at least one plane sur- vives the Air-to-Air Combat Step. If one plane survives, the names of all ships in the hex must be disclosed. Exact Cornoav

**7.15.1** Exact locations of planes and exact numbers of planes in plane carrying ship and base boxes are never revealed, unless necessary during combat resolution. Likewise, the fact that planes are dispersed is never re- vealed unless necessary during combat resolution. (See 21.7) 

**7.15.2** The fact that ships are anchored is not revealed until the beginning of the AA Combat Step. If ships are anchored, the opponent must be told which specific ships are anchored at the beginning of the AA Combat Step.

**7.16** A player does not have to put the correct TF counter or Air Formation counter on the mapboard when units are observed. He can use any one T F or Air Formation counter to represent all the observed units in one hex. The only restriction is that if the unit observed is an Air Forma- tion, an Air Formation counter must be placed on the mapboard and if the unit is a TF, a TF counter must be placed on the mapboard; T F counters and Air Formation counters cannot be used to represent the other. Keep track of the actual TF and Air Formation counters on the Plot Map. If a player has both Air Formations and TFs in a hex, he must put one Air Formation and one TF counter on the map. If during the Shadowing Phase, the Task Force Movement Phase, or the Plane Movement Phase, ships or planes (that were observed at the beginning of the turn and can still be observed) reorganize, the opponent must be told of such changes within the bounds of the appropriate Condition Number.

**7.17** The non-moving player cannot place Air Formations or TFs on the mapboard during the other players Plane Movment Phase to observe units or initiate combat with units as he sees them move within range of his hidden units. Of course, if these units are observed by the moving units, they must be placed on the mapboard, and can then themselves observe enemy units.

**7.18** Observation does not cost any additional movement points.
"""
"""
Observation logic for Flattop game, implementing rules from observation_rules.py and game_requirements.txt.
"""

import random
from flattop.hex_board_game_model import Hex, Piece, get_distance
from flattop.operations_chart_models import AirFormation, Carrier, TaskForce, Base, Ship, Aircraft
from flattop.weather_model import WeatherManager, CloudMarker


TURN_DAY = "day"
TURN_NIGHT = "night"

# --- Search Table Logic ---
def search_table_roll(is_cloud=False, is_night=False):
    """
    Returns True if observation is successful, False otherwise.
    +1 to die roll if in cloud, +1 if at night.
    """
    roll = random.randint(1, 6)
    modifier = 0
    if is_cloud:
        modifier += 1
    if is_night:
        modifier += 1
    result = roll + modifier
    return result <= 5

# --- Observation Table Logic ---
# Returns Condition Number (1, 2, or 3) or None if not observable
# This is a simplified version for core logic, can be expanded for full table

def get_condition_number(observer, target, weather_manager:WeatherManager, hex_coord, distance, turn_type, radar=False):
    """
    Returns the Condition Number for observation based on observer/target types, weather, distance, turn type, and radar.
    Uses WeatherManager to determine weather at hex_coord.
    """
    # Get weather at hex
    weather = weather_manager.get_weather_at_hex(hex_coord)
    if weather == "storm":
        return None
    
    is_cloud = weather == "cloud"
    is_clear = weather == "clear"
    # Night turn: only certain observations allowed
    if turn_type == TURN_NIGHT:
        if isinstance(observer, Base):
            if isinstance(target, AirFormation) and is_clear and distance == 1:
                return 1
            if isinstance(target, TaskForce) and distance == 1:
                return 1
        if isinstance(observer, TaskForce):
            if isinstance(target, AirFormation) and is_clear and distance == 1:
                return 1
            if isinstance(target, TaskForce) and distance == 1:
                return 1
        if isinstance(observer, AirFormation):
            if isinstance(target, AirFormation) and is_clear and distance in (1,2):
                return 1
            if isinstance(target, TaskForce) and is_clear and distance == 1:
                return 1
        # Radar logic (TF or Base with radar)
        if radar and isinstance(observer, (TaskForce, Base)) and isinstance(target, AirFormation):
            if distance in (1,2):
                return 1
        return None
    # Day turn
    if isinstance(observer, Base):
        if isinstance(target, AirFormation):
            if is_clear:
                if distance == 3:
                    return 1
                elif distance == 2:
                    return 2
                elif distance == 1:
                    return 3
            elif is_cloud:
                if distance == 2:
                    return 1
                elif distance == 1:
                    return 2
        if isinstance(target, TaskForce):
            if is_clear:
                if distance == 3:
                    return 1
                elif distance == 2:
                    return 2
                elif distance == 1:
                    return 3
            elif is_cloud:
                if distance == 3:
                    return 1
                elif distance == 2:
                    return 2
                elif distance == 1:
                    return 3
    if isinstance(observer, TaskForce):
        if isinstance(target, AirFormation):
            if is_clear:
                if distance == 3:
                    return 1
                elif distance == 2:
                    return 2
                elif distance == 1:
                    return 3
            elif is_cloud:
                if distance == 2:
                    return 1
                elif distance == 1:
                    return 2
        if isinstance(target, TaskForce):
            if is_clear:
                if distance == 3:
                    return 1
                elif distance == 2:
                    return 2
                elif distance == 1:
                    return 3
            elif is_cloud:
                if distance == 3:
                    return 1
                elif distance == 2:
                    return 2
                elif distance == 1:
                    return 3
    if isinstance(observer, AirFormation):
        if isinstance(target, AirFormation):
            if is_clear:
                if distance == 3:
                    return 1
                elif distance == 2:
                    return 2
                elif distance == 1:
                    return 3
            elif is_cloud:
                if distance == 2:
                    return 1
                elif distance == 1:
                    return 2
        if isinstance(target, TaskForce):
            if is_clear:
                if distance == 3:
                    return 1
                elif distance == 2:
                    return 2
                elif distance == 1:
                    return 3
            elif is_cloud:
                if distance == 2:
                    return 1
                elif distance == 1:
                    return 2
    # Radar logic (TF or Base with radar)
    if radar and isinstance(observer, (TaskForce, Base)) and isinstance(target, AirFormation):
        if distance in (1,2):
            return 1
    return None

# --- Observation Reporting ---
def report_observation(condition_number, target):
    """
    Returns a dict describing what is revealed about the target based on the Condition Number.
    """
    if condition_number == 1:
        # Only presence and type
        return {"type": type(target).__name__, "present": True}
    elif condition_number == 2:
        # Number, classes, and total ships/planes (±50% fudge allowed)
        # For simplicity, we do not apply fudge here
        info = {"type": type(target).__name__, "present": True}
        if isinstance(target, AirFormation):
            info["aircraft_classes"] = list(set(ac.type for ac in target.aircraft))
            info["total_aircraft"] = sum(ac.count for ac in target.aircraft)
        elif isinstance(target, TaskForce):
            info["ship_classes"] = list(set(ship.type for ship in target.ships))
            info["total_ships"] = len(target.ships)
        return info
    elif condition_number == 3:
        # Exact numbers and classes
        info = {"type": type(target).__name__, "present": True}
        if isinstance(target, AirFormation):
            info["aircraft_details"] = [(ac.type, ac.count) for ac in target.aircraft]
        elif isinstance(target, TaskForce):
            info["ship_details"] = [(ship.name, ship.type) for ship in target.ships]
        return info
    return {"present": False}

# --- Main observation logic ---
def attempt_observation(observer, target, weather_manager : WeatherManager, hex_coord:Hex, distance:int, turn_type):
    """
    Attempts to observe a target from an observer, applying all rules.
    Returns observation report dict or None if not observed.
    Set the target 
    Integrates with WeatherManager.
    """
    # Storm hex: no observation
    if weather_manager.is_storm_hex(hex_coord):
        return None
    
    if distance > 3:
        return None
    
    # check if observer has radar
    radar = False
    if isinstance(observer, (TaskForce, Base)):
        radar = observer.has_radar

    weather = weather_manager.get_weather_at_hex(hex_coord)
    is_cloud = weather == "cloud"
    is_night = turn_type == TURN_NIGHT
    if isinstance(observer, AirFormation):
        # Roll on Search Table
        if not search_table_roll(is_cloud, is_night):
            return None
    result = []  # Initialize result list to collect observations
    # TFs, bases, coastwatchers always observe (no roll)
    condition_number = get_condition_number(observer, target, weather_manager, hex_coord, distance, turn_type, radar)
    if condition_number is None:
        return None
    observer_result = report_observation(condition_number, target)
    if observer_result:
        set_game_model_observed(target, condition_number)
        result.append(observer_result)
        print(f"{observer} observed {target} with Condition Number {condition_number}: {result}")
    #now check if the target can observe the observer
    target_condition_number = get_condition_number(target, observer, weather_manager, hex_coord, distance, turn_type, radar)
    if target_condition_number is not None:
        target_result = report_observation(target_condition_number, observer)
        if target_result:
            set_game_model_observed(observer, target_condition_number)
            print(f"{target} observed {observer} with Condition Number {target_condition_number}: {target_result}")
            result.append(target_result)
    return result


# --- Utility: Mark piece as observed/unobserved ---
def set_game_model_observed(game_model, observation_condition:int):
    # can't actually set piece observed condition. Needs to be done against the game model
    if not isinstance(game_model, (Piece, AirFormation, TaskForce, Base, Carrier)):
        pass  # Not a valid game model type, assume its weather or similar
    if observation_condition is None:
        raise ValueError("Observation condition cannot be None.")
    if not isinstance(observation_condition, int) or observation_condition < 0:
        raise ValueError("Observation condition must be a non-negative integer.")
    
    if game_model is not None:
        game_model.observed_condition = observation_condition

# --- Utility: Remove unobserved pieces from mapboard ---
def remove_unobserved_pieces(pieces):
    return [p for p in pieces if getattr(p, "observed_condition", 0) > 0]

# --- Example usage ---

# === USAGE EXAMPLES AND INTEGRATION DETAILS ===
#
# Example 1: Basic observation check (no UI)
# --------------------------------------------------
# af = AirFormation(1)
# tf = TaskForce(1)
# weather_manager = WeatherManager()
# hex_coord = Hex(2, 2)
# distance = 2
# turn_type = TURN_DAY
# result = attempt_observation(
#     af, tf, weather_manager, hex_coord, distance, turn_type,
#     radar=False, airformation_attempts=True
# )
# print("Observation result:", result)
# if result:
#     set_piece_observed(tf, True)
# else:
#     set_piece_observed(tf, False)
# print("TF observed status:", getattr(tf, "observed", False))
#
# Example 2: Integrating with DesktopUI for popups
# --------------------------------------------------
# ui = DesktopUI(board, turn_manager, weather_manager)
# af = AirFormation(1)
# tf = TaskForce(1)
# hex_coord = Hex(2, 2)
# distance = 2
# turn_type = TURN_DAY
# result = attempt_observation(
#     af, tf, weather_manager, hex_coord, distance, turn_type,
#     radar=False, airformation_attempts=True
# )
# # This will display a popup with the observation result at the hex location
#
# Example 3: Game loop integration
# --------------------------------------------------
# for piece in board.pieces:
#     # Only attempt observation if piece can observe
#     if hasattr(piece, 'can_observe') and piece.can_observe:
#         for target in board.pieces:
#             if target.side != piece.side:
#                 hex_coord = target.position
#                 distance = get_distance(piece.position, target.position)
#                 turn_type = TURN_DAY if not turn_manager.is_night() else TURN_NIGHT
#                 result = attempt_observation(
#                     piece.game_model, target.game_model, weather_manager,
#                     hex_coord, distance, turn_type, radar=False, airformation_attempts=True
#                 )
#                 if result:
#                     set_piece_observed(target, True)
#                 else:
#                     set_piece_observed(target, False)
#
# Example 4: Removing unobserved pieces from the mapboard
# --------------------------------------------------
# board.pieces = remove_unobserved_pieces(board.pieces)
#
# Notes:
# - WeatherManager should be updated each turn to reflect current weather and cloud/storm positions.
# - DesktopUI integration allows observation results to be shown interactively to the player.
# - Use set_piece_observed to mark pieces as visible/invisible for rendering.
