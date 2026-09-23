# 1942 Flattop Detailed Requirements

## 1. Purpose

This document defines the detailed gameplay, interaction, and AI requirements for a digital implementation of 1942 Flat Top. It is intended to be the authoritative gameplay specification for the project and should be read as a requirements source for product design, UI behavior, game rules implementation, and AI logic.

This specification is grounded in the original rules as captured in the project rule source, especially the turn sequence, damage model, flight endurance, repair rules, and victory-point system. It intentionally preserves the strategic feel of the board game while describing the behavior a digital implementation must support in a clear and testable form.

The complete aircraft, ship, carrier, base, and combat-data contract is defined in [UNIT_DATA_SPEC.md](UNIT_DATA_SPEC.md). This document defines player-visible and behavioral requirements; the unit-data document defines the values and schema those requirements operate on.

## 2. Product Goal

The product must provide a playable, rule-aware naval-air strategy game for a human player or a human-versus-computer match. It must support multiple historical scenarios, maintain hidden information, preserve tactical uncertainty, and enable a serious opponent to make decisions that are meaningful and legal.

The game is not required to reproduce every historical bookkeeping abstraction of the original board game literally. It must reproduce the rule logic that matters to gameplay: task-force movement, air launch and recovery, observation, combat, damage, repair, and victory scoring.

## 3. Core Rule Principles

The digital implementation must respect the following principles:

1. The game is a two-side naval-air strategy game with Japanese and Allied forces.
2. Each turn proceeds through a strict phase order and cannot be skipped or rearranged.
3. Air and naval units are interdependent; carriers, bases, ships, and aircraft all affect one another.
4. Observation is limited and partial; hidden units must remain hidden until observed.
5. Aircraft have finite endurance and must either land safely or be lost if they cannot do so.
6. Damage reduces combat and operational capability, not only unit count.
7. Repairs are limited, delayed, and cannot fully restore all states.
8. Victory is determined by a points system, not just by eliminating all forces.
9. The AI must obey the same rules and information constraints as any human player.

## 4. Scenario and Game Structure Requirements

### REQ-04.01: Multiple scenarios
The game must support more than one scenario. Each scenario must define:

- board map and map sectors
- the board dimensions and source land-hex coordinates used by the scenario
- initial starting setup for both sides
- starting task forces and base locations
- initial air formations and aircraft allocation
- air and ship readiness states
- scenario-specific objectives and automatic victory threshold
- any special weather or reinforcement rules

### REQ-04.02: Scenario self-containment
Each scenario must be complete and playable without manual cross-file setup. The scenario data must define all required initial states and any special rules that differ from the base game.

### REQ-04.03: New game flow
The player must be able to:

- choose a scenario
- choose a game mode
- select a side
- start a new game
- restart the scenario
- exit to a menu or lobby

### REQ-04.04: Scenario setup fidelity
The digital setup must represent the currently defined scenario setups without collapsing their forces into generic placeholders.

Scenario One must support the setup represented by `scenario_one_setup`, including:

- Board One at 44 by 50 hexes (`44x50`)
- Japanese bases at Rabaul, Gasmata, Kavieng, and Truk
- the Japanese Air Formation 1 setup
- Allied Port Moresby
- Allied Task Force 1 with Lexington, four cruisers, ten destroyers, and its configured aircraft

Scenario Two must support the setup represented by `scenario_two_setup`, including:

- the combined 80 by 50 map (`80x50`) using Board One and Board Two land hexes
- Japanese bases at Rabaul, Gasmata, Kavieng, Truk, Lae, and Shortland
- Shokaku, Zuikaku, and Shoho task forces
- Landing Force 1a, Landing Force 1b, and Landing Force 2
- Allied bases at Port Moresby, Australia, and New Caledonia
- Allied Lexington and Yorktown task forces

The player must be able to identify each task force by name, side, position, ship composition, and aircraft composition when that information is legally available.

## 5. Turn and Phase Requirements

The game must implement the sequence of play exactly as required by the rule source.

### REQ-05.01: Required phase order
The engine must enforce this order for each turn:

1. Weather phase
2. Air operations phase
3. Task-force movement plotting phase
4. Shadowing phase
5. Task-force movement execution phase
6. Initiative phase
7. Plane movement phase
8. Combat phase
9. Repair phase
10. Time record phase

