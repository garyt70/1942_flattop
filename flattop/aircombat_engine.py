"""

Rules.....

Only certain planes can perform certain missions.

- **8.12.1** The following planes can always serve as interceptors, escorts, or bombers: Zero, P-38, P-39, P-40, Beaufighter, Wildcat.  
    The following planes can serve as interceptors and escorts, but not as bombers: Dave, Jake, Pete.  
    The following planes can serve as bombers, but not as escorts: Avenger, Dauntless, Judy, Val.
- **8.12.2** If an Air Factor that can serve as an interceptor or escort is in an Air Formation with bombers, it is an escort. If the Air Formation does not have bombers, it is an interceptor.
- **8.12.3** All other planes can only serve as bombers.
- **8.12.4** If an Air Factor is armed when it takes off, it is considered to be a bomber until it lands, even after it has performed its bombing mission or jettisoned its bomb. Each armed Air Factor may only make one attack; to make another attack it must land and then rearm again before taking off.
- **8.12.5** Planes which cannot serve as interceptors or escorts may be in flight unarmed. They cannot initiate combat of any kind.


## 15. COMBAT

**15.1** Units must occupy the same hex in order to have combat. All combat that occurs in one hex is considered part of the same battle. Observation Condition Numbers are not considered once combat begins. (See 7.15.)

**15.2** Air-to-Air Combat can only occur within two hexes of a plane-carrying ship or base, or in any hex with any ship, and only between observed units. Anti-Aircraft Combat and Air Attack Combat can only occur in a hex with a ship or base, and only between observed units. Surface Attack Combat can occur in any sea or partial-land hex on the mapboard, but only between observed units. Note that combat in general is not mandatory, although certain Combat Steps are once the combat procedure has been initiated.

**15.3** A unit has a Basic Hit Table (hereafter referred to as BHT) for all types of combat it may participate in. In all Combat Steps, players must always announce which enemy units their units are attacking before rolling the die to resolve the combat.

**15.4** Combat in different hexes can be resolved in any order. All combat in one hex (one battle) should be resolved before combat in another hex is begun. Note that one battle may actually contain more than one sequence of Combat Steps in cases such as 14.18, 16.8, and 16.9. Players should skip Combat Steps in battles that do not apply to that battle.

**15.5** Sequence. Players should perform combat in the following order for each battle:
- 15.5.1 Air-to-Air Combat Step.
- 15.5.2 Anti-Aircraft Combat Step.
- 15.5.3 Air Attack Combat Step.
- 15.5.4 Surface Attack Combat Step.

**15.6** Effect of Combat on RFs. Planes expend RFs during certain types of combat. When a plane expends an RF due to combat, the Air Record Sheet is adjusted. The number of turns the plane expending the RF can remain in flight is reduced by one by crossing out the notation for that plane in the turn it was formerly supposed to land and putting the notation in the turn before this. This is done each turn an RF is expended due to combat.

- **15.6.1** One RF is expended by interceptors and escorts for every turn in which they engage in Air-to-Air Combat. Only one RF is expended each turn, even if an Air Factor engages in more than one Air-to-Air Combat. Interceptors and escorts may choose not to expend an RF in Air-to-Air Combat, but if they do, their BHT for Air-to-Air Combat is reduced by six tables (-6). To avoid expending the RF for the whole turn, Air Factors would have to suffer this six-table reduction for every Air-to-Air Combat in the turn.
- **15.6.2** Bombers do not expend RFs in Air-to-Air Combat.
- **15.6.3** One RF is expended by bombers if they make a dive bombing attack, a torpedo bombing attack, or a level bombing attack from low altitude. Bombers that make a level bombing attack from high altitude do not expend RFs.

**15.7** Only one round of all types of combat is allowed in one turn. After one round of Surface Attack Combat has been fought, no more combat can take place in that hex for the rest of the turn. If combatants are still present next turn, the procedure could start over again. In other words, there are no second or subsequent rounds of combat in any turn.
---
## 16. AIR-TO-AIR COMBAT

**16.1** Air-to-Air Combat involves only plane units. Only interceptors can initiate Air-to-Air Combat, and the other side may not avoid it; escorts and bombers cannot initiate Air-to-Air Combat. If both sides have interceptors, combat can be initiated by either side and the other side may not avoid it. Otherwise, interceptors may always choose to avoid combat. The Interception Table is never used during the Combat Phase. If one side can, and wishes to, initiate Air-to-Air Combat, it is initiated automatically.  
*Exception: 14.13.* The player with the interceptors can choose not to use all of his interceptors in a hex (even if they are all in one Air Formation) except when both players have interceptors and one wishes to initiate combat; then both players must use all interceptors in the hex.

**16.2** Planes can be involved in more than one Air-to-Air Combat in one turn, if involved in Special Air-to-Air Combat during the Plane Movement Phase. However, planes can only be involved in one Air-to-Air Combat Step in a battle during the Combat Phase.

**16.3** Air-to-Air Combat is resolved in two parts, in the following sequence:
- **16.3.1** Interceptor to Escort Combat.
- **16.3.2** Interceptor to Bomber Combat.

**16.4** The player with the interceptors has the option to divide his interceptors into two groups, one designated to attack the escorts and one designated to attack the bombers. The interceptor to escort combat is resolved first; interceptors designated to attack the bombers take no part in this combat. A player may assign all his interceptors to attack the escorts if he so chooses.

**16.5** Interceptor to Escort Combat
- **16.5.1** Interceptors must be at the same altitude as the enemy escorts to attack.
- **16.5.2** The attacker totals the number of interceptors he has in the hex designated to attack the escorts, even if they are in more than one Air Formation. The defender totals the number of escorts he has in the hex, even if they are in more than one Air Formation.
- **16.5.3** Combat is simultaneous. Each player rolls one die for each attacking plane name, using that plane name's BHT. All hits are removed only after all planes (interceptors and escorts) have attacked.
- **16.5.4** Each plane name can attack one other plane name, or Air Factors of one plane name can be split up to attack two or more enemy plane names.
- **16.5.5** After each plane name of both sides has attacked, all Air Factors that were eliminated are removed and the appropriate amount of Victory Points recorded.

**16.6** Interceptor to Bomber Combat
- **16.6.1** Interceptors must be at the same altitude as enemy bombers to attack them.
- **16.6.2** After interceptor to escort combat, if the ratio of surviving interceptors (designated to attack the escorts) to escorts is 2:1 or better, the surviving interceptors designated to attack the escorts may join (combine with) the interceptors that were designated to attack the bombers. Follow the procedure detailed in 16.5.2–16.5.5, except that the combat is between all the interceptors and the bombers; the escorts take no part.
- **16.6.3** After interceptor to escort combat, if the ratio of surviving escorts to the interceptors (designated to attack the escorts) is 2:1 or better, no interceptor to bomber combat is allowed. Air-to-Air Combat is over for all the planes.
- **16.6.4** If neither the surviving interceptors (designated to attack the escorts) nor escorts have a 2:1 advantage, only the interceptors that were designated to attack the bombers may attack the bombers. Follow the procedure detailed in 16.5.2–16.5.5, except that the combat is between the interceptors designated to attack the bombers and the bombers; the escorts and interceptors designated to attack the escorts take no part.
- **16.6.5** The player with the interceptors is never required to attack the bombers after interceptor to escort combat just because he is able to do so.

**16.7** Interceptor to interceptor combat is like interceptor to escort combat, except there is no interceptor to bomber combat, and both sides must use all their Air Factors in the hex in combat. If one player has just interceptors while the other has interceptors and bombers, and the player with just the interceptors wishes to attack the bombers, the player with the bombers can require (and initiate) Air-to-Air Combat between his interceptors and the other player's interceptors first. Interceptor to bomber combat would then follow this. (See 14.17 and 14.18.)

**16.8** If some interceptors, escorts, or bombers in the same hex are at high altitude and some are at low altitude, two separate Air-to-Air combat sequences are fought in the one hex, one involving the planes at each altitude. Planes cannot switch altitude during combat and planes at one altitude have no effect on planes at the other altitude during combat.

**16.9** When a battle contains both the situation shown in 14.18 and the situation shown in 16.8, it is possible to have four separate Air-to-Air Combats in the same hex in one turn; two at each altitude, one with each player as the attacker.

**16.10** Modifiers
- **16.10.1** If interceptors or escorts do not expend an RF, their BHT is reduced by six tables (-6). Bombers never expend RFs in Air-to-Air Combat.
- **16.10.2** If the combat is taking place in a hex with clouds, the BHT is reduced by one table (-1).
- **16.10.3** If the combat is taking place at night, the BHT is reduced by two tables (-2).
- **16.10.4** If any of the following planes are armed, they have their BHT reduced by six tables (-6): Wildcat, P-38, P-39, P-40, Beaufighter, Zero, and Rufe.

*Example of Air-to-Air Combat:*  
In the hex, the Japanese player has two Air Formations. Air Formation 5 contains 15 unarmed Zero Air Factors, 5 at high altitude and 10 at low altitude. Air Formation 17 contains 4 unarmed Val Air Factors at low altitude.  
The Allied player has three Air Formations in the hex. Air Formation 1 has 10 armed B-17 Air Factors at high altitude. Air Formation 2 has 9 Wildcats, 3 at high altitude and 6 at low altitude. Air Formation 4 has 2 armed Hudson Air Factors, 2 armed A-20 Air Factors, 10 armed B-26 Air Factors, and 2 unarmed Beaufighter Air Factors at low altitude.

The Japanese player initiates Air-to-Air Combat. The players decide to resolve the combat at high altitude first. The Japanese player designates all his interceptors (5 Zeros) to attack the escorts (3 Wildcats). The BHT for Zeros is 9. The Japanese player rolls a '4'. Two hits are scored. The BHT for Wildcats is 9. The Allied player rolls a '3'. One hit is scored. Two Wildcats and one Zero Air Factor are eliminated.

The ratio of interceptors to escorts is now 4:1, more than the required 2:1, so the interceptors designated to attack the escorts can attack the bombers, and the Japanese player decides to make the attack. The Japanese player rolls a '6'. Three hits are scored. The BHT for B-17s is 8. The Allied player rolls a '2'. One hit is scored. Three B-17s and one Zero are eliminated.

All combat at high altitude is finished, so the players now must resolve combat at low altitude. The Japanese player designates some of his interceptors (4 Vals and 4 Zeros) to attack the escorts and some of his interceptors (6 Zeros) to attack the bombers. The BHT for Vals is 2. The Japanese player states that the Vals will attack the Wildcats. He rolls a '3'. No hits are scored. The Japanese player states that the Zeros will attack the Wildcats. He rolls a '5'. Two hits are scored.

The BHT for Beaufighters is 6. The Allied player states that the Beaufighters will attack the Zeros. He rolls a '4'. No hits are scored. The Allied player states that the Wildcats will attack the Zeros. He rolls a '3'. Three hits are scored. Two Wildcats and three Zeros are eliminated.

The ratio of interceptors to escorts is now 5:6, less than 2:1 for either side, so only the interceptors designated to attack the bombers (6 Zeros) may attack the bombers (2 Hudsons, 2 A-20s, and 10 B-26s). The interceptors designated to attack the escorts and the escorts take no part.

The Japanese player states that the Zeros will attack the B-26s. He rolls a '2'. One hit is scored. The BHT for Hudsons is 3. The Allied player rolls a '3'. No hits are scored. The BHT for A-20s is 3. The Allied player rolls a '5'. One hit is scored. The BHT for B-26s is 4. The Allied player rolls a '3'. No hits are scored. One B-26 and one Zero are eliminated.

All combat at low altitude is finished, and all Air-to-Air Combat in the hex is now over.


"""

