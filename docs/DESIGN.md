# 1942 Flattop Detailed Design

## 1. Design Objective

This document defines the design for a digital implementation of 1942 Flat Top that remains faithful to the rule spirit of the original naval-air wargame while being playable and understandable as a computer game. The design is grounded in the original board-game model but is intentionally framed as a digital strategy game rather than a literal tabletop reproduction.

Unit attributes and source-data validation are specified in [UNIT_DATA_SPEC.md](UNIT_DATA_SPEC.md). The design must use that catalog rather than duplicating aircraft or ship statistics in UI, AI, or scenario code.

The implementation must support:

- human-vs-human gameplay
- human-vs-computer gameplay
- multiple scenarios
- serious turn-based strategic play
- hidden information and observation
- air and naval combat resolution
- rule-based AI competitor behavior

## 2. Design Principles

### 2.1 Rule spirit over literal tabletop fidelity
The product must preserve the strategic logic of the game: aircraft endurance, fleet composition, airfield pressure, indirect damage, weather effects, and score-based victory. The application does not need to recreate every physical board-game convention, but it must preserve the causal rules that define play.

### 2.2 Human usability over rulebook memorization
The digital game must surface the current state, legal moves, and system consequences in a format that a human player can act on without memorizing the entire rulebook.

### 2.3 Hidden information is core gameplay
Observation and partial intelligence are not a UI gimmick; they are part of the tactical identity of the game. The design must deliberately preserve that uncertainty and its consequences.

### 2.4 Damage must matter continuously
The design treats damage as a permanent operational reducer, not just a surface label. A damaged ship or base changes movement, combat power, launch capacity, and tempo of play.

### 2.5 Victory is score-driven and scenario-driven
The game must track strategic value beyond just “who still has units.” The victory-point system is a central mechanism and must be visible, enforceable, and explainable.

## 3. Product Scope

### 3.1 In scope

- two-sided strategic war game with Japanese and Allied forces
- scenario-based play
- hex-based map and movement
- task force management and ship composition
- air formation launches, movement, and landing
- combat between planes, ships, and bases
- weather, clouds, storms, and visibility impacts
- damage, repairs, replacements, and point tracking
- AI-controlled opponent

### 3.2 Out of scope for the initial release

- exact physical board game reproduction
- literal raw table lookups for every unneeded edge case
- complex historical card or counter management that is not essential to play
- fully simulating every board-game edge case if digital simplification improves clarity

## 4. High-Level System Architecture

The implementation should be organized around a rule engine and a presentation layer.

### 4.1 Core subsystems

1. Scenario loader and setup subsystem
2. Turn controller and phase engine
3. Unit state model and command validation layer
4. Movement and pathfinding subsystem
5. Combat resolver
6. Damage and repair subsystem
7. Observation and hidden-information subsystem
8. Victory-point and endgame evaluation subsystem
9. AI decision engine
10. User interface and interaction layer

### 4.2 Architectural separation
The design must keep rules logic separate from UI logic so the same engine can run with multiple UI front ends, from desktop to web.

## 5. Core Domain Model

### 5.1 Side
The game always has two sides:

- Japanese
- Allied

Each side has force composition, scenario setup, AI control state, and point totals.

### 5.2 Map
The map is a hex-based environment containing:

- sea hexes
- land and partial-land hexes
- island and base locations
- weather markers
- sectors and directional wind markers

The map supports adjacency, movement, and through-hex combat resolutions.

### 5.3 Task Force
A task force is a grouping of ships acting as one operational unit for movement and target assignment.

Required properties:

- ship list
- owning side
- location
- movement factor
- current observed status
- damage state
- composition restrictions

### 5.4 Ship
Ships must include:

- name and type
- gunnery factor
- torpedo factor
- AA factor
- movement factor
- damage factor
- launch factor where applicable
- status: anchored, crippled, sunk, screened, etc.

### 5.5 Base
Bases are strategic support points and possible combat targets.

Required properties:

- base name and side
- launch factor (LF)
- anti-aircraft factor
- surface factor
- aircraft capacity
- damage count
- repair state

### 5.6 Air Formation
Air formations must hold aircraft grouped into a coherent mission unit.

Required properties:

- side
- aircraft list and counts by plane type
- altitude state
- location or in-flight state
- take-off origin
- landing requirement
- armed or unarmed status
- mission type

### 5.7 Air Factor
Each air factor is a plane unit and carries plane-specific metadata:

- plane name
- side
- altitude
- readiness state
- range factor
- bomb load and armament
- movement factor
- current aggression or interception role

## 6. Turn Engine Design

### 6.1 Turn structure
The turn engine must be the authoritative controller of game flow and phase validity. It must:

- validate phase transitions
- lock actions to legal timing
- resolve simultaneous phases and sequential movement phases correctly
- maintain the initiative state

### 6.2 Initiative logic
During the initiative phase, each side rolls a die. Higher roll wins. Ties resolve via the rule that the player who did not hold initiative last turn wins the next initiative.

The initiative determines who moves aircraft first in the plane movement phase.

### 6.3 Phase ordering and validation
The system must enforce strict order, because several rules depend on the fact that players are not allowed to act outside the proper phase. Each phase must be represented as a state machine rather than a free-form action queue.

## 7. Weather and Map State Design

### 7.1 Weather system
Weather should be modeled as a first-class game system with a state object representing:

- wind direction by sector
- cloud markers and their placement
- storm regions created by marker overlap
- seasonal or scenario-specific weather state

### 7.2 Storm logic
The design must compute whether a hex is a storm hex and propagate that to movement and observation logic. Storms must affect:

- aircraft flight restrictions
- ship movement restrictions
- concealed movement and observation
- combat prohibition

### 7.3 Observation effect
The observation model must check weather and map state before revealing information. Cloud or storm state modifies search outcome or the quality of intelligence.

## 8. Movement Design

### 8.1 Task-force movement
Task Force movement must use movement factors and valid pathing rules. Movement is not just a single unit relocation; it must account for:

- stacking and grouping rules
- movement in hex grid
- integrating multiple ship classes in one TF
- restricting movement when ships are crippled or damaged

### 8.2 Aircraft movement
Aircraft movement uses aircraft movement factor and altitude. The formation MF is determined by the slowest air factor in the formation. Unused movement is lost; it is not carried over.

### 8.3 Fuel / range factor model
The design introduces a numerical range factor for each aircraft. This acts as the game’s fuel/endurance representation.

Design mapping:

- each aircraft has a landing deadline based on its RF and launch turn
- the system keeps a per-plane “must land by” turn
- if the aircraft is still in flight after that turn and lacks a valid landing opportunity, it is treated as lost or as an invalid flight state

This is the digital translation of the board-game rule that aircraft cannot remain airborne indefinitely and must eventually land or be lost.

### 8.4 Launch types
The system must support minimum, normal, and maximum launches with different movement consequences.

- minimum launch: full movement allowed
- normal launch: half movement allowed
- maximum launch: no movement allowed

The digital engine must calculate and display these constraints so the player can understand the tradeoff between tempo and launch volume.

### 8.5 Formation construction and armament

Air Operations is an authoring phase as well as a status view. The player constructs numbered formations by selecting aircraft factors from Ready groups, selecting a count, selecting legal armament, and committing the formation. One formation can contain multiple aircraft types.

The operations chart presents two explicit budgets above the aircraft lanes: remaining Launch Factor for the selected carrier/base and remaining Readying Factor for the turn. Launch Factor is consumed by committed takeoffs/landings; Readying Factor is consumed by queued movement between Just Landed, Readying, and Ready. Both budgets are validated by the rules engine, not inferred by the client.

The operations workflow must maintain a pending assignment model until commit. On commit it must:

- remove selected factors from Ready
- consume the corresponding launch factor
- assign the formation number and launch origin
- preserve armament per aircraft group
- make the formation available to the movement phase

