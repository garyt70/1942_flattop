# 1942 Flat Top

**1942 Flat Top** is a digital adaptation of the classic 1980s board wargame simulating naval battles in the Pacific Theater during World War II, focusing on the Battle of Midway and the Coral Sea. Players control either Japanese or Allied forces, managing air and naval operations across a hexagonal map.

## Features

- **Hexagonal Board Model:** Core logic for hex-based movement and piece management.
- **Operations Charts:** Manage air formations, task forces, carriers, and bases, following the original game's rules.
- **Air and Naval Combat:** Implements detailed combat rules, including air-to-air, anti-aircraft, and bombing missions.
- **Observation and Weather:** Realistic observation rules and weather effects, including clouds and storms.
- **AI Opponent:** Computer opponent logic for solo play.
- **Desktop UI:** Graphical interface using Pygame for interactive play, including popups for air formations, task forces, and combat results.
- **Save/Load:** Save and restore full game state to/from disk.
- **Unit Tests:** Core logic is covered by unit tests.

## Project Structure

```
flattop/
	aircombat_engine.py         # Air combat rules and resolution
	computer_oponent_engine.py  # AI logic for computer opponent
	game_engine.py              # Main game logic (non-UI)
	hex_board_game_model.py     # Board, hex, and piece models
	observation_rules.py        # Observation and visibility logic
	operations_chart_models.py  # Task forces, air formations, bases, aircraft
	save_load_game.py           # Save/load game state
	weather_model.py            # Weather and cloud logic
	ui/desktop/                 # Pygame-based desktop UI
		desktop_ui.py           # Main UI class
		base_ui.py, airformation_ui.py, taskforce_ui.py, etc.
tests/
	test_basic.py               # Board and basic logic tests
	test_desktop_ui.py          # UI and interaction tests
	test_operations_chart_models.py # Operations chart and model tests
main.py                        # Entry point for launching the game
requirements.txt               # Python dependencies
game_requirements.txt          # Game rules and notes
setup.py                       # (Optional) Setup script
```

## Installation

1. **Install Python 3.10+**
2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
   - Main dependency: `pygame`

## Running the Game

```sh
python main.py
```

This will launch the desktop UI. You can play against another human or the computer opponent.

## Game Rules

The game implements the original Avalon Hill "Flat Top" rules, including:

- Air and naval unit management
- Detailed observation and fog-of-war
- Weather effects
- Realistic combat and movement
- Scenario setup and sequence of play

See `game_requirements.txt` for detailed rules and notes.

## Testing

Run all unit tests with:

```sh
python -m unittest discover tests
```

## License

This project is a fan-made adaptation for educational and personal use. See original Avalon Hill rules for copyright.

---

Let me know if you want to add sections for contributing, screenshots, or more details!
