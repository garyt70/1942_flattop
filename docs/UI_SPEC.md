# 1942 Flattop UI Specification

## 1. Purpose

This document specifies the human-facing interface for the digital 1942 Flat Top game. It defines screens, controls, information visibility, phase workflows, validation feedback, combat presentation, and AI interaction. It is platform-neutral and can be implemented in a desktop or web UI.

The UI must reduce bookkeeping without removing meaningful decisions. It must never reveal information that the active player has not legally observed.

## 2. UI Principles

1. The active phase and required decisions are always visible.
2. Legal actions are discoverable from the selected unit.
3. Illegal actions are disabled where practical and explained when attempted.
4. Important commitments require confirmation before execution.
5. Hidden information is represented as uncertainty, not as empty map space.
6. Rule consequences are shown before a player commits when they can be calculated.
7. Combat results are presented as an auditable sequence, not as an unexplained outcome.
8. The interface must remain usable when many formations, task forces, contacts, and weather markers occupy one area.

## 3. Persistent Game Layout

The main game screen uses five persistent regions:

### 3.1 Map region

The map is the primary workspace. It displays:

- hex grid and coordinates
- land, sea, and partial-land terrain
- friendly units
- legally observed enemy units
- uncertain enemy contacts
- bases and coastwatcher coverage
- clouds, storms, and wind direction
- movement, observation, and attack overlays

The map must support zooming and panning without changing game state. A selected hex must have a stable visual treatment distinct from a selected unit.

### 3.2 Phase and time bar

The top-level status area displays:

- scenario name
- current time and turn number
- day or night status
- current phase
- side currently acting
- initiative holder
- whether the phase is simultaneous, awaiting the human, or processing the AI
- pending decisions or confirmations

### 3.3 Selection and action panel

The side panel displays the selected unit, selected hex, or pending action. It contains only actions legal for the current phase and selected state.

### 3.4 Event and combat log

The log records:

- phase transitions
- weather changes
- observations
- movement discoveries
- launches and landings
- combat declarations and results
- damage and losses
- Victory Point events
- AI action summaries
- validation errors

The player can filter the log by phase, unit, combat, observation, and scoring.

### 3.5 Force and score summary

A compact summary shows:

- each side's Victory Points
- automatic-victory threshold and score difference
- known enemy strength summary, without hidden detail
- aircraft awaiting launch, in flight, due to land, and lost
- damaged ships and bases requiring attention

## 4. Main Menu and New Game

### 4.1 Main menu controls

The main menu must provide:

- New Game
- Load Game
- Continue Recent Game
- Rules and Help
- Settings

### 4.2 New Game screen

The player selects:

- scenario
- game mode: human vs human or human vs computer
- human side
- AI difficulty, when applicable
- optional deterministic random seed for testing or replay

The scenario preview must show:

- scenario title and historical context
- expected playing time
- starting time and end time
- map area
- sides and forces
- automatic victory threshold
- special rules

The Start button remains unavailable until all required choices are valid.

## 5. Game Board Screen

### 5.1 Initial board state

On entry, the UI must show the starting board and identify the first required phase. Hidden enemy units must not be rendered as visible units. The player may open friendly operations charts and setup information without exposing the opponent's private state.

### 5.2 Map interactions

Clicking or tapping a friendly unit selects it. Selecting an enemy unit shows only information legally available to the player. Selecting a hex shows terrain, weather, known occupants, observation coverage, and legal contextual actions.

The map must support:

- select
- inspect
- move
- plot
- observe
- shadow
- launch or recover aircraft where applicable
- initiate an eligible battle
- clear selection
- undo an uncommitted phase action where the phase permits planning

### 5.4 Piece selection and context menu (REQ-15.03a)

Clicking a map piece opens a context menu whose contents depend on the selected piece and current phase. The menu must not reveal hidden opponent details or offer actions that are not legal.

- Base: Details
- Task force: Details, Move during Task Force Movement, Combat when an enemy task force is co-located during Combat
- Air formation: Details, Move during Plane Movement, Land in a friendly base or plane-carrying task-force hex during the legal phase, Combat when an eligible enemy is co-located

Right-click may open the details or observation view directly. If several pieces share a hex, show a selection menu first. Clicking empty map space starts panning rather than opening a blank unit panel. The web mockup should demonstrate this as a local, non-engine-backed interaction.

### 5.3 Overlays

The player can toggle overlays for:

- movement range
- aircraft endurance and landing deadline
- observation range
- radar coverage
- coastwatcher coverage
- cloud and storm effects
- known enemy contacts
- attack eligibility
- damaged and crippled units