"""
Combat results table is a simple table that has Attack Factor on the X axis and Hit Table values on the Y axis  
The hit table values are derived from the Basic Hit Table (BHT) for each aircraft type, modified by various conditions such as clouds, night, and whether the aircraft is armed.
The attack factor is the sum of the attack factors of all aircraft in the air formation that are attacking.


To implement this the number of attacking factors is a tuple (minimum, maximum) where the minimum is the minimum number of sum of attack factors. For Aircraft this is the sum of all aircraft for that aircraft type 
The hit table is from 1 to 15 and is the number of the hit value for GP, AP, Torpedo, and Air-to-Air combat.

The die roll adjusts the hit table value by the die roll result, and the hit table value, cross rferenced with the attacking facors, is then used to determine the number of hits scored.

example:
|           |  Attacking Factors                                                                                    |
| Hit Table | 1-2 | 3-4 | 5-6 | 7-8 | 9-10 | 11-12 | 13-15 | 16-20 | 21-23 | 26-30 | 31-35 | 36-40 | 41=45| 46-50+  | 
| 1         | None| None| None| 0   | 0    | 0     | 1     | 1     | 1     | 1     | 1     | 1     | 1    | 2       |
| 2         | None| None| 0   | 1   | 1    | 1     | 1     | 1     | 2     | 2     | 2     | 3     | 3    | 3       |
| 3         | None| 0   | 1   | 1   | 1    | 1     | 2     | 2     | 2     | 3     | 3     | 4     | 4    | 5       |
| 4         | None| 1   | 1   | 1   | 2    | 2     | 2     | 2     | 3     | 4     | 4     | 5     | 6    | 6       |
| 5         | None| 1   | 1   | 1   | 2    | 2     | 3     | 3     | 4     | 5     | 6     | 6     | 7    | 8       |
| 6         | 0   | 1   | 1   | 1   | 2    | 2     | 3     | 4     | 5     | 6     | 7     | 8     | 8    | 9       |
| 7         | 0   | 1   | 1   | 2   | 2    | 3     | 3     | 4     | 5     | 7     | 8     | 9     | 10   | 11      |
| 8         | 0   | 1   | 1   | 2   | 2    | 3     | 4     | 5     | 6     | 7     | 9     | 10    | 11   | 13      |
| 9         | 0   | 1   | 2   | 2   | 3    | 3     | 4     | 5     | 7     | 8     | 10    | 11    | 13   | 14      |
| 10        | 0   | 1   | 2   | 2   | 3    | 4     | 5     | 6     | 7     | 9     | 11    | 12    | 14   | 16      |
| 11        | 0   | 1   | 2   | 3   | 3    | 4     | 5     | 6     | 8     | 10    | 12    | 13    | 16   | 17      |
| 12        | 0   | 1   | 2   | 3   | 4    | 4     | 6     | 7     | 9     | 11    | 13    | 15    | 17   | 19      |
| 13        | 0   | 1   | 2   | 3   | 4    | 5     | 6     | 7     | 9     | 11    | 13    | 16    | 18   | 21      |
| 14        | 0   | 1   | 2   | 3   | 4    | 5     | 7     | 8     | 10    | 12    | 14    | 17    | 20   | 22      |
| 15        | 0   | 1   | 2   | 3   | 4    | 5     | 7     | 9     | 11    | 13    | 17    | 19    | 21   | 23      |
This table is used to determine the number of hits scored by the attacking aircraft against the defending aircraft

"""

