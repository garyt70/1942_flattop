# Victory Points Combat Tracking

This document explains where and how victory points are awarded during combat resolution.

## Combat Flow and VP Tracking

### 1. Air-to-Air Combat (`resolve_air_to_air_combat`)

**Where hits are recorded**: `remove_hits()` function at lines 579-605
- Populates `result["eliminated"]["interceptors"]` - attacker's losses
- Populates `result["eliminated"]["escorts"]` - defender's losses  
- Populates `result["eliminated"]["bombers"]` - defender's losses

**VP tracking location**: `award_victory_points_from_combat()` in desktop_ui.py
- Interceptor losses → defender gets 2 VP per aircraft
- Escort losses → attacker gets 2 VP per aircraft
- Bomber losses → attacker gets 2 VP per aircraft

**Example result structure**:
```python
{
    "eliminated": {
        "interceptors": [("Zero", 2), ("Zero", 1)],  # 3 attacker aircraft lost
        "escorts": [("Wildcat", 4)],                  # 4 defender aircraft lost
        "bombers": [("Dauntless", 2)]                 # 2 defender bombers lost
    }
}
```

### 2. Anti-Aircraft Combat - Taskforce (`resolve_taskforce_anti_aircraft_combat`)

**Where hits are recorded**: Lines 650-661
- Removes bomber count and adds to `result["eliminated"]["bombers"]`
- These are the attacker's bombers being shot down

**VP tracking location**: `award_victory_points_from_combat()` in desktop_ui.py
- Bomber losses → defender gets 2 VP per aircraft

**Example result structure**:
```python
{
    "eliminated": {
        "bombers": [("Avenger", 3), ("Dauntless", 2)]  # 5 attacking bombers lost
    }
}
```

### 3. Anti-Aircraft Combat - Base (`resolve_base_anti_aircraft_combat`)

**Where hits are recorded**: Lines 707-716
- Removes bomber count and adds to `result["eliminated"]["bombers"]`
- These are the attacker's bombers being shot down

**VP tracking location**: `award_victory_points_from_combat()` in desktop_ui.py
- Bomber losses → defender gets 2 VP per aircraft

**Example result structure**:
```python
{
    "eliminated": {
        "bombers": [("B-17", 2)]  # 2 attacking bombers lost
    }
}
```

### 4. Air-to-Ship Combat (`resolve_air_to_ship_combat`)

**Where hits are recorded**: 
- **Aircraft on sunk carriers**: Lines 870-881 - when carrier is sunk, all aircraft on it are added to `result["eliminated"]["aircraft"]`
- **Aircraft on damaged carriers**: Line 883 calls `_resolve_base_aircraft_hits()` which adds to `result["eliminated"]["aircraft"]`
- **Ship sinking**: Line 862 sets `ship.status = "Sunk"`