### REQ-05.02: Simultaneous and sequential phases
The rules must enforce the distinction between simultaneous phases and the non-simultaneous aircraft movement phase:

- phases before initiative operate on both sides in the same turn structure
- the plane movement phase resolves one side at a time, with the initiative holder acting first

### REQ-05.03: Phase legality
The application must prohibit illegal actions outside the active phase. For example:

- aircraft launch not allowed before air operations
- ship movement not allowed during the combat phase
- repairs not allowed outside the repair phase

### REQ-05.04: Turn clock
The game must track time using the time-record system and must expose the current turn time to the player with clear indication of day/night state.

## 6. Map, Terrain, and Weather Rules

### REQ-06.01: Hex map
The game board must use a hex-based map with clear land, sea, and coast distinctions. Movement and combat must be computed using hex adjacency, not free-form board movement. The map must render the source coordinate system and distinguish Board One from Board Two when a scenario uses both.

### REQ-06.05: Coordinate-aware map interaction
The UI must display the source hex coordinates for bases, task forces, air formations, and selected map cells. Selecting a marker must expose its coordinate and scenario identity without changing the underlying game state.

### REQ-06.06: Map board selection
For scenarios using multiple boards, the player must be able to switch between Board One and Board Two while retaining the same scenario state. The UI must show each board's dimensions and land-hex footprint.

### REQ-06.02: Weather phase rules
Weather must affect play through:

- wind direction changes at set intervals
- cloud markers
- storm hexes
- movement restrictions for air and ship units
- observation penalties in clouded or storm hexes

### REQ-06.03: Storm restriction
If a unit enters or begins a turn in a storm hex, the game must apply the equivalent to the rule set:

- air units cannot enter storm hexes
- ships in storm hexes have reduced or zero movement factor for that turn
- combat in storm hexes is not allowed

### REQ-06.04: Observation penalties
Clouds and storm conditions must increase the chance of failed observation or reduce the information available. This must be reflected in the observation logic and in the AI model.

## 7. Unit Model Requirements

### REQ-07.01: Task force model
Each task force must represent a grouped naval force that can include multiple types of ships. A task force must support:

- ship composition
- movement points
- damage state
- air-capable ships and carriers
- hidden or observed status

The task-force view must support named formations from the scenario setup, including carriers, cruisers, destroyers, transports, gunboats, oilers, and tankers where present. It must show ship counts and aircraft carried without revealing hidden details to an opposing player.

### REQ-07.02: Ship types and capabilities
The game must model ship classes with distinct features, including:

- carriers / carrier escorts
- battleships
- cruisers
- destroyers
- transports and auxiliaries
- plane-carrying ships with launch capacity

### REQ-07.03: Air formation model
Each air formation must include:

- owning side
- aircraft types and counts
- altitude state
- location
- mission status
- launch origin
- landing requirement and eventual landing destination

### REQ-07.04: Base model
Each base must include:

- operational capacity
- launch factor
- grounding and readiness state
- aircraft present and damaged state
- repair state
- anti-aircraft and surface factors

### REQ-07.05: Air factor model
Each air factor represents an individual aircraft unit of a named plane type and must carry:

- plane type
- side
- altitude
- armed or unarmed status
- movement factor
- range factor / endurance score
- current status: ready, readied, just landed, in flight, dispersed

## 8. Air Operations and Flight-Endurance Requirements

### REQ-08.01: Launch factor and capacity
The system must track:

- maximum capacity of a ship or base
- launch factor (LF) at minimum, normal, and maximum launch levels
- the rule that launch factor can be reduced by damage

The digital rules engine must enforce that the total number of aircraft taking off and landing at a ship or base does not exceed that unit’s launch factor.

### REQ-08.02: Readiness progression
Aircraft on ships and bases must move through readiness states correctly:

- just landed
- readied
- ready
- air formation box

The system must enforce the rule that an aircraft cannot be in more than one readiness state at the same time and that aircraft may not exceed the readiness movement limit for the turn.

### REQ-08.02a: Air operations assignment workflow
The air-operations UI must let the player select individual aircraft groups or partial counts from the Ready area and assign them to a numbered Air Formation. The player must be able to:

- choose the Air Formation number from the available 1-35 range
- choose how many factors of each aircraft type to add
- see the remaining Ready count and remaining LF before committing
- add more than one aircraft type to the same formation
- remove or reduce a pending selection before committing
- create the formation only when at least one factor is selected

Creating the formation must move the selected factors out of Ready, consume the applicable launch factor, register the formation, and make it available for the plane movement phase.

### REQ-08.02b: Aircraft armament selection
Before an aircraft group is committed to an Air Formation, the player must be able to select its armament from the legal options for that aircraft: General Purpose bomb (`GP`), Armor Piercing bomb (`AP`), torpedo, or unarmed where permitted. The selected armament must be visible in the operations chart and must affect whether the aircraft is treated as armed, its mission role, attack eligibility, and later combat resolution.

### REQ-08.02c: Readying actions
The player must be able to select aircraft in Just Landed and move them to Readying, and select aircraft in Readying and move them to Ready, subject to the remaining Readying Factor. The UI must show pending readiness moves and commit them together through an explicit action.

### REQ-08.03: Launch type behavior
The system must support three launch behaviors:

- minimum launch: full movement allowed
- normal launch: half movement allowed
- maximum launch: no movement allowed

### REQ-08.04: Flight endurance / fuel logic
Each plane has a range factor (RF) that functions as a flight-endurance or fuel limit. The system must track the number of turns an aircraft can remain in flight and must require each aircraft to land by the turn derived from its RF value.

The rule source states that the plane must be assigned a landing turn based on the RF count and the turn of takeoff. If the aircraft remains airborne past its assigned landing window, it is considered to have failed to land safely and becomes ineligible for continued flight.

### REQ-08.05: Landing restrictions
Aircraft may only land at a valid base or plane-carrying ship with available capacity. Landing is not allowed at any arbitrary location.

### REQ-08.06: Night landing safety
For night turns, the engine must apply night landing chart effects. If an aircraft lands during a night turn and the roll indicates loss, the plane is eliminated.

### REQ-08.07: Off-map flight entry and exit
The game must support off-board bases and entry-hex movement patterns. Aircraft may enter the map only through defined entry hexes and may exit only through valid off-map landing rules.

### REQ-08.08: Altitude model
The system must support high and low altitude states, including:

- altitude-specific movement rules
- interception based on matching altitude
- combat restrictions based on altitude
- altitude changes only permitted in certain movement contexts

## 9. Observation and Hidden Information Requirements

### REQ-09.01: Hidden unit tracking
The system must track hidden enemy assets on the plot map and reveal them only when observable according to the rules.

### REQ-09.02: Observation conditions
The engine must model the condition levels for observation:

- Condition 1: something is present, but not exact numbers
- Condition 2: counts by formation or unit class, with some reporting tolerance
- Condition 3: exact numbers, classes, and compositions

### REQ-09.03: Radar exception
Ships and bases with radar must enable improved observation for high-altitude air units, but radar does not reveal low-altitude aircraft in the same way.

### REQ-09.04: Player knowledge boundary
The game must maintain the rule that players are not always told exact names or counts of ships and planes unless the observation condition and combat state permit disclosure.

### REQ-09.05: Mapboard versus plot map
The game must distinguish between known visible units on the map and hidden units retained on the plot map until observed.

## 10. Combat Requirements

For the complete player-facing and implementation-facing combat explanation, see [COMBAT_RULES.md](COMBAT_RULES.md). That reference defines BHT, Result Numbers, die adjustments, modifiers, combat sequencing, and hit application.

BHT means Basic Hit Table. It identifies the Combat Results Table column used with the number of attacking factors; it is not itself a number of hits. The final BHT is bounded from 1 through 15 before the Result Number is looked up.

### REQ-10.01: Combat phase structure
Each battle must resolve in an ordered sequence:

1. air-to-air combat
2. anti-aircraft combat
3. air attack combat
4. surface attack combat

### REQ-10.02: Air-to-air combat
The engine must support:

- interceptors attacking escorts
- interceptors attacking bombers
- escort and bomber differentiation
- altitude matching rules
- BHT modifications for RF expenditure, clouds, night, and armed aircraft types