"""
---

## 20. COMBAT RESOLUTION

**20.1** All combat is resolved using the Combat Results Table, by cross-indexing the BHT with the number of attacking units. Planes have different BHTs for different types of bombing attacks and targets (bases or TFs).

**20.2** All modifiers for each type of combat are listed on the Combat Modifiers Table. All modifiers that apply are cumulative. These modifiers are added to or subtracted from the BHT. The BHT in any type of combat can never be less than 1 no matter how many negative modifiers are applied. Attacks with a modified BHT of more than 15 are treated as 15.

**20.3** The numbers in the boxes within the columns of the Combat Results Table are the Result Numbers. For each attack, roll one die.  
- If the die number is '3' or '4', the Result Number is the number of hits scored.  
- If the die number is '1', the number of hits scored is equal to the Result Number minus two (-2).  
- If the die number is '2', the number of hits scored is equal to the Result Number minus one (-1).  
- If the die number is '5', the number of hits scored is equal to the Result Number plus one (+1).  
- If the die number is '6', the number of hits scored is equal to the Result Number plus two (+2).  
- If the Result Number is a *, a roll of 6 equals one hit scored and rolls of 1-5 have no effect.

*Example:*  
If the BHT is 8 and the number of attacking factors is 14, the Result Number is 4. If a '1' is rolled, 2 hits are scored. If a '2' is rolled, 3 hits are scored. If a '3' or '4' is rolled, 4 hits are scored. If a '5' is rolled, 5 hits are scored. If a '6' is rolled, six hits are scored.

---

### 21. DAMAGE

#### 21.1 Hits on Plane Units

Hits on plane units are recorded by eliminating Air Factors equal to the number of hits scored. If more hits are scored than there are Air Factors, excess hits are lost; they may not be transferred or accumulated.

"""

