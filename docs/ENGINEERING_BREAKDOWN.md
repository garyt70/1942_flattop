# 1942 Flattop Engineering Breakdown

## 1. Purpose

This document turns the gameplay requirements and UI specification into a platform- and language-neutral implementation plan. It identifies the capabilities to build, the responsibilities and contracts of each subsystem, their dependencies, the recommended delivery order, and the tests required to prove the rule behavior.

The current repository is one possible prototype, but the target implementation may be a web application or another client/server product. This document therefore specifies domain capabilities, interfaces, state boundaries, and deployment concerns without requiring Python, a particular frontend framework, a particular database, or a particular hosting model.

## 2. Implementation Strategy

Build from the rules engine outward:

1. establish authoritative state and command validation
2. implement the turn and phase lifecycle
3. make movement, readiness, endurance, damage, repair, combat, and scoring deterministic and testable
4. expose legal commands to both the human UI and AI
5. build the UI around those commands
6. harden AI behavior and persistence after the full rules loop works

The same command and validation path must be used by the human player and computer opponent. The UI must never implement rules independently, and the AI must never bypass validation.

## 3. Capability and Service Map

The implementation may be a monolith, modular service, or client/server system. These are logical boundaries, not mandatory deployment units.

| Capability | Responsibility | Required contract |
|---|---|---|
| Game state store | authoritative scenario, turn, unit, weather, knowledge, combat, and score state | load, validate version, read state, apply a committed transition |
| Turn coordinator | strict phase state machine, turn clock, initiative, phase transitions | current phase, legal phase transitions, phase status |
| Command boundary | player and AI intents | submit command, return validation result or committed event sequence |
| Rule validation | phase-aware legality and human-readable reasons | deterministic validation against a state snapshot |
| Movement capability | hex paths, terrain, storm, MF, launch, entry, and exit restrictions | legal paths and movement consequences |
| Air operations capability | readiness, launch/recovery, LF, MC, RF, altitude, payload | legal operations and updated air state |
| Observation capability | hidden state, contacts, condition levels, radar, disclosure | side-filtered knowledge projection |
| Combat capability | BHT, combat sequencing, dice, hits, losses, damage | auditable combat result and state events |
| Damage and repair capability | degradation, aircraft elimination, repair eligibility | effective capabilities and repair transitions |
| Victory capability | event ledger, transport scoring, automatic victory, final result | score events, totals, endgame decision |
| AI capability | legal action generation, evaluation, uncertainty handling | commands submitted through the same command boundary |
| Presentation adapter | map, panels, logs, notifications, input workflows | render side-filtered projections and submit commands |
| Persistence adapter | save/load, replay, deterministic continuation | versioned state and event serialization |

The current prototype files can map onto these capabilities, but the target design must not require those filenames or a Python runtime. A web implementation may expose the command boundary through HTTP, WebSocket, or another transport; a desktop implementation may call the same boundary in-process.

## 4. Authoritative State Model

Before adding more UI behavior, define the state that must survive save/load and be visible to rule tests.

### 4.1 Game state

The game state must contain:

- scenario identifier and special rules
- current turn and time
- active phase
- initiative holder and previous initiative holder
- board and weather state
- both sides' units
- hidden-information state for each side
- pending plots and commitments
- combat state when a battle is in progress
- score ledger and current totals
- replacement and daily-loss tracking
- deterministic random state when configured

### 4.2 Unit state

Task forces, ships, bases, air formations, and air factors need stable identifiers. State must distinguish original values from effective values so damage can be applied and repaired correctly.

Examples:

- `original_mf` and `effective_mf`
- `original_lf` and `effective_lf`
- `damage_hits`
- `damage_factor`
- `crippled`
- `ready`, `readying`, `just_landed`, `dispersed`, or `in_flight`
- `takeoff_turn` and `must_land_by`
- `observed_by_side` and condition number

## 5. Phase and Command Layer

### 5.1 Turn coordinator

Implement:

- the ten required phases
- phase transition validation
- simultaneous versus sequential phase behavior
- initiative rolls and tie handling
- day/night lookup
- end-of-turn and end-of-game hooks

The turn engine should expose a read-only phase status object for UI and AI.

### 5.2 Command boundary

Define commands for all meaningful actions, including:

- advance phase
- move task force
- combine or split task forces
- search
- shadow
- move air formation
- launch aircraft
- land aircraft
- reorganize air formations
- change altitude
- jettison bombs
- initiate interception
- declare air attack
- declare surface attack
- assign ships to gunnery, torpedo, or screen
- select aircraft losses when permitted
- repair base
- scuttle ship
- save game