### REQ-10.03: Anti-aircraft combat
The system must apply anti-aircraft fire to bombers attacking ships or bases, consistent with the rule that bombers may be fired on before their bombing attack resolves.

### REQ-10.04: Air attack combat
The engine must support dive bombing, torpedo bombing, and level bombing with the correct attack restrictions and RF consumption.

### REQ-10.05: Surface attack combat
The engine must support ship-versus-ship combat, including:

- gunnery combat
- torpedo combat
- breakthrough combat
- bombardment attack against bases
- concealed ship setup and reveal timing

### REQ-10.06: Combat outcomes and hits
Whenever combat resolves, the engine must:

- compute hits according to the combat result table
- apply modifiers cumulatively
- handle fractional or modified BHT values correctly
- resolve damage after evaluating the whole attack group

### REQ-10.07: BHT and Combat Results Table transparency
The game must treat Basic Hit Table (BHT) as the table column used to resolve an attack, not as a hit count. For every attack, the rules engine and combat log must retain:

- base BHT
- all applicable modifiers and their reasons
- final BHT, bounded to 1 through 15
- attacking factor count
- Combat Results Table Result Number
- die result
- final hit count

The Combat Results Table must be represented as 15 BHT rows and exactly 14 attack-factor columns covering 1-2, 3-4, 5-6, 7-8, 9-10, 11-12, 13-15, 16-20, 21-24, 25-30, 31-35, 36-40, 41-45, and 46-plus. Attack factors must be summed only for the declared attack. Totals 24 and 25 must resolve to their respective adjacent ranges, 21-24 and 25-30.

The source-equivalent range data is `[(1, 2), (3, 4), (5, 6), (7, 8), (9, 10), (11, 12), (13, 15), (16, 20), (21, 24), (25, 30), (31, 35), (36, 40), (41, 45), (46, 999)]`.

The engine must apply the die conversion correctly: 1 means Result Number -2, 2 means -1, 3 or 4 means unchanged, 5 means +1, and 6 means +2. A `*` table result produces one hit only on a 6. Negative hits become zero.

### REQ-10.08: Combat step ordering
The engine must resolve each battle in this order: air-to-air, anti-aircraft, air attack, and surface attack. It must enforce the relevant declaration locks, simultaneous-loss timing, altitude separation, RF expenditure, ammunition expenditure, and one-round-per-combat-type limit.

The surface-combat portion must explicitly support gunnery, torpedo, breakthrough, and bombardment combat. Damage application must then update aircraft losses, ship hits and sinking, base hits, movement factor, launch factor, AA, gunnery, carried aircraft, ammunition, and torpedo availability as applicable.

### REQ-10.09: Combat verification
The test suite must verify BHT meaning and bounds, Result Number lookup, die conversion, air-to-air, anti-aircraft, air attack, surface combat, damage application, RF expenditure, and persisted combat events.

## 11. Damage, Repair, and Unit Degradation Requirements

### REQ-11.01: Ship damage model
Hits on ships must be recorded as damage markers; if the accumulated hits equal the ship’s damage factor, the ship is sunk.

The engine must implement:

- movement factor reduction when damage reaches half the ship’s damage factor
- crippled ships becoming dead in the water when one hit short of sinking
- gunnery and AA reduction by damage
- launch factor reduction on carriers and battleships
- elimination of one air factor on plane-carrying ships per hit

### REQ-11.02: Base damage model
Base damage must be tracked separately from ship damage and must support:

- LF reduction by damage
- AA factor reduction
- surface factor reduction
- negative LF values when damage exceeds the zero threshold
- Victory Point tracking while LF is zero or less
- no takeoff from a base with LF of zero or less

### REQ-11.03: Repair model
Damaged bases may be repaired during the repair phase, with one hit repaired per base per turn unless the scenario says otherwise.

The system must enforce:

- repair occurs only during the repair phase
- repair is prevented if the base was involved in air attack combat or bombardment combat that turn
- a base cannot be repaired to exceed its original scenario specifications

### REQ-11.04: Damage-to-air factor elimination logic
When a ship or base takes hits, the engine must eliminate aircraft in the correct order:

1. ready aircraft first
2. just-landed aircraft next
3. readied aircraft next
4. dispersed aircraft last, at one aircraft per two hits