import random
from flattop.operations_chart_models import AirFormation, Aircraft, AircraftType

# --- Combat Results Table Implementation ---
# Each row is a Hit Table value (1-15), each column is an attack factor range.
# The table is indexed as [hit_table][attack_factor_range_index]
COMBAT_RESULTS_TABLE = [
    # 1-2, 3-4, 5-6, 7-8, 9-10, 11-12, 13-15, 16-20, 21-23, 26-30, 31-35, 36-40, 41-45, 46-50+
    [None, None, None, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 2],   # Hit Table 1
    [None, None, 0, 1, 1, 1, 1, 1, 2, 2, 2, 3, 3, 3],      # Hit Table 2
    [None, 0, 1, 1, 1, 1, 2, 2, 2, 3, 3, 4, 4, 5],         # Hit Table 3
    [None, 1, 1, 1, 2, 2, 2, 2, 3, 4, 4, 5, 6, 6],         # Hit Table 4
    [None, 1, 1, 1, 2, 2, 3, 3, 4, 5, 6, 6, 7, 8],         # Hit Table 5
    [0, 1, 1, 1, 2, 2, 3, 4, 5, 6, 7, 8, 8, 9],            # Hit Table 6
    [0, 1, 1, 2, 2, 3, 3, 4, 5, 7, 8, 9, 10, 11],          # Hit Table 7
    [0, 1, 1, 2, 2, 3, 4, 5, 6, 7, 9, 10, 11, 13],         # Hit Table 8
    [0, 1, 2, 2, 3, 3, 4, 5, 7, 8, 10, 11, 13, 14],        # Hit Table 9
    [0, 1, 2, 2, 3, 4, 5, 6, 7, 9, 11, 12, 14, 16],        # Hit Table 10
    [0, 1, 2, 3, 3, 4, 5, 6, 8, 10, 12, 13, 16, 17],       # Hit Table 11
    [0, 1, 2, 3, 4, 4, 6, 7, 9, 11, 13, 15, 17, 19],       # Hit Table 12
    [0, 1, 2, 3, 4, 5, 6, 7, 9, 11, 13, 16, 18, 21],       # Hit Table 13
    [0, 1, 2, 3, 4, 5, 7, 8, 10, 12, 14, 17, 20, 22],      # Hit Table 14
    [1, 1, 2, 3, 4, 5, 7, 9, 11, 13, 17, 19, 21, 23],      # Hit Table 15
]