**VP tracking location**: `award_victory_points_from_combat()` in desktop_ui.py
- Aircraft losses → attacker gets 2 VP per aircraft (defender's carrier aircraft)
- Ship sunk → attacker gets VP based on ship type and damage_factor
  - CV (Carrier): 24 × 4 = 96 VP
  - BB (Battleship): 20 × 10 = 200 VP
  - CA (Heavy Cruiser): 12 × 3 = 36 VP
  - CL (Light Cruiser): 8 × 3 = 24 VP
  - DD (Destroyer): 6 × 1-2 = 6-12 VP

**Note**: `perform_air_to_ship_combat()` in desktop_ui.py adds `ship` object and `ship_was_sunk` flag to results for VP tracking

**Example result structure**:
```python
{
    "eliminated": {
        "aircraft": [("Zero", 4), ("Val", 3)]  # 7 defender aircraft lost on carrier
    },
    "ship": <Ship object>,
    "ship_was_sunk": True
}
```

### 5. Air-to-Base Combat (`resolve_air_to_base_combat`)

**Where hits are recorded**: Lines 951-963
- Base damage is applied: `base.damage += hits`
- Calls `_resolve_base_aircraft_hits()` at line 963 which adds to `result["eliminated"]["aircraft"]`

**VP tracking location**: `award_victory_points_from_combat()` in desktop_ui.py
- Aircraft losses → attacker gets 2 VP per aircraft (defender's base aircraft)

**Base damage VP tracking**: ✅ IMPLEMENTED
- Per game rules, damaged bases with LF≤0 award 5 VP per turn
- Implemented in `TurnManager._award_base_damage_victory_points()` called from `next_turn(board)`
- Awards VP at end of each turn for bases with `available_launch_factor_min ≤ 0` and `damage > 0`
- See [tests/test_base_damage_vp.py](tests/test_base_damage_vp.py) for comprehensive tests

**Example result structure**:
```python
{
    "eliminated": {
        "aircraft": [("Zero", 2), ("Betty", 3)]  # 5 defender aircraft lost at base
    }
}
```

### 6. Surface Combat (`resolve_surface_combat`)

**Where hits are recorded**: In surface_combat_engine.py (not shown)
- Ships are sunk and removed from taskforces
- Aircraft on sunk carriers are eliminated

**VP tracking location**: `award_victory_points_from_combat()` in desktop_ui.py
- Currently has TODO placeholders for ship tracking
- Aircraft on sunk carriers are tracked via `eliminated["attacker"]` and `eliminated["defender"]` keys

**Note**: Surface combat VP tracking needs improvement to properly track sunk ships

## VP Award Function Flow

```
Combat occurs → desktop_ui.py:perform_air_combat_ui()
    ↓
Combat results assembled in combat_results dict
    ↓
desktop_ui.py:award_victory_points_from_combat() called
    ↓
For each combat type:
  - Extract eliminated aircraft lists
  - Extract sunk ship information
  - Call aircombat_engine.py:award_aircraft_elimination_vp()
  - Call aircombat_engine.py:award_ship_sunk_vp()
    ↓
Helper functions call victory_points.py:VictoryPointsTracker methods:
  - award_aircraft_eliminated()
  - award_ship_sunk()
    ↓
Points added to tracker.allied_points or tracker.japanese_points
    ↓
Points displayed in UI (Combat Results popup, Dashboard)
```

## Computer Opponent

The computer opponent in `computer_oponent_engine.py` uses the same `award_victory_points_from_combat()` function after combat resolution, ensuring consistent VP tracking for both human and AI players.

## Key Points

1. **Eliminated aircraft are tracked at the point of loss**: When aircraft counts are reduced in combat resolution functions
2. **VP awards happen after combat completes**: The `award_victory_points_from_combat()` function processes all combat results
3. **Side attribution is correct**: 
   - The `owning_side` parameter in award functions indicates which side LOST the units
   - The helper functions internally award points to the opponent
4. **Ship sinking requires ship object**: Air-to-ship and surface combat must include ship objects in results for proper VP calculation
5. **Base damage VPs are end-of-turn**: Damaged bases award 5 VP per turn while LF≤0, checked at turn end ✅ IMPLEMENTED

## Testing

All VP tracking is tested in `tests/test_victory_points.py`:
- Aircraft elimination (normal and unnecessary)
- Ship sinking (all ship types)
- Ship damage
- Base damage
- Base damage per-turn VP awards (7 additional tests in test_base_damage_vp.py)
- Automatic victory conditions
- Winner determination
- Serialization/deserialization

All tests pass ✓ (17 total tests)

## Base Damage Victory Points (End-of-Turn)

Base damage victory points are awarded differently from combat VP. They are checked and awarded at the **end of each turn**, not during combat.

### Implementation

**Location**: [hex_board_game_model.py](flattop/hex_board_game_model.py)

**Key Methods**:
- `TurnManager.next_turn(board)` - Main turn advancement method
- `TurnManager._award_base_damage_victory_points(board)` - VP checking and award

### How It Works

```python
def next_turn(self, board=None):
    # Award VP for damaged bases BEFORE incrementing turn
    if board and hasattr(self, 'victory_points'):
        self._award_base_damage_victory_points(board)
    
    # Then increment turn counter
    self.current_hour += 1
    self.turn_number += 1
    # ... rest of turn advancement

def _award_base_damage_victory_points(self, board):
    # Get all base pieces
    base_pieces = [p for p in board.pieces if isinstance(p.game_model, Base)]
    
    for piece in base_pieces:
        base = piece.game_model
        base_side = piece.side
        
        # Check if base is damaged with LF ≤ 0
        if base.available_launch_factor_min <= 0 and base.damage > 0:
            # Award 5 VP to the opposing side
            opposing_side = "Japanese" if base_side == "Allied" else "Allied"
            self.victory_points.award_base_damaged(
                opposing_side, base.name, self.turn_number
            )
```

### Game Rules Reference

From game_requirements.txt Section 25.6:
> "A player receives 5 VPs each turn (beginning on the turn after the base was damaged) for each enemy base with a Landing Factor of zero or less."

### Landing Factor Calculation

A base's landing factor is calculated as:
```python
available_launch_factor_min = launch_factor_min - damage
```

So a base with:
- `launch_factor_min = 5`
- `damage = 6`

Has `available_launch_factor_min = -1` (≤ 0), so it awards 5 VP per turn.

### When VP Are Awarded

1. **During Combat**: Base is attacked, `base.damage` is increased
2. **End of Turn**: `next_turn(board)` is called (or `next_phase(board)` wraps around)
3. **VP Check**: All bases are checked for LF ≤ 0
4. **VP Award**: Opposing side gets 5 VP per damaged base
5. **Next Turn**: Turn counter increments

This means VP awards happen **at the boundary between turns**, recorded with the current turn number before incrementing.

### Integration Points

Base damage VP tracking is triggered from:

1. **UI Turn Change**: `desktop_popup.py:show_turn_change_popup()`
   ```python
   desktop_ui.turn_manager.next_phase(desktop_ui.board)
   ```

2. **Direct Turn Advance**: Any code calling `turn_manager.next_turn(board)`

### Testing

See [tests/test_base_damage_vp.py](tests/test_base_damage_vp.py) for comprehensive tests:
- `test_base_damage_awards_vp_per_turn` - Basic VP award test
- `test_undamaged_base_no_vp` - No VP for undamaged bases
- `test_damaged_base_with_positive_lf_no_vp` - No VP if LF > 0
- `test_multiple_damaged_bases_award_vp` - Multiple bases each award 5 VP
- `test_japanese_base_damage_awards_allied_vp` - Correct side attribution
- `test_next_phase_triggers_base_vp_at_turn_end` - Phase advancement integration
- `test_no_board_parameter_no_crash` - Graceful handling of missing board

All 7 tests passing ✓