This elimination order must respect the rule that the attacker or defender chooses which plane names are eliminated depending on the combat context.

### REQ-11.05: Plane losses and replacements
The system must support daily reinforcements based on losses from the previous day. For every three aircraft of the same name eliminated, one may return as replacement, with fractions lost.

### REQ-11.06: Sunk plane-carrying ship rule
If a plane-carrying ship is sunk, all aircraft on it are immediately lost and cannot be used as replacements.

## 12. Fleet and Air Movement Requirements

### REQ-12.01: Task-force movement
Task forces must be able to:

- move during plotting and execution phases
- combine or split without movement cost when in the same hex during the task-force movement phase
- exit the mapboard only at valid edges, with the unit removed from play and VP recorded as appropriate

### REQ-12.02: Aircraft movement
Aircraft movement must obey:

- movement points per hex
- the slowest air factor determines movement within the formation
- unused movement is lost and not carried over
- movements can be in any direction but cannot skip hexes
- formations may reorganize when in friendly base or carrier hexes

### REQ-12.03: Mission restrictions
The engine must prevent illegal mission assignments such as:

- bombing without bomb load or proper aircraft type
- torpedo attack from unsupported aircraft type or altitude
- fighter interception when planes are not at matching altitude

## 13. Victory Conditions and Scoring Requirements

### REQ-13.01: Victory points system
The game must maintain a score for both sides using the victory-point table. Scores may be earned for:

- sunk enemy ships
- destroyed air units
- transports unloading cargo
- other scenario-specific objectives

### REQ-13.02: Automatic victory threshold
The engine must support scenario-specific automatic victory point thresholds evaluated at the end of the 2400 turn.

### REQ-13.03: Minimum score rule
If no automatic victory occurs, the winner must be the player with the most points, but only if that player has at least 50 points. If neither player reaches 50 points, the result is a draw.

### REQ-13.04: Unnecessary air-factor loss penalty
The engine must track expensive air losses where the aircraft are lost unnecessarily because the player failed to land them safely by their landing turn. This is scored at 10 Victory Points per aircraft rather than the normal 2.

### REQ-13.05: Transport unload scoring
The engine must award Victory Points each turn an amphibious transport unloads, up to the scenario-defined maximum, while also reducing the sunk-value value of the transport proportionally.

## 14. AI Requirements

### REQ-14.01: Rule-compliant AI
The computer player must obey the same rules and phase sequence as a human. It may not use hidden information beyond what has been legally observed.

### REQ-14.02: Mission prioritization
The AI must decide among valid actions using strategic rules such as:

- priority on defending high-value assets
- offensive opportunities against observed targets
- intercepting enemy bombers or attackers
- preserving aircraft and airfields
- reacting to weather and visibility constraints

### REQ-14.03: Tactical judgement
The AI must evaluate:

- relative force strength
- target value
- damage state and cripple conditions
- likely enemy actions
- mission completion requirements

### REQ-14.04: Limited information handling
The AI must operate under incomplete information and maintain uncertainty estimates when enemy units are hidden or only partially observed.

### REQ-14.05: Difficulty levels
The game must support multiple AI difficulty levels, each modifying:

- risk tolerance
- target selection quality
- availability of tactical opportunism
- willingness to engage or withdraw

## 15. User Interface and Usability Requirements

### REQ-15.01: Map readability
The player must be able to see the board, unit positions, weather markers, and highlighted legal actions without confusion.

### REQ-15.02: Unit detail panel
The UI must show relevant values for selected units, including:

- unit type
- side and name
- location
- movement capability
- launch or combat factors
- damage state
- readiness state
- legal actions available this phase

### REQ-15.03: Action feedback
If a move or action is illegal, the UI must provide a concise reason. Examples include invalid launch factor, impossible landing, out-of-range attack, or action outside the current phase.

### REQ-15.03a: Piece selection and context menu
Clicking a visible map piece must open a context action menu rather than immediately executing or bypassing interaction. The menu must be generated from the selected piece, current phase, side, and nearby pieces.

The menu must support:

- Details for bases, task forces, and air formations
- Move for movable friendly units in the applicable movement phase
- Land for an air formation in a friendly base or plane-carrying task-force hex when legal
- Combat when an eligible opposing unit occupies the same hex during Combat
- Cancel