Overlays must not reveal information that the player could not legally know.

## 6. Operations and Readiness Screen

The operations view is opened for a base, carrier, or other plane-carrying unit. It must show separate, clearly labeled areas for:

- Ready
- Readying
- Just Landed
- Air Formation / In Flight
- Dispersed aircraft

For each area, show aircraft type and count where the player is entitled to know it. The screen must show:

- maximum capacity
- current occupancy
- current LF and remaining launch/landing capacity
- Readying Factor and remaining readiness moves
- damage-modified values
- aircraft that must launch this turn
- aircraft that must land by a particular turn

The interface must prevent moving an aircraft more than once in the same turn or exceeding the Readying Factor.

The screen must show `LF total / used / remaining` for the selected carrier or base and `RF total / queued / remaining` for the current turn. Plus and minus buttons adjust batch counts between readiness lanes and the pending formation. Controls must update these counters immediately and must be disabled when the move exceeds the available budget. Armament is editable only for aircraft in Readying; Ready aircraft use a locked armament display and may be added to a formation.

### 6.1 Launch workflow

1. Select aircraft from a valid Ready area.
2. Select destination or mission.
3. Select minimum, normal, or maximum launch.
4. Select altitude where legal.
5. Review LF use, movement allowance, RF landing deadline, and payload.
6. Confirm launch.

The review step must warn if the selected formation cannot reach a valid landing location before its deadline.

### 6.3 Formation construction workflow

The operations chart must provide a direct construction workflow for formations, not only a read-only status display:

1. In Ready, select an aircraft row.
2. Adjust the number of factors to add to the pending formation.
3. Cycle or choose the armament: `GP`, `AP`, `Torpedo`, or unarmed where legal. This control is enabled only while the aircraft is in Readying.
4. Choose an available Air Formation number from 1 through 35.
5. Add additional aircraft types if desired.
6. Use plus/minus controls to adjust the selected factor count. Removing a pending factor returns it to Ready.
7. Review total factors, LF consumption, launch type, payload, and resulting mission roles.
8. Commit Create Air Formation.

The UI must keep pending selections separate from committed game state. Cancel must restore the uncommitted selection without changing Ready counts.

### 6.4 Readiness action workflow

The aircraft combat-values table must expose the plus/minus controls. Ready `+` assigns factors to the pending formation and Ready `-` returns pending factors to the available Ready pool. Just Landed `+` queues Just Landed -> Readying; Readying `+` queues Readying -> Ready; Readying `-` queues Readying -> Just Landed; and Ready exposes a reverse Ready -> Readying transition. The player can queue transitions, see remaining Readying Factor, and commit the readiness batch. Controls must be unavailable when the selected transition would exceed the remaining factor.

### 6.2 Recovery workflow

When an air formation is in a valid landing hex, the UI must show eligible recovery locations and each location's remaining LF and capacity. It must show night-landing risk before confirmation.

## 7. Task-Force Movement Screen

### 7.1 Plotting

During plotting, the player selects a task force and chooses a legal route. The UI displays:

- current MF
- damage or weather reductions
- plotted destination
- path through each hex
- shadowing implications where known
- whether the route exits the map

The route must be validated before it can be committed.

### 7.2 Movement execution

During execution, the player can step through or confirm the plotted route. The UI must pause for required observation declarations and show new observations immediately without revealing unrelated hidden state.

### 7.3 Task-force reorganization

When multiple friendly task forces occupy a valid hex, the UI provides Combine and Split actions. It must display the resulting ship composition and warn about carrier, air-capacity, and scenario restrictions before committing.

## 8. Observation and Contact UI

### 8.1 Search declaration

Before moving an air formation, the UI asks whether it will attempt observation. The player must choose Search or Do Not Search. If Search is selected, the UI applies the correct weather, radar, and storm restrictions and displays the result.

### 8.2 Contact representation

Contacts have three states:

- Condition 1: presence and broad unit category
- Condition 2: approximate formation or task-force counts and classes
- Condition 3: exact formation count and class composition allowed by the rules

The UI must label the information quality and distinguish reported estimates from exact data.

### 8.3 Information history

The player can inspect how a contact was discovered and when its information was last refreshed. The history must not expose the opponent's actual hidden state.

## 9. Combat UI

### 9.1 Battle declaration

When a legal battle is available, the UI presents the battle hex, eligible participants, and available combat types. Combat begins only after the initiating player confirms.

### 9.2 Air combat setup

The player selects:

- altitude sequence
- interceptors
- escorts
- bombers
- target assignments
- whether applicable aircraft expend RF

The UI previews BHT modifiers from clouds, night, armament, and RF decisions.