# Attack factor ranges for columns in the table
ATTACK_FACTOR_RANGES = [
    (1, 2), (3, 4), (5, 6), (7, 8), (9, 10), (11, 12), (13, 15), (16, 20),
    (21, 23), (26, 30), (31, 35), (36, 40), (41, 45), (46, 999)
]

def get_attack_factor_index(attack_factor):
    for idx, (low, high) in enumerate(ATTACK_FACTOR_RANGES):
        if low <= attack_factor <= high:
            return idx
    return None

def get_hits_from_table(hit_table, attack_factor):
    # hit_table: integer 1-15
    # attack_factor: integer
    idx = get_attack_factor_index(attack_factor)
    if idx is None or hit_table < 1 or hit_table > 15:
        return 0
    result = COMBAT_RESULTS_TABLE[hit_table - 1][idx]
    return result if result is not None else 0

class AirCombatResult:
    def __init__(self):
        self.hits = {}
        self.summary = ""

    def add_hit(self, plane_type, count):
        self.hits[plane_type] = self.hits.get(plane_type, 0) + count

    def __str__(self):
        r = ""
        if len(self.hits) > 0:
           r =  f"Hits: {self.hits}\n{self.summary}"
        return r



def classify_aircraft(airformation_list):
                    """
                    ### 8.12 Plane Missions

                    Only certain planes can perform certain missions.

                    - **8.12.1** The following planes can always serve as interceptors, escorts, or bombers: Zero, P-38, P-39, P-40, Beaufighter, Wildcat.  
                        The following planes can serve as interceptors and escorts, but not as bombers: Dave, Jake, Pete.  
                        The following planes can serve as bombers, but not as escorts: Avenger, Dauntless, Judy, Val.
                    - **8.12.2** If an Air Factor that can serve as an interceptor or escort is in an Air Formation with bombers, it is an escort. If the Air Formation does not have bombers, it is an interceptor.
                    - **8.12.3** All other planes can only serve as bombers.
                    - **8.12.4** If an Air Factor is armed when it takes off, it is considered to be a bomber until it lands, even after it has performed its bombing mission or jettisoned its bomb. Each armed Air Factor may only make one attack; to make another attack it must land and then rearm again before taking off.
                    - **8.12.5** Planes which cannot serve as interceptors or escorts may be in flight unarmed. They cannot initiate combat of any kind.

                    ---
                    """
                    # Plane type sets for rule 8.12.1
                    CAN_DO_ALL = {
                        AircraftType.ZERO,
                        AircraftType.P38,
                        AircraftType.P39,
                        AircraftType.P40,
                        AircraftType.BEAUFIGHTER,
                        AircraftType.WILDCAT,
                    }
                    INTERCEPT_ESCORT_ONLY = {
                        AircraftType.DAVE,
                        AircraftType.JAKE,
                        AircraftType.PETE,
                    }
                    BOMBER_ONLY = {
                        AircraftType.AVENGER,
                        AircraftType.DAUNTLESS,
                        AircraftType.JUDY,
                        AircraftType.VAL,
                        AircraftType.B17,
                        AircraftType.B25,
                        AircraftType.B26,
                        AircraftType.AVENGER,
                        AircraftType.KATE
                        
                    }

                    interceptors, escorts, bombers = [], [], []

                    # First, collect all aircraft and classify by type and armament
                    for af in airformation_list:
                        has_bombers = False
                        # Determine if this air formation has bombers (for 8.12.2)
                        for ac in af.aircraft:
                            if ac.type not in CAN_DO_ALL and ac.type not in INTERCEPT_ESCORT_ONLY:  
                                has_bombers = True
                                break

                        # 8.12.1: Classify aircraft in the air formation
                        ac:Aircraft
                        for ac in af.aircraft:
                            ac_type = ac.type
                            is_armed = getattr(ac, "armament", False)
                            # 8.12.4: If armed, always bomber
                            if is_armed:
                                bombers.append(ac)
                                has_bombers = True
                                continue

                            # 8.12.3: All others bomber
                            if ac_type not in CAN_DO_ALL and ac_type not in INTERCEPT_ESCORT_ONLY:   
                                bombers.append(ac)
                                has_bombers = True
                                continue

                            # 8.12.1: Classification by type
                            if ac_type in CAN_DO_ALL:
                                # 8.12.2: If in formation with bombers, act as escort, else interceptor
                                if has_bombers:
                                    escorts.append(ac)
                                else:
                                    interceptors.append(ac)
                            elif ac_type in INTERCEPT_ESCORT_ONLY:
                                # Can only be interceptor or escort, never bomber
                                if has_bombers:
                                    escorts.append(ac)
                                else:
                                    interceptors.append(ac)
                            elif ac_type in BOMBER_ONLY:
                                # Can only be bomber, never escort
                                bombers.append(ac)
                            else:
                                
                                # If in formation with bombers, act as escort, else interceptor
                                if has_bombers:
                                    escorts.append(ac)  
                                else:
                                    interceptors.append(ac)
                            # Note: Unarmed aircraft that cannot serve as interceptors or escorts are ignored
                    return interceptors, escorts, bombers

