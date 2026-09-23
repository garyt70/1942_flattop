# 1942 Flat Top PostgreSQL Runtime Design

## 1. Purpose

This document defines PostgreSQL's role in the web application. PostgreSQL is the required development and runtime database, configured externally by connection string. Scenario YAML remains the source of truth for scenario definitions; PostgreSQL stores runtime game data and immutable references to the definitions used.

This document is a design proposal. It does not create a database, migrations, or application code.

## 2. Database Responsibilities

PostgreSQL stores:

- users and game participants
- game sessions and lifecycle status
- scenario and ruleset references
- authoritative game snapshots
- committed commands
- emitted domain events
- replay and save metadata
- AI job state when asynchronous AI is introduced

PostgreSQL does not become the editable source of ordinary scenario definitions in the first version.

## 3. Connection and Development Model

The server receives a PostgreSQL URL from configuration:

```text
DATABASE_URL=postgresql://user:password@host:5432/flattop
```

Development requirements:

- PostgreSQL is provisioned externally.
- Startup must fail clearly when the database is unavailable.
- Database migrations run explicitly before the server is considered ready.
- Tests use an isolated database or schema.
- Credentials must never be committed to the repository.
- Production and development databases use separate credentials and databases.

## 4. Logical Tables

### `games`

Stores one row per game:

- `id`
- `scenario_id`
- `scenario_version`
- `ruleset_id`
- `ruleset_version`
- `status`
- `current_turn`
- `current_phase`
- `state_version`
- `created_at`
- `updated_at`

Scenario and ruleset references are immutable after game creation.

### `game_players`

Stores participant membership:

- `game_id`
- `player_id`
- `side`
- `role`
- `joined_at`

A player may see only the projection allowed for their side.

### `game_snapshots`

Stores authoritative serialized state checkpoints:

- `game_id`
- `state_version`
- `state_jsonb`
- `random_state_jsonb`
- `created_at`

Snapshots reduce replay cost. `jsonb` is appropriate for evolving domain state, while frequently queried metadata remains in normal columns.

### `game_commands`

Stores submitted intents:

- `id`
- `game_id`
- `expected_version`
- `actor_id`
- `command_type`
- `payload_jsonb`
- `accepted`
- `validation_error_code`
- `created_at`

Rejected commands may be retained for debugging and audit, subject to privacy policy.

### `game_events`

Stores committed domain events:

- `id`
- `game_id`
- `state_version`
- `event_type`
- `payload_jsonb`
- `visibility`
- `created_at`

Events must be ordered by `(game_id, state_version, id)`. Visibility may identify public, Allied-only, Japanese-only, or private event projections.

### `save_points`

Stores named player-visible saves:

- `id`
- `game_id`
- `state_version`
- `name`
- `created_by`
- `created_at`

A save point references an immutable snapshot/version rather than duplicating state unnecessarily.

## 5. Transaction Boundary

A validated command and its consequences must commit atomically:

1. lock or compare the current game version
2. load the authoritative snapshot
3. validate the command
4. apply the transition
5. append the command result
6. append domain events
7. write a new snapshot when checkpoint policy requires it
8. update the game version and phase metadata
9. commit the PostgreSQL transaction

If any step fails, no partial state or event must be visible.

Optimistic concurrency should reject commands whose `expected_version` does not match the current `state_version`.

## 6. Event and Snapshot Strategy

Use an event log for auditability and snapshots for efficient loading:

- write every accepted command's events
- snapshot at game creation
- snapshot periodically, such as every turn or configurable event count
- rebuild a game by loading the latest snapshot and replaying later events
- preserve random-generator state for deterministic replay

The event log is the authoritative history of committed transitions. Snapshots are rebuildable accelerators.

## 7. Scenario References

When a game is created, store:

- scenario ID
- scenario semantic version
- content hash of the YAML definition
- ruleset ID and version
- ruleset code release identifier

This prevents a future YAML edit or code update from silently changing an existing game.

## 8. Migrations

Use versioned forward migrations for:

- initial schema
- indexes and constraints
- new event or snapshot fields
- new authentication or multiplayer fields

Migration execution must be separate from application startup or explicitly controlled by deployment. Every migration requires a rollback or recovery plan, even if production rollback uses a forward corrective migration.

## 9. Required Constraints and Indexes

At minimum:

- unique game state version per game
- unique player side per game
- foreign keys from commands, events, snapshots, and saves to games
- index events by `(game_id, state_version)`
- index commands by `(game_id, created_at)`
- index active games by status and updated time
- check supported status and phase values where practical

## 10. Read Models and Projections

The browser should not receive raw snapshots or unrestricted event payloads. The API builds a side-filtered read model containing:

- visible map units and contacts
- current phase and legal actions
- selected unit details
- air operations state
- combat review data
- public event log
- score projection

Projection generation must enforce hidden-information rules in the server layer.

## 11. AI and PostgreSQL

The initial AI can execute in-process within the command transaction workflow. If AI becomes asynchronous:

- create an AI job record
- enqueue a job after the committed human action
- generate commands from the AI's side-filtered projection
- submit commands through the normal command boundary
- publish resulting events over the WebSocket

The AI must not write game snapshots directly.

## 12. Backup and Recovery

The deployed system must define:

- PostgreSQL backup schedule
- point-in-time recovery policy
- restore testing procedure
- event-log retention
- handling of interrupted commands
- recovery of WebSocket clients after server restart

A recovered game must preserve state version, event ordering, scenario hash, ruleset reference, and deterministic random state.

## 13. Testing

Database tests must cover:

- migration from an empty database
- game creation with a scenario/version reference
- atomic accepted command and event writes
- rejected command persistence policy
- optimistic concurrency conflicts
- snapshot and event replay
- hidden-information projection queries
- save/load continuation
- recovery after transaction failure

## 14. Design Decision

Use PostgreSQL as the required external development and runtime database. Keep YAML scenario files in the repository as immutable versioned inputs, and store only scenario references, hashes, runtime game state, commands, events, and save metadata in PostgreSQL.