### 9.3 Anti-aircraft and air attack setup

Before AA combat, the player assigns bombers to targets and selects bombing type where legal. The UI locks allocations before AA resolution, because surviving bombers cannot change their declared target afterward.

The review panel shows:

- bombers committed
- attack type
- target
- expected RF expenditure
- target damage and aircraft-on-target consequences
- applicable modifiers

### 9.4 Surface combat setup

Each side privately assigns ships to:

- Gunnery Attack
- Torpedo Attack
- Screen

The UI must keep these assignments private until reveal. It must enforce that crippled and anchored ships are screened. After both sides commit, the interface reveals positions and resolves gunnery, torpedo, and breakthrough combat in order.

### 9.5 Combat resolution presentation

Combat resolves as a step-by-step panel:

1. participating units
2. declared attacks
3. BHT and modifiers
4. dice result
5. hits
6. damage and eliminations
7. Victory Points awarded
8. surviving units and new statuses

The player can expand rule explanations but cannot alter a completed step.

## 10. Damage, Repair, and Scoring UI

### 10.1 Damage display

Every damaged ship and base shows:

- current hits
- damage factor or original capacity
- effective MF
- effective LF
- effective AA and gunnery values
- crippled or sunk status
- irreversible versus repairable effects

### 10.2 Aircraft-loss selection

When the rules permit a choice of aircraft to eliminate, the UI shows only eligible plane names and readiness boxes. It must not disclose hidden counts beyond what the combat rules require.

### 10.3 Repair screen

During repair, each base shows:

- whether it was attacked this turn
- whether it is eligible to repair
- current damage
- current and restored LF, AA, and SF
- original scenario maximums

The player confirms repair decisions if the scenario allows a choice; otherwise the system performs the deterministic repair automatically and logs it.

### 10.4 Victory Point ledger

The score panel must provide an event ledger showing:

- event and time
- side receiving points
- points awarded
- reason and affected unit
- whether the event used normal or unnecessary-loss scoring
- transport unloading progress and remaining sunk value

## 11. AI Turn Presentation

While the AI acts, the UI must show the current phase and a concise action feed. It may display intent categories such as Search, Intercept, Strike, Withdraw, Defend, Repair, or Reorganize, but must not reveal private AI information.

The player can pause between AI actions if the selected game mode permits. At the end of the AI phase, the UI presents a summary of meaningful actions, discoveries, combat, losses, and score changes.

## 12. Help and Rule Explanation

Contextual help must explain:

- why an action is legal or illegal
- how launch type affects movement
- when an aircraft must land
- how damage changes capabilities
- why a base can or cannot repair
- how a Victory Point event was calculated

Help must describe the current state and rule consequence, not expose hidden opponent data.

## 13. RF Endurance, Persistence, Save, Load, and Recovery

The launch and movement UI must explicitly label RF endurance as the aircraft's remaining flight allowance. For every formation, the player must be able to see the applicable must-land-by turn, RF consumed by combat, and whether the current route can still reach a valid landing location.

Save controls must be available at safe phase boundaries and must preserve:

- turn, time, phase, and initiative
- all visible and hidden state
- pending plots and commitments where legal
- damage, readiness, RF deadlines, and score ledger
- AI planning state necessary for deterministic continuation

Loading a game must restore the same legal action set and information boundary.

## 14. Usability Acceptance Criteria

The UI is acceptable when a new player can:

1. start a scenario without manual setup
2. identify the current phase and required action
3. inspect a friendly unit and understand its effective capabilities
4. launch aircraft while seeing LF, movement, and landing consequences
5. plot and validate a task-force route
6. distinguish known, estimated, and hidden enemy information
7. resolve an air or surface battle from declaration through scoring
8. understand why damage changed a unit's capabilities
9. understand why a base did or did not repair
10. identify the current score, automatic-victory threshold, and remaining objectives

## 15. UI Validation Tests

The UI implementation must include focused tests or executable checks for:

- phase, turn, initiative, and active-side presentation
- legal-action filtering and validation messages
- launch review showing LF, movement allowance, RF endurance, and landing deadline
- hidden-information filtering for Condition 1, 2, and 3 contacts
- combat-step display without revealing private setup prematurely
- damage, repair eligibility, and Victory Point updates
- save/load restoration of the visible state and information boundary

## 16. Delivery Milestones

The UI should be delivered in these increments:

1. persistent phase bar, map selection, and unit details
2. operations/readiness and launch/recovery workflows
3. movement plotting, observation contacts, and overlays
4. combat resolution, damage, repair, and scoring views
5. save/load, AI action summaries, and usability testing