Commands must contain intent and references, not UI-specific objects.

### 5.3 Rule validation

Every command must be checked for:

- active phase
- acting side
- unit ownership
- unit status
- location and path legality
- capacity and factor limits
- hidden-information permissions
- target eligibility
- movement and endurance constraints

The validator should return structured errors with a stable code and readable message. Examples:

- `WRONG_PHASE`
- `NOT_OWNER`
- `INSUFFICIENT_LF`
- `NO_VALID_LANDING`
- `RF_DEADLINE_EXCEEDED`
- `STORM_HEX`
- `TARGET_NOT_OBSERVED`
- `BASE_ATTACKED_THIS_TURN`

### 5.4 Transition executor

Apply only validated commands. Each execution must:

1. capture the pre-action state needed for logging
2. mutate authoritative state
3. emit structured events
4. update knowledge and score consequences
5. expose the next legal action state

## 6. Air Operations Implementation

### 6.1 Air operations capability

Implement:

- maximum capacity
- minimum, normal, and maximum launch
- launch and landing LF accounting
- Readying Factor limits
- one-state-per-air-factor rule
- aircraft arming and payload state
- formation creation, splitting, and reorganization
- altitude changes
- off-map entry and exit timing
- night landing resolution

### 6.2 RF endurance and fuel tracking

For every air factor in flight:

1. record takeoff turn
2. calculate the landing deadline from its RF
3. reduce the deadline when combat consumes RF
4. require the formation to reach a valid landing or entry state
5. classify failure to land as an unnecessary loss when the rules require it

Mixed formations must retain separate deadlines by aircraft type or flight group. The engine must not collapse them into a single deadline unless all constituent factors share the same deadline.

### 6.3 Readiness transitions

Implement the legal transitions:

- Just Landed -> Readying
- Readying -> Ready
- Ready -> Air Formation
- Ready -> Readying
- Readying -> Dispersed or Undispersed where legal

Enforce that one air factor cannot make more than one readiness move per turn and that the total moves do not exceed the location's Readying Factor.

## 7. Movement, Weather, and Observation

### 7.1 Movement ownership

The board/pathfinding layer should calculate geometric paths. The validator and movement engine should apply game-specific restrictions such as:

- land/sea legality
- storm and cloud effects
- damaged or crippled ship movement
- launch-type movement reduction
- entry and exit hex timing
- one-hex-at-a-time observation triggers

### 7.2 Weather implementation

The weather capability must own:

- wind direction by sector
- scheduled wind checks
- cloud movement
- storm overlap calculation
- relocation between sectors
- weather modifiers consumed by observation and combat

### 7.3 Knowledge and observation

The knowledge capability should maintain a separate information view for each side. It must support:

- hidden units on the plot map
- Condition 1, 2, and 3 disclosure
- radar-specific high-altitude detection
- contact aging and removal when no longer observable
- exact-name disclosure only when permitted by combat
- no accidental leakage through UI serialization or AI state

## 8. Combat Implementation

The authoritative combat explanation is [COMBAT_RULES.md](COMBAT_RULES.md). BHT means Basic Hit Table: it is the combat-results table column used with the number of attacking factors, not a hit count. The implementation must preserve the following explicitly: BHT is bounded from 1 through 15; the Result Number comes from BHT and attacker count; the die conversion is -2, -1, 0, 0, +1, or +2 for die results 1 through 6; and the combat sequence is air-to-air, anti-aircraft, air attack, then surface combat.

### 8.1 Combat coordinator

Create or refactor a combat coordinator that owns the battle sequence:

1. identify a battle hex
2. validate eligible participants
3. resolve air-to-air combat
4. resolve anti-aircraft combat
5. resolve air attack combat
6. resolve surface attack combat
7. apply losses and damage
8. award points
9. mark bases as attacked where relevant
10. emit a complete combat event stream

### 8.2 Air combat

The air-combat capability must explicitly model:

- interceptor initiation
- special interception during movement
- altitude-separated battles
- interceptor-to-escort combat
- interceptor-to-bomber combat
- RF consumption choice and BHT penalty
- cloud, night, and armament modifiers
- simultaneous loss removal

### 8.3 Surface combat

The surface-combat capability must explicitly model:

- private ship position assignments
- gunnery attack
- ammunition expenditure
- torpedo availability and one-use expenditure
- screening
- breakthrough conditions
- bombardment attacks
- anchored and crippled modifiers
- simultaneous damage application

### 8.4 Combat results

The combat-results capability should provide a pure calculation interface:

- inputs: BHT, attacker count, die result, modifiers
- output: result number and hit count