Right-click or an equivalent secondary action may open details directly. Clicking an empty map hex must begin map pan/drag behavior when no action target is present. When multiple pieces share a hex, the UI must first present a piece-selection list.

### REQ-15.04: Combat log
The UI must present a readable combat log for each battle, summarizing hits, unit losses, and resulting damage states.

### REQ-15.05: Hidden information representation
The UI must distinguish clearly between:

- definitely known enemy units
- uncertain or partially observed enemy units
- hidden enemy units that are not yet revealed

### REQ-15.06: Turn state presentation
The UI must show the current turn, current phase, whose turn it is, and whether the game is waiting for the human or the AI.

## 16. Non-Functional Requirements

Combat resolution records, score events, and authoritative state transitions must be persisted sufficiently to support save/load, replay, audit, and deterministic debugging.

### REQ-16.01: Rule transparency
The game should help the player learn the rules by surfacing legal actions and by making damage, readiness, and flight-endurance states explicit.

### REQ-16.02: Determinism and reproducibility
Deterministic cases should be reproducible whenever the same seed or scenario state is used. Randomized combat should still be visibly logged.

### REQ-16.03: Extensibility
The game rules engine must be extensible enough to support multiple scenarios and future rule adjustments without rewriting the entire system.

## 17. Acceptance Criteria

The implementation is considered complete when the following behaviors are true:

1. A player can select a scenario and start a full game.
2. The turn order is enforced without skipping or reordering phases.
3. Aircraft must be launched only with valid capacity and flying rules.
4. Aircraft that exceed their range/endurance requirements are treated as incapable of safely continuing flight.
5. Hits on ships reduce movement, gunnery, anti-aircraft, and launch capability exactly according to the rule model.
6. Bases can be damaged, lose LF/AAF/SF, and repair only under correct phase and attack conditions.
7. Combat results are resolved in the correct sequence and all modifiers are applied.
8. Observation preserves hidden information and only reveals units legally observable.
9. Victory points are scored and tracked correctly for sunk ships, air losses, and unload actions.
10. The AI can complete a full turn using valid decisions under the same rules as a human player.

## 18. Summary

The game must be played as a modern digital naval-air strategy game, but it must remain faithful to the structural logic of the original rules. The rule source is very explicit on damage, repair, launch factor, flight range, and victory scoring. A compliant implementation must treat these as first-class gameplay systems, not optional detail. They are central to the game’s tactical and strategic identity.
- readiness matters
- combat decisions have real consequences

### RULE-02: Simplification is allowed only where it improves usability
The game may streamline minor bookkeeping or edge-case rule detail, but not the central strategic logic of movement, observation, aircraft operations, and combat.

### RULE-03: Critical decisions must remain understandable to players
Players must understand why an action is legal or illegal, and why a battle outcome occurred, without depending on hidden internal calculations.

---

## 10. Non-Functional Requirements

### NFR-01: Validity and stability
The game must not enter invalid states. All actions, combat resolutions, and turn transitions must remain coherent and consistent.

### NFR-02: Responsiveness
The system must respond quickly to actions, map browsing, and combat resolution without frustrating delays.

### NFR-03: Platform flexibility
The design must be generic enough to support desktop or web deployment without assuming a single platform-specific architecture.

### NFR-04: Save and restore behavior must remain consistent
A saved game must preserve the current game state accurately enough to continue without corruption.

---

## 11. Acceptance Criteria

A successful implementation satisfies the following:

1. A player can choose a scenario and begin a game.
2. A player can play as either side.
3. A player can play against another human or the computer.
4. The UI clearly indicates the current phase and side.
5. The player can inspect units and legal actions.
6. Invalid actions are prevented or explained.
7. Combat results are visible and understandable.
8. Observation and hidden information work according to the rule spirit.
9. The AI makes legal, rational decisions and behaves like a serious opponent.
10. The game supports multiple scenarios and continues from a valid game state.

---

## 12. Final Design Direction

This requirements set is intentionally built for a digital game rather than a literal tabletop reproduction. It is suitable for:

- product design documentation
- engineering implementation planning
- AI behavior specification
- UI workflow definition
- future game iteration and expansion

It captures the major gameplay and usability goals while staying flexible enough for either desktop or web delivery.