Armament options are `GP`, `AP`, `Torpedo`, and unarmed where the aircraft and situation allow. Armament determines whether aircraft are armed bombers, what attacks they can perform, and whether fighter aircraft are treated as escorts or interceptors.

### 8.6 Readying and recovery controls

The operations chart must support pending readiness transitions from Just Landed to Readying and from Readying to Ready. These transitions consume Readying Factor, cannot move an aircraft more than once in the same turn, and must be committed as an explicit readiness action. Recovery must place aircraft in Just Landed before they can be readied again.

The aircraft combat-values table is the single control surface for these transitions. Each row exposes state-appropriate plus/minus controls: Ready `+` assigns factors to the pending formation, Ready `-` removes pending formation factors, Just Landed `+` moves factors to Readying, Readying `+` moves factors to Ready, Readying `-` moves factors back to Just Landed, and Ready exposes a reverse move to Readying. Armament is editable only in the Readying row; Ready aircraft show a locked armament value and can be selected for formation construction. The chart must make the disabled state and the reason visible when an adjustment would exceed Readying Factor or Launch Factor.

## 9. Combat System Design

The detailed combat rules reference is [COMBAT_RULES.md](COMBAT_RULES.md). It is the shared explanation for the UI, AI, rules engine, and test plan.

### 9.1 Combat resolution architecture
Combat resolution should be driven by a shared battle object that records:

- battle location
- participating side units
- target assignments
- altitude separation
- weather modifiers
- result tables and BHT calculation

The design should avoid ad hoc combat rules spread across UI logic. Combat logic belongs in the rules engine and should be reproducible by logs and replays.

### 9.2 Air-to-air combat flow
The battle engine must implement the following sequence:

1. assign interceptors and escorts
2. determine altitude match
3. resolve interceptor-to-escort combat
4. resolve bomber-attack sequencing and escort logic
5. apply RF expenditure and unit removal

### 9.3 Anti-aircraft flow
The engine must resolve anti-aircraft fire before bombs actually hit targets. This matters because bombers may be reduced before hitting the base or ship they are attacking.

### 9.4 Air attack and surface attack flows
Air attack combat should distinguish among:

- dive bombing
- level bombing
- torpedo bombing

Surface attack combat should resolve gunnery combat, torpedo combat, breakthrough combat, and optional bombardment against bases.

### 9.5 BHT resolution model

BHT means Basic Hit Table. It identifies the Combat Results Table column used for an attack; it is not itself a number of hits. The rules engine must calculate a base BHT, apply every relevant modifier cumulatively, clamp the final value to 1 through 15, and then cross-index that final BHT with the number of attacking factors to obtain a Result Number.

One die modifies the Result Number as follows:

- 1: minus 2
- 2: minus 1
- 3 or 4: unchanged
- 5: plus 1
- 6: plus 2

Negative results produce zero hits. A `*` result produces one hit only on a 6. The engine must retain each intermediate value for the combat log and replay.

The BHT bounds are 1 through 15: the final modified BHT must never be below 1 and values above 15 are treated as 15. The Result Number is looked up using the final BHT and number of attacking factors before applying the die conversion.

### 9.6 Combat sequence and damage application

Each battle resolves air-to-air combat, anti-aircraft combat, air attack combat, and then surface attack combat. Air combat is separated by altitude. AA declarations lock air-attack allocations before AA losses are applied. Surface combat hides ship-position assignments until both sides commit, then resolves gunnery, torpedo, and eligible breakthrough attacks.

Hits are applied according to target type: aircraft are eliminated by hits, ship hits accumulate toward damage and sinking, and base hits reduce LF, AA, and SF. Damage to plane-carrying units also applies the rule-defined aircraft elimination order and may double applicable bombing damage.

### 9.7 Combat Results Table data design