def roll_die():
    return random.randint(1, 6)

def get_bht(aircraft:Aircraft, armed=False, die=None):
    # Returns the Basic Hit Table value for the aircraft, with modifiers for armament
    bht = getattr(aircraft.combat_data, "air_to_air", 0)
    # 16.10.4: If armed and type is in list, reduce BHT by 6
    ARMED_BHT_PENALTY_TYPES = {"Wildcat", "P-38", "P-39", "P-40", "Beaufighter", "Zero", "Rufe"}
    if armed and str(aircraft.type) in ARMED_BHT_PENALTY_TYPES:
        bht = max(1, bht - 6)
    # If die is provided, adjust BHT based on die roll
    if die is not None:
        bht =max(1, resolve_die_roll(bht, die))
    return bht

def apply_bht_modifiers(bht, rf_expended=True, clouds=False, night=False, armed=False, aircraft=None):
    # 16.10.1: If RF not expended, -6
    if not rf_expended:
        bht -= 6
    # 16.10.2: Clouds -1
    if clouds:
        bht -= 1
    # 16.10.3: Night -2
    if night:
        bht -= 2
    # 16.10.4: If armed and type is in list, -6 (already handled in get_bht)
    return max(1, bht)

def resolve_die_roll(result_number, die_roll):
    """
    Implements the die roll logic from Combat Resolution (20.3).
    - die 3 or 4: hits = result_number
    - die 1: hits = result_number - 2
    - die 2: hits = result_number - 1
    - die 5: hits = result_number + 1
    - die 6: hits = result_number + 2
    - if result_number is None, hits = 0
    - if result_number is '*', die 6 = 1 hit, else 0
    """
    if result_number is None:
        return 0
    if result_number == '*':
        return 1 if die_roll == 6 else 0
    if die_roll in (3, 4):
        return max(0, result_number)
    elif die_roll == 1:
        return max(0, result_number - 2)
    elif die_roll == 2:
        return max(0, result_number - 1)
    elif die_roll == 5:
        return max(0, result_number + 1)
    elif die_roll == 6:
        return max(0, result_number + 2)
    return 0

