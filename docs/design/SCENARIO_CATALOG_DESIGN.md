# 1942 Flat Top Scenario Catalog and Special Rules Design

## 1. Purpose

This document defines how new scenarios are represented, validated, published, selected when starting a game, and extended when a scenario requires special rules. It is a design proposal for review only.

The goal is to make ordinary scenario additions data-only while providing an explicit, reviewed code extension path for scenarios that require behavior not expressible as data.

## 2. Scenario Lifecycle

A scenario moves through these stages:

1. Author adds or updates a YAML file in the repository.
2. Schema validation checks structure, types, identifiers, coordinates, unit references, and ruleset references.
3. Domain validation checks that the setup creates a legal initial game state.
4. Automated tests load the scenario and verify expected counts and locations.
5. A developer reviews the scenario and its tests.
6. The scenario is assigned a version and publication status.
7. The application release bundles the scenario catalog.
8. The server exposes only published, valid scenarios to `Start New Game`.

A scenario referenced by an existing game is immutable. Corrections create a new scenario version.

## 3. Scenario YAML Structure

Each scenario is one versioned YAML document:

```yaml
schema_version: 1
scenario:
  id: coral-sea-approach
  version: 1.0.0
  name: Coral Sea Approach
  description: Allied and Japanese carrier forces contest the Coral Sea.
  status: published
  ruleset: flat-top-standard-v1
  board:
    width: 44
    height: 50
    coordinate_system: axial-flat-top
    land_hexes:
      - [0, 9]
      - [1, 9]
  sides:
    - id: allied
      display_name: Allied
    - id: japanese
      display_name: Japanese
  objectives:
    - id: protect-carriers
      type: victory_points
  setup:
    bases: []
    task_forces: []
    air_formations: []
  expected_setup:
    unit_counts:
      bases: 5
      task_forces: 1
```

The actual schema should use the complete unit and combat contracts from [UNIT_DATA_SPEC.md](UNIT_DATA_SPEC.md). Scenario files should reference catalog IDs rather than duplicate aircraft or ship statistics.

## 4. Board Definition

A scenario board contains:

- dimensions
- coordinate system and projection identifier
- land hex coordinates
- named map locations
- bases and their coordinates
- optional map labels or regions
- weather setup when scenario-specific

The board definition must not contain executable behavior. Coordinates must be validated against board dimensions and land/sea restrictions.

## 5. Unit Setup

Setup records reference catalog entities:

```yaml
setup:
  bases:
    - id: port-moresby
      catalog_id: port-moresby
      side: allied
      position: [3, 23]
      aircraft:
        - aircraft_id: p40
          count: 12
          state: ready
  task_forces:
    - id: allied-tf-1
      side: allied
      position: [20, 10]
      ships:
        - ship_id: lexington
          state: operational
        - ship_id: pensacola
          state: operational
```

Scenario setup may override scenario-state fields such as initial damage, readiness state, armament, or observation status when the catalog permits that override. It must not silently override immutable unit statistics.

## 6. Scenario Ruleset Reference

Every scenario references a ruleset identifier:

```yaml
ruleset: flat-top-standard-v1
```

The ruleset determines the code-backed behavior used by the game. A ruleset is versioned and immutable once used by a published scenario.

Examples:

- `flat-top-standard-v1`
- `coral-sea-special-v1`
- `training-scenario-v1`

The scenario catalog loader must reject unknown ruleset identifiers.

## 7. Ordinary Data-Only Scenarios

A scenario is data-only when its differences can be represented by:

- board dimensions and land hexes
- starting unit placement
- starting aircraft allocation
- initial damage and readiness state
- weather setup
- objectives and victory values already supported by the rules engine
- side-specific visibility or setup metadata already supported by the engine

Adding a data-only scenario must not require editing the rules engine.

## 8. Special Rules Requiring Code

Some scenarios may require new behavior. These are explicit code changes, not hidden YAML scripts.

A special-rule implementation must provide:

- a stable ruleset or rule-plugin identifier
- the code module implementing the behavior
- a typed configuration contract
- validation rules
- domain tests
- scenario tests
- documentation of player-visible effects
- migration or compatibility notes if persistence changes

Example YAML reference:

```yaml
ruleset: coral-sea-special-v2
special_rules:
  search_modifier: carrier_scouting
  landing_restriction: night_recovery_adjustment
```

The YAML may select and configure approved rule identifiers, but it must not contain arbitrary Python, JavaScript, SQL, or executable expressions.

## 9. Special-Rule Extension Interface

The rules engine should expose a narrow extension interface rather than allowing scenario code to mutate state freely:

```text
Ruleset
  validate_scenario(scenario_definition)
  legal_commands(state, knowledge)
  validate_command(state, command)
  before_command(state, command)
  resolve_command(state, command)
  after_command(state, command, events)
  victory_status(state)
```

Most scenarios should use the standard ruleset. A custom ruleset should override only the explicitly required hooks and reuse standard behavior for all other rules.

## 10. Scenario Validation

Validation occurs at two levels.

### 10.1 Schema validation

Check:

- required fields
- YAML types
- identifier format
- version format
- known catalog IDs
- known ruleset IDs
- valid side IDs
- board dimensions
- coordinate bounds
- duplicate IDs

### 10.2 Domain validation

Check:

- no unit starts in an illegal terrain hex
- aircraft counts do not exceed carrier/base capacity
- aircraft readiness states are legal
- formation numbers are unique and in range
- ship composition is legal
- initial damage is within limits
- armament is legal for the aircraft
- scenario objectives are supported
- starting phase and time are valid
- hidden-information setup is consistent

Validation must fail the build or release when a published scenario is invalid.

## 11. Scenario Catalog API

The server exposes read-only scenario metadata for the new-game screen:

```http
GET /api/scenarios
GET /api/scenarios/{scenario_id}
```

The response contains:

- ID and version
- display name and description
- map dimensions
- available sides
- estimated complexity or duration
- ruleset label
- publication status
- setup summary

The API must not expose hidden scenario setup information that players should not see before starting.

## 12. New Game Creation

```http
POST /api/games
```

Request:

```json
{
  "scenario_id": "coral-sea-approach",
  "scenario_version": "1.0.0",
  "player_side": "allied",
  "opponent": "computer"
}
```

The server:

1. loads the exact YAML version
2. validates it
3. resolves the referenced ruleset
4. creates the initial authoritative state
5. stores the scenario and ruleset references
6. writes the initial event
7. returns a side-filtered game projection

## 13. Testing and Review Requirements

Every scenario file must have:

- schema validation coverage
- a load test
- expected setup assertions
- at least one legal-action smoke test
- a ruleset test if special rules are used

A pull request adding a scenario should contain:

- the YAML file
- scenario tests
- player-facing description
- any required map asset
- special-rule documentation if applicable

## 14. Recommended Initial Scenario Layout

```text
scenarios/
  catalog.yaml
  schema.yaml
  coral-sea-approach/
    scenario.yaml
    expected_setup.yaml
    README.md
  training-scenario/
    scenario.yaml
    expected_setup.yaml
    README.md
```

`catalog.yaml` may provide ordering and presentation metadata, while each scenario owns its complete definition and tests.

## 15. Design Decision

Use YAML for versioned scenario definitions and explicit code-backed rulesets for special behavior. Keep scenario files in the repository as the source of truth, validate them during CI and application startup, and store immutable scenario/version references in PostgreSQL when games are created.