The result table must be represented as versioned rule data with 15 BHT rows and exactly 14 attack-factor columns. The current attack-factor columns are 1-2, 3-4, 5-6, 7-8, 9-10, 11-12, 13-15, 16-20, 21-24, 25-30, 31-35, 36-40, 41-45, and 46-plus. The ranges are contiguous: 24 belongs to 21-24 and 25 belongs to 25-30.

The source-equivalent range data is `[(1, 2), (3, 4), (5, 6), (7, 8), (9, 10), (11, 12), (13, 15), (16, 20), (21, 24), (25, 30), (31, 35), (36, 40), (41, 45), (46, 999)]`.

The lookup must validate BHT 1 through 15, sum only the attacking factors assigned to the declared attack, select the containing attack-factor range, retrieve the Result Number from the BHT row and range column, then apply the die conversion. Empty cells and unmatched ranges produce no hits. The result table must enforce the minimum BHT of 1 and maximum treatment of 15. Randomness must be injectable so tests can use a known sequence.

The combat capability must also expose surface gunnery, torpedo, breakthrough, and bombardment decisions, plus damage application to aircraft, ships, bases, launch factors, movement factors, AA, gunnery, and carried aircraft. RF and ammunition expenditure must be emitted as explicit combat events. Combat events and state transitions must be persisted in the event history for replay and audit.

## 9. Damage, Repair, and Replacement Implementation

### 9.1 Damage capability

Implement ship damage:

- hit accumulation and sinking
- MF reduction at half damage factor
- odd/even movement for MF-1 ships where required
- crippled status one hit below sinking for applicable ships
- gunnery and AA reduction
- carrier, carrier-light, AV/CAV, and BB LF reduction
- air-factor losses from plane-carrying ships
- immediate loss of aircraft when the ship sinks

Implement base damage:

- LF, AA, AAF, and SF reduction
- negative effective values where required
- no takeoff at LF zero or below
- aircraft loss and dispersed-aircraft two-hit rule
- doubled aircraft damage from applicable attack types
- attacker/defender choice of plane name when permitted

### 9.2 Repair capability

Implement:

- one repair hit per base per repair phase
- scenario overrides
- no repair after air attack or bombardment
- restoration limited to original scenario values
- event logging for restored capabilities

### 9.3 Replacements

Track daily losses by plane name and sea-based versus land-based category. At the defined replacement time, return one aircraft for every three lost, discard fractions, and permanently discard ineligible losses including aircraft lost with sunk carriers.

## 10. Victory and Endgame

### 10.1 Victory capability

Convert scoring into an append-only ledger. Each entry should include:

- timestamp
- receiving side
- points
- reason code
- affected unit or objective
- normal or unnecessary-loss category

Scoring must cover ships, aircraft, transport unloading, base LF-zero turns, and scenario-specific objectives.

### 10.2 Endgame capability

Evaluate:

- automatic victory at the scenario timing point
- end-of-scenario score comparison
- minimum 50-point requirement
- draw result
- final score report

The result should explain exactly which condition ended the game.

## 11. AI Implementation

### 11.1 Legal action generation

The AI must request candidate actions from the same command and validator layer used by the UI. It must never generate an action from hidden enemy state that its side has not observed.

### 11.2 AI phases

Implement AI behavior in phase-specific services:

- weather response and forecast use
- readiness and launch planning
- task-force plotting
- shadowing and search planning
- initiative-aware aircraft movement
- combat target and allocation decisions
- repair and replacement decisions
- endgame and objective pressure

### 11.3 AI utility model

Score candidates using weighted factors such as:

- expected Victory Points
- threat reduction
- probability of safe aircraft recovery
- target value and damage potential
- preservation of irreplaceable aircraft and ships
- weather and observation confidence
- transport and objective timing

The score must include a severe penalty for avoidable aircraft losses caused by missed landing deadlines.

### 11.4 Difficulty

Difficulty should change evaluation depth, uncertainty handling, risk tolerance, and tactical search quality. It must not grant illegal information or modify combat odds.

### 11.5 AI explanation

Every meaningful AI decision should emit a short explanation category and selected factors for the UI log, such as “intercepted observed bombers,” “withdrew before RF deadline,” or “protected damaged carrier.”

## 12. UI Integration

The UI should consume:

- read-only game state projections
- available commands
- validation results
- event stream
- knowledge-filtered views

The desktop UI modules should be updated incrementally:

1. phase and time presentation
2. selected-unit details and effective damage values
3. operations/readiness workflow
4. movement plotting and overlays
5. observation/contact display
6. combat declaration and resolution panels
7. score ledger and repair screen
8. AI action summaries