def resolve_air_to_air_combat(
    interceptors, escorts, bombers,
    rf_expended=True, clouds=False, night=False
):
    """
    Resolve air-to-air combat according to rules 16.x and Combat Resolution 20.x.
    interceptors, escorts, bombers: lists of Aircraft (same altitude).
    Returns a dict with results.
    """
    result = {
        "interceptor_hits_on_escorts": AirCombatResult(),
        "escort_hits_on_interceptors": AirCombatResult(),
        "interceptor_hits_on_bombers": AirCombatResult(),
        "bomber_hits_on_interceptors": AirCombatResult(),
        "eliminated": {"interceptors": [], "escorts": [], "bombers": []}
    }

    #keep track of total hits. Ths is used to remove losses at the end
    hits_on_bombers = 0
    hits_on_escorts = 0
    hits_on_interceptors = 0

    def determine_hits(aircraft_list, target_type):
        hits = 0
        for ac in aircraft_list:
            armed = ac.armament is not None
            die = roll_die()
            bht = get_bht(ac, armed=armed, die=die)
            bht = apply_bht_modifiers(bht, rf_expended, clouds, night, armed, ac)
            attack_factor = ac.count
            idx = get_attack_factor_index(attack_factor)
            if idx is None:
                continue
            hit_table = max(1, min(15, bht))
            hits = COMBAT_RESULTS_TABLE[hit_table - 1][idx]
            print(f"{ac.type} attacking {target_type} with BHT {bht},die {die}, attack factor {attack_factor}, hit table {hit_table}, hits {hits}")
        return hits

    # --- Interceptor to Escort Combat ---
    if interceptors and escorts:
        for ic in interceptors:
            hits = determine_hits([ic], "escorts")
            print(f"Interceptor {ic.type} attacking escorts. Hits resolved: {hits}")
            if hits > 0:
                result["interceptor_hits_on_escorts"].add_hit(str(ic.type), hits)
            hits_on_escorts += hits
        if hits_on_escorts > 0:
            result["interceptor_hits_on_escorts"].summary = f"Interceptors attacked escorts. ({hits_on_escorts} hits total)"

        for ec in escorts:
            hits = determine_hits([ec], "interceptors")
            print(f"Escort {ec.type} attacking interceptors. Hits resolved: {hits}")
            if hits > 0:
                result["escort_hits_on_interceptors"].add_hit(str(ec.type), hits)
            hits_on_interceptors += hits
        if hits_on_interceptors > 0:
            result["escort_hits_on_interceptors"].summary = f"Escorts attacked interceptors. ({hits_on_interceptors} hits total)"

    # --- Ratio check for 2:1 advantage ---
    total_interceptors = sum(ic.count for ic in interceptors)
    total_escorts = sum(ec.count for ec in escorts)
    interceptor_advantage = total_interceptors >= 2 * total_escorts

    # --- Interceptor to Bomber Combat ---
    if bombers and (interceptor_advantage or not escorts):
        for ic in interceptors:
            hits = determine_hits([ic], "bombers")
            print(f"Interceptor {ic.type} attacking bombers. Hits resolved: {hits}")
            if hits > 0:
                result["interceptor_hits_on_bombers"].add_hit(str(ic.type), hits)
            hits_on_bombers += hits
        if hits_on_bombers > 0:
            result["interceptor_hits_on_bombers"].summary = f"Interceptors attacked bombers. ({hits_on_bombers} hits total)"
        # Bombers can return fire if allowed by scenario/rules (not typical, but for completeness)
        for bc in bombers:
            hits = determine_hits([bc], "interceptors")
            print(f"Bomber {bc.type} attacking interceptors. Hits resolved: {hits}")
            if hits > 0:
                result["bomber_hits_on_interceptors"].add_hit(str(bc.type), hits)
            hits_on_interceptors += hits
        if hits_on_interceptors > 0:
            result["bomber_hits_on_interceptors"].summary = f"Bombers attacked interceptors. ({hits_on_interceptors} hits total)"   

    # --- Remove losses ---
    # Remove hits from interceptors, escorts, and bombers
    # modify range_remaining if RF expended

    def remove_hits(aircraft_list, hits, rf_expended):
        """
        Remove hits from aircraft in the list.
        If hits exceed count, remove all and return excess hits.
        If RF expended, decrement range_remaining.
        """
        while hits > 0 and aircraft_list:
            ac = aircraft_list.pop()
            hits_to_remove = min(ac.count, hits)
            # Determine which category to add to eliminated
            if ac in interceptors:
                result["eliminated"]["interceptors"].append((ac.type, hits_to_remove))
            elif ac in escorts:
                result["eliminated"]["escorts"].append((ac.type, hits_to_remove))
            else:
                result["eliminated"]["bombers"].append((ac.type, hits_to_remove))
            hits -= hits_to_remove
            ac.count -= hits_to_remove
            if rf_expended:
                ac.range_remaining -= 1
            if ac.count > 0:
                aircraft_list.append(ac)

    remove_hits(interceptors, hits_on_interceptors, rf_expended)
    remove_hits(escorts, hits_on_escorts, rf_expended)  
    remove_hits(bombers, hits_on_bombers, rf_expended)
    
    
    return result

# Example usage:
if __name__ == "__main__":
    from operations_chart_models import AircraftType, AircraftCombatData

    interceptors = [Aircraft(AircraftType.ZERO, count=5, acd=AircraftCombatData(air_to_air=9))]
    escorts = [Aircraft(AircraftType.WILDCAT, count=3, acd=AircraftCombatData(air_to_air=9))]
    bombers = [Aircraft(AircraftType.B17, count=10, acd=AircraftCombatData(air_to_air=8))]

    results = resolve_air_to_air_combat(interceptors, escorts, bombers, rf_expended=True, clouds=False, night=False)
    for k, v in results.items():
        print(f"{k}: {v}")