The Combat Results Table is versioned rule data with 15 BHT rows and exactly 14 attack-factor columns. The columns are 1-2, 3-4, 5-6, 7-8, 9-10, 11-12, 13-15, 16-20, 21-24, 25-30, 31-35, 36-40, 41-45, and 46-plus. The lookup sums the attack factors assigned to one declared attack, selects the containing range, and retrieves the Result Number at the intersection with the final BHT row.

The source-equivalent range data is `[(1, 2), (3, 4), (5, 6), (7, 8), (9, 10), (11, 12), (13, 15), (16, 20), (21, 24), (25, 30), (31, 35), (36, 40), (41, 45), (46, 999)]`.

The source data now assigns 24 to the 21-24 column and 25 to the 25-30 column. The previous 24-25 unmapped edge case is resolved; the implementation, UI, and AI must use these explicit boundary assignments.

## 10. Damage and Repair Design

### 10.1 Ship damage rules
The damage system must track hits and translate them into actual capabilities.

Required effects:

- accumulate damage markers until the ship sinks
- halved movement factor when damage reaches half the ship’s damage factor
- crippled ship rule when one hit short of sinking
- gunnery and AA degradation by hits
- launch factor degradation for plane-carrying ships

### 10.2 Base damage rules
Base damage must be represented as a numeric sequence of hits, not just as a binary “damaged” flag. It must affect:

- LF
- AA factor
- SF
- aircraft elimination counts

The base can go below zero on certain factors and the game must still enforce that no planes can take off when LF is zero or less.

### 10.3 Repair logic
Repair rules are mechanically important:

- one hit repaired per base per turn unless otherwise specified
- repair is blocked if the base was attacked that turn
- base repair cannot exceed original scenario specifications

This implies the repair subsystem must know whether a base was attacked during the turn, which is a direct dependency of the battle-resolution event log.

## 11. Victory and Points System Design

### 11.1 Score model
The victory-point system should not be implemented as a loose tally. It must be a structured ledger that logs each event causing points, including:

- ship sink value
- transport unload scoring
- unnecessary air-factor loss penalty
- scenario-specific victory conditions

### 11.2 Automatic endgame logic
At the end of the 2400 turn, the game must compare the score difference to the scenario’s automatic victory threshold. A scenario-specific value is required here.

### 11.3 Minimum-score win logic
If no automatic victory occurs, the winner is the side with the most points, but only if that side has at least 50 points. Otherwise the game ends in a draw.

### 11.4 Unnecessary loss logic
The design must support a penalty when aircraft are lost for operational errors or failure to land; these losses are scored at 10 points each instead of the base 2-point value.

This rule is important because it makes route planning and landing discipline a real tactical concern rather than just a bookkeeping afterthought.

## 12. Observation and Hidden Information Design

### 12.1 Observation state model
Observation must be implemented with a hidden state per unit to track:

- observed or hidden
- which side can see it
- condition number
- what details are disclosed

### 12.2 Reporting hierarchy
The reporting system must preserve the original rule distinctions:

- condition 1: presence only
- condition 2: unit or formation counts and classes, with some allowed inaccuracy
- condition 3: exact composition and numbers

### 12.3 UI representation
The UI should not show a hidden unit as a fully visible piece. Instead, it should show either:

- known visible unit
- uncertain contact marker
- hidden but tracked plot-state unit

## 13. AI Design

### 13.1 AI responsibilities
The AI must do the same legal work as a human player:

- plan moves
- launch aircraft
- manage readiness and landing windows
- observe and infer enemy position
- attack valid targets
- take damage and repair logically

### 13.2 AI decision framework
The AI should operate through a decision flow:

1. update known state and hidden-information estimates
2. identify friendly force priorities and strategic goals
3. generate legal actions for each unit
4. score each legal action
5. choose the highest-scoring action or action group

### 13.3 Strategic priorities for AI
The AI should weight decisions using:

- air superiority and interception opportunities
- damage to important ships or bases
- transport unloading pressure
- need to preserve aircraft from avoidable losses
- weather and enemy observation state

### 13.4 Difficulties
AI skill should not alter the rule set. It should alter:

- tactical foresight
- risk tolerance
- aggressiveness vs caution
- effectiveness at inference and target selection

## 14. UI and Interaction Design

### 14.1 Main UI screens

1. Main menu and scenario selection
2. Game board screen
3. Side panel with selected unit details
4. Combat log and event feed
5. Victory and summary screen

### 14.2 Interaction model
The player should be able to:

- select a unit
- see legal actions for that unit
- commit a move or attack with clear confirmation
- examine damage and launch state at any time
- review hidden information versus known information

Map piece clicks must open a phase-aware context menu. Details, Move, Land, Combat, and Cancel are generated from the piece type, ownership, current phase, co-located units, and observation state. Empty map clicks pan the board. Multiple pieces in one hex require a selection step before the context menu. A secondary click may bypass the action menu for details or observation.

### 14.3 Action validation
Every action must be validated by the rules engine before committing. The UI should handle the result by either:

- accepting the action and updating the board
- blocking the action with readable feedback

### 14.4 Event logging and explainability
The UI must provide a clear history of battle and turn events, so the player can understand why damage, losses, or observation states changed.

## 15. Data and Persistence Design

### 15.1 Scenario persistence
Scenario data should be stored in a structured, readable format that contains all starting forces, condition values, and scenario-specific rules.

### 15.2 Save game model
Save files should preserve:

- current turn and phase
- side to move
- initiative status
- board state and hidden information
- damage and repair counters
- score and endgame state

### 15.3 Replayability
The system should support enough event logging to review a previous battle or step through turn actions for debugging and user learning.

## 16. Testability and Validation

The game should be validated against the rule source using specific rule-based tests, including:

- damage state reduces movement and launch correctly
- aircraft must land or be treated as lost based on ending flight endurance
- base repair only occurs when allowed by the phase and prior attack state
- victory points are scored correctly for sunk ships and transport unloads
- observation adheres to condition number and radar rules
- AI acts only within valid legal game-state constraints

## 17. Implementation Notes

The most important design decision is that the rules engine must be authoritative. The UI and AI may provide convenience, but they may not bypass the rules or implicitly adjust the same logic. A board-game rule is only a good digital game rule if it is consistently enforced in one place and visible to the player.

This project should prioritize a clean rules engine, a transparent UI, and an AI that reasons under the same constraints as the human player.

## 18. Final Design Summary

The digital design for 1942 Flat Top is a rule-respecting, turn-based naval-air strategy game with hidden information, aircraft endurance, ship and base damage, weather, and score-based victory conditions. Every critical board-game mechanism — especially launch factors, flight endurance, damage effects, repair timing, and points tracking — must be translated into the digital engine as first-class game systems rather than treated as optional presentation details.

Purpose:
- explain who attacked whom, what happened, and what changed

### Screen 5: Scenario Summary or End Screen

Purpose:
- show the result and allow replay or restart

---

## 10. AI Design

## 10.1 AI Goals

The AI must act like a competent strategic opponent. It should:

- operate within all core rules
- make choices based on known information
- prioritize tactical value and strategic necessity
- protect key forces and objectives
- search effectively when contact is uncertain
- engage when the action is favorable

## 10.2 AI Decision Categories

### Search
When enemy contact is uncertain, the AI should search strategically rather than move randomly.

### Contact and Engagement
When enemy positions are known, the AI should choose attack or interception actions that maximize value and preserve force integrity.

### Defense
The AI should protect carriers, bases, and task forces that are important to long-term survival and scenario success.

### Resource Management
The AI should manage aircraft readiness, sortie planning, and attack timing in a way consistent with the game systems.

## 10.3 AI Difficulty Model

The AI can use a light skill ladder:

- Beginner: simpler target evaluation and less strategic coordination
- Standard: balanced tactical and strategic behavior
- Expert: more deliberate planning and better risk management

The difficulty system should change decision quality, not game rules.

## 10.4 AI Transparency

The player should be able to understand what the AI is doing at a high level. Examples:

- searching suspected enemy routes
- attacking exposed carrier group
- defending an island base
- prioritizing aircraft launch for intercepts

This does not require fully exposing the AI’s internal calculations, only the meaningful intent behind its actions.

---

## 11. Rule Interpretation and Simplification

The digital version should preserve the key game principles while simplifying detailed bookkeeping.

### 11.1 What Must Remain

- phase structure
- movement rules and legal movement checks
- visibility and observation logic
- aircraft launch and readiness
- task-force deployment and naval operations
- combat participation and consequences
- scenario objective logic

### 11.2 What May Be Simplified

- exact table lookup and notation burden
- board-bookkeeping overhead
- manual tracking of every hidden state that the UI can represent automatically
- some low-level record-keeping if it does not affect user-facing clarity

### 11.3 Rule Spirit Requirement

The product may simplify how a rule is represented, but it must not remove the strategic impact of the rule. For example:

- hidden information must remain an active design element
- air operations must still matter for force projection
- combat must still be consequential
- task-force composition must still affect tactical outcome

---

## 12. Data Model

The game system should organize data into core entities.

### 12.1 Side

- name: Japanese or Allied
- available units
- scenario-specific objectives

### 12.2 Unit

- id
- side
- type
- name
- position
- status
- visibility state
- current group assignment

### 12.3 Task Force

- id
- side
- ships
- current position
- movement state
- combat status

### 12.4 Base

- id
- side
- location
- aircraft available
- readiness state
- damage state

### 12.5 Air Formation

- id
- side
- aircraft composition
- altitude
- current mission or state
- launch source
- movement status

### 12.6 Weather

- current conditions
- wind vector
- cloud pattern
- storm regions

### 12.7 Scenario

- scenario name
- board layout
- side setups
- starting units
- victory condition
- notes and historical context

---

## 13. Validation and Error Handling

### 13.1 Validation Requirements

The system must validate all player and AI actions before applying them. Examples:

- legal board movement
- legal launch based on readiness and capacity
- legal target selection
- legal combat participation
- legal observation range

### 13.2 Error Handling

When an invalid action occurs, the system should:

- prevent the action
- explain the problem in user-friendly terms
- keep the game in a valid state

### 13.3 Logging and Debugging

The system should log:

- turn number and phase
- action attempted
- actor and target
- reason for invalid action
- final state post-resolution

---

## 14. Persistence and Save/Load

The game should support save and restore of the current state.

Required persistence behavior:

- save the current scenario and turn state
- save unit positions, attributes, and readiness
- save weather and hidden information state
- preserve AI state where needed
- restore without invalidating the game state

---

## 15. Acceptance Criteria

The design is successful if the product can meet the following outcomes:

1. A player can choose a scenario and start a game.
2. A player can play as either side.
3. A player can play human-vs-human or human-vs-computer.
4. The UI clearly communicates turn order and phase state.
5. Players can inspect units and legal actions.
6. Combat outcomes are understandable and visible.
7. Observation and hidden information are preserved.
8. The computer opponent behaves like a competent strategic player.
9. Multiple scenarios can be supported without redesigning the system.
10. The game uses a digital design that maintains the historical strategic feel of the original.

---

## 16. Implementation Outlook

This design supports a modular build:

- rules engine for legality and resolution
- board and map model for terrain and movement
- scenario manager for historical setups
- UI layer for map, panels, and actions
- AI layer for decision-making and validation
- persistence layer for save/load

This separation allows the system to be implemented in a platform-neutral manner, whether the final product is a desktop app or a web application.

---

## 17. Summary

The 1942 Flattop digital game should be a playable, understandable, and strategically rich computer wargame. It must preserve the spirit of the original naval-air conflict while using digital tools to simplify bookkeeping, expose hidden information correctly, and provide a credible AI opponent.

The design centers on a simple principle:

- make the game understandable to a human
- keep the rules valid and coherent
- let the AI act as a serious and legal opponent
- deliver a satisfying strategic experience across multiple scenarios