No UI module should calculate combat hits, damage, LF, RF deadlines, or Victory Points directly.

## 13. Persistence and Replay

Persistence is a logical requirement independent of the storage technology. A web implementation may use a database and API, while another implementation may use local files or an embedded store.

### 13.1 Persistence adapter

Serialize:

- complete authoritative state
- hidden information per side
- pending legal commitments
- random generator state when deterministic continuation is required
- score ledger and event identifiers

Do not serialize only the visible UI projection.

### 13.2 Replay and debugging

Events should be serializable so a test or user can replay a turn. A replay must preserve information boundaries and random outcomes. Debug logs should identify command, actor, target, validation result, state mutation, and emitted events.

## 14. Recommended Delivery Milestones

### Milestone 1: Rules foundation

Deliver:

- authoritative state model
- phase state machine
- command and validator layer
- deterministic event log
- basic scenario loading

Exit condition: a scenario can advance through all phases with no illegal state transitions.

### Milestone 2: Movement and air operations

Deliver:

- task-force movement and plotting
- readiness transitions
- launch types
- RF deadlines
- landing and off-map timing
- weather movement restrictions

Exit condition: a formation can launch, move, and land or be correctly classified as unable to land.

### Milestone 3: Observation and combat

Deliver:

- knowledge state
- condition-level observation
- radar and weather effects
- air combat
- AA and air attack
- surface combat

Exit condition: a complete battle produces an auditable event sequence and legal visibility changes.

### Milestone 4: Damage, repair, scoring

Deliver:

- ship and base damage degradation
- aircraft elimination order
- repair restrictions
- replacement accounting
- score ledger
- endgame evaluation

Exit condition: damage and score examples from the rule source reproduce correctly.

### Milestone 5: Human UI integration

Deliver:

- board interactions
- operations screen
- movement and combat workflows
- validation feedback
- score and repair views
- save/load controls

Exit condition: a human can complete a scenario without direct model manipulation.

### Milestone 6: Serious AI

Deliver:

- phase-specific action generation
- strategic scoring
- uncertainty handling
- safe landing planning
- difficulty levels
- AI explanations

Exit condition: the computer can complete a full scenario without illegal actions and demonstrates objective-aware behavior.

## 15. Test Matrix

### 15.1 Rules unit tests

Combat tests must cover BHT meaning and bounds, every Combat Results Table row, every attack-factor range, the 24 and 25 boundary assignments, Result Number lookup, die conversion, air-to-air, anti-aircraft, air attack, surface combat, damage application, RF expenditure, and persistence of combat events.

Test at minimum:

- every phase transition and invalid transition
- minimum, normal, and maximum launch movement
- LF and MC limits
- Readying Factor and one-move-per-air-factor rule
- RF deadline calculation and RF combat expenditure
- night landing loss
- storm movement and combat restrictions
- observation condition levels and radar
- ship damage thresholds and capability reduction
- base negative LF and repair behavior
- aircraft elimination order and dispersed losses
- replacement calculation
- combat result table boundaries and modifiers
- Victory Point events and endgame thresholds

### 15.2 Integration tests

Test complete flows:

- scenario setup to first turn
- launch, movement, observation, combat, landing, and repair
- carrier damage followed by reduced operations
- base attack followed by blocked repair
- transport unloading across multiple turns
- sunk carrier with aircraft loss and replacement exclusion
- hidden contact becoming observed and then disappearing
- human command and AI command producing the same rule validation results

### 15.3 UI tests

Test:

- current phase and side presentation
- legal-action highlighting
- hidden-information filtering
- launch review warnings
- combat-step presentation
- damage and score updates
- save/load restoration

### 15.4 AI tests

Test:

- no illegal command generation
- no use of hidden enemy state
- aircraft are routed toward valid landing locations
- damaged units show reduced utility and capability
- AI responds to high-value observed targets
- AI does not receive altered combat probabilities at higher difficulty

## 16. Definition of Done

A feature is complete when:

1. its rule behavior is represented in the authoritative engine
2. invalid actions produce stable validation errors
3. state changes emit structured events
4. the human UI can display the resulting state
5. the AI can use the same capability where applicable
6. focused tests cover normal, boundary, and invalid cases
7. save/load preserves the new state
8. the behavior is traceable to a requirement or rule section

## 17. First Implementation Slice

The first coding slice should be deliberately small:

1. introduce the phase state machine around the existing game engine
2. define command and validation result types
3. add focused tests for phase order and active-side restrictions
4. expose the phase status to the desktop UI

Once this slice is passing, add air operations and damage as separate slices. This keeps the rule engine testable before the UI and AI become dependent on incomplete behavior.
