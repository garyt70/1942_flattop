import math
from flattop import operations_chart_models
from flattop.operations_chart_models import AirFormation,  Aircraft, Base, TaskForce, Carrier


class Hex:
    def __init__(self, q, r, terrain="sea"):
        self.q = q  # axial q coordinate
        self.r = r  # axial r coordinate
        self.terrain = terrain  # "sea" or "land"

    def __eq__(self, other):
        return self.q == other.q and self.r == other.r #and self.terrain == other.terrain

    def __hash__(self):
        return hash((self.q, self.r, self.terrain))

    def __add__(self, other):
        return Hex(self.q + other.q, self.r + other.r, self.terrain)

    def neighbors(self):
        directions = [Hex(1, 0), Hex(1, -1), Hex(0, -1),
                      Hex(-1, 0), Hex(-1, 1), Hex(0, 1)]
        return [self + direction for direction in directions]

    def __iter__(self):
        yield self.q
        yield self.r

    def __repr__(self):
        return f"Hex({self.q}, {self.r}, terrain={self.terrain})"

class Piece:
    """
    Represents a game piece on the hexagonal board.

    Attributes:
        owner (str): The owner of the piece (e.g., player name or identifier).
        position (Hex): The current position of the piece on the board.
        games_model (HexBoardModel): The game model this piece belongs to, it can be AirFormation or TaskForce (optional).
    """
    def __init__(self, name, side="Allied", position=Hex(0,0), gameModel=None):
        """
        Initializes a Piece object.

        Args:
            owner (str): The owner of the piece.
            position (Hex): The initial position of the piece on the board.
        """
        self.name = name  # Name or identifier for the piece
        self.side = side
        self.position = position  # A Hex object
        self._game_model = gameModel  # Optional reference to the game model, which can be an AirFormation or TaskForce, Base, etc.
        self.has_moved = False  # Flag to track if the piece has moved
        self.phase_move_count = 0  # Count hexes moved into in the current phase

    @property
    def game_model(self):
        return self._game_model

    @game_model.setter
    def game_model(self, value):
        allowed_types = (
            getattr(operations_chart_models, "AirFormation", None),
            getattr(operations_chart_models, "TaskForce", None),
            getattr(operations_chart_models, "Base", None)
        )
        if value is not None and not isinstance(value, allowed_types):
            raise TypeError("game_model must be an Base, AirFormation or TaskForce instance")
        self._game_model = value

    @property
    def movement_factor(self):
        """
        Returns the movement factor for the piece's game_model if available.

        Returns:
            int or float or None: The movement factor if the game_model has it, otherwise None.
        """
        if hasattr(self._game_model, "movement_factor"):
            return self._game_model.movement_factor
        return 0

    @property
    def can_move(self):
        """
        Determines if the piece can move based on its game model type.

        Returns:
            bool: True if the piece can move, False otherwise.
        """
        can_move = isinstance(self._game_model, (operations_chart_models.AirFormation, operations_chart_models.TaskForce))

        return can_move
    
    @property
    def can_attack(self):
        """
        Determines if the piece can attack based on its game model type. And if it has the can_attack attribute.

        Returns:
            bool: True if the piece can attack, False otherwise.
        """
        can_attack = False
        if isinstance(self._game_model, (operations_chart_models.AirFormation, operations_chart_models.TaskForce)):
            can_attack = self._game_model.can_attack 

        return can_attack
    
    @property
    def can_observe(self):
        """
        Determines if the piece can observe based on its game model type.

        Returns:
            bool: True if the piece can observe, False otherwise.
        """
        can_observe = False
        if self._game_model is not None:
            if hasattr(self._game_model, 'can_observe'):
                can_observe = self._game_model.can_observe
        
        return can_observe

    @property
    def observed_condition(self):
        """
        see obsevervation_rules.py for details on what the conditions are.
        """
        observed_condition = 0
        if self._game_model is not None:
            if hasattr(self._game_model, 'observed_condition'):
                observed_condition = self._game_model.observed_condition
        # If the game model has a has_been_observed attribute, return its value
        return observed_condition
        

    def move(self, target_hex):
        """
        Moves the piece to a new position.

        Args:
            target_hex (Hex): The target position to move the piece to.
        """

        distance = get_distance(self.position, target_hex)

        #only AirFormation and TaskForce can move
        if self.can_move and not self.has_moved:
           self.position = target_hex
           self.phase_move_count += distance
           if self.phase_move_count < self.movement_factor:
               self.has_moved = False # still available moves in this phase
           else:
               self.has_moved = True

    def __repr__(self):
        """
        Returns a string representation of the Piece object.

        Returns:
            str: A string describing the piece's owner and position.
        """
        strValueToReturn = f"Piece(owner={self.side}, position={self.position})"
        if self._game_model is not None:
            strValueToReturn += f", game_model={self._game_model})"
            

        return strValueToReturn

class HexBoardModel:
    def __init__(self, width, height, land_hexes=None, players = []):
        self.width = width
        self.height = height
        self.land_hexes = set(land_hexes) if land_hexes else set()
        self.tiles = set(self.generate_board(width, height))
        self.pieces = []
        self.players = dict() # this is a dictionary of AirOperationsChart

    def generate_board(self, width, height):
        # Generates a rectangular grid of hexes using axial coordinates
        for q in range(width):
            for r in range(height):
                terrain = "land" if (q, r) in self.land_hexes else "sea"
                yield Hex(q, r, terrain=terrain)

    def get_hex(self, q, r):
        """
        Returns the Hex object at the given (q, r) coordinates, or None if not found.
        """
        for tile in self.tiles:
            if tile.q == q and tile.r == r:
                return tile
        return None

    def is_valid_tile(self, hex_coord):
        return any(tile.q == hex_coord.q and tile.r == hex_coord.r for tile in self.tiles)

    def add_piece(self, piece):
        if self.is_valid_tile(piece.position):
            self.pieces.append(piece)

    def get_piece_at(self, hex_coord):
        for piece in self.pieces:
            if piece.position == hex_coord:
                return piece
        return None

    def move_piece(self, piece : Piece, target_hex : Hex):
        is_valid_tile = self.is_valid_tile(target_hex)

        # Prevent TaskForce from moving into land hex
        is_task_force = (
            hasattr(piece, "game_model") and
            getattr(operations_chart_models, "TaskForce", None) is not None and
            isinstance(piece.game_model, operations_chart_models.TaskForce)
        )
        is_land_hex = self.get_terrain(target_hex) == "land"
        if is_task_force and is_land_hex:
            return False

        if is_valid_tile and piece.can_move:
            piece.move(target_hex)
            return True
        return False

    def get_terrain(self, hex_coord):
        for tile in self.tiles:
            if tile.q == hex_coord.q and tile.r == hex_coord.r:
                return tile.terrain
        return None

    def display(self):
        for piece in self.pieces:
            print(piece)

    def get_pieces_by_side(self, side):
        """
        Returns a list of pieces owned by the specified side.
        
        Args:
            side (str): The side to filter pieces by (e.g., "Allied", "Japanese").
        
        Returns:
            list: A list of Piece objects owned by the specified side.
        """
        return [piece for piece in self.pieces if piece.side == side]

    def reset_pieces_for_new_turn(self):
        """
        Resets the has_moved flag for all pieces at the start of a new turn.
        """
        piece : Piece
        for piece in self.pieces:
            piece.has_moved = False
            piece.phase_move_count = 0  # Reset the move count for the new turn
            # If the piece is an AirFormation, update aircraft ranges and remove those out of fuel
            if isinstance(piece.game_model, AirFormation):
                af: AirFormation = piece.game_model
                ac: Aircraft
                to_remove = []
                for ac in af.aircraft:
                    ac.range_remaining -= 1
                    if ac.range_remaining <= 0:
                        to_remove.append(ac)
                for ac in to_remove:
                    af.remove_aircraft(ac)
                    print(f"Air Formation {af.name}: Aircraft {ac.type} ran out of fuel and was removed.")
                if len(af.aircraft) <= 0:
                    #the airformation is destroyed
                    self.pieces.remove(piece)
                    print(f"Air Formation {af.name}, ran out of fuel")
                af.reset_for_new_turn()
            elif isinstance(piece.game_model, Base):
                base: Base
                base = piece.game_model
                base.reset_for_new_turn()
            elif isinstance(piece.game_model, TaskForce):
                tf:TaskForce
                tf = piece.game_model
                tf.reset_for_new_turn()
                

def get_distance(start_hex: Hex, dest_hex: Hex):
    # Calculate distance using offset coordinates (odd-q vertical layout)
    # See: https://www.redblobgames.com/grids/hexagons/#distances-offset
    # Convert offset (odd-q) coordinates to cube coordinates for accurate distance calculation
    def offset_to_cube(q, r):
            # Odd-q vertical layout
            x = q
            z = r - (q - (q & 1)) // 2
            y = -x - z
            return (x, y, z)
    start_cube = offset_to_cube(start_hex.q, start_hex.r)
    dest_cube = offset_to_cube(dest_hex.q, dest_hex.r)
    dx = dest_cube[0] - start_cube[0]
    dy = dest_cube[1] - start_cube[1]
    dz = dest_cube[2] - start_cube[2]
    distance = max(abs(dx), abs(dy), abs(dz))
    #print(f"Cube distance from {start_hex} to {dest_hex}: {distance}")
    return distance

class TurnManager:
    """
    Manages the game turns, days, and hour tracking.

    There are ten phases within each turn. Phases may not be skipped or performed out of sequence. Players perform all phases simultaneously except the Plane Movement Phase.

    1. **Weather Phase** — Wind direction changes are made and Cloud markers are moved.
    2. **Air Operations Phase** — Planes are readied and placed in Air Formations.
    3. **Task Force Movement Plotting Phase** — Movement for all TFs is logged on the Plot Map.
    4. **Shadowing Phase** — TFs and Air Formations that are shadowing and TFs that are being shadowed are moved on the mapboard.
    5. **Task Force Movement Execution Phase** — TFs which did not move in the Shadowing Phase are moved on the mapboard or on the Plot Map according to their plotted move.
    6. **Initiative Phase** — Players determine which player has the initiative.
    7. **Plane Movement Phase** — The player with the initiative moves all his Air Formations on the mapboard and on the Plot Map, then the player without the initiative does the same.
    8. **Combat Phase** — All combat is resolved, one battle at a time, following the Combat sequence for each battle.
    9. **Repair Phase** — Damaged bases are repaired.
    10. **Time Record Phase** — The passage of one turn is marked on the Time Record Chart.

    """

    PHASES = [
        "Air Operations",
        "Shadowing",
        "Task Force Movement",
        "Plane Movement",
        "Combat",
        "Repair",
    ]

    def __init__(self, total_days=1):
        self.total_days = total_days
        self.current_day = 1
        self.current_hour = 0  # 0 to 23
        self.turn_number = 1
        self.current_phase_index = 0
        self.side_with_initiative = None  # Player with initiative, can be set later
        self._decide_initiative("Allied", "Japanese")  # Default players, can be set later
        self.combat_results_history = []  # Store combat results for later reference
        self._last_combat_result = None

    def add_combat_result(self, combat_result):
        self.combat_results_history.append(combat_result)
        self._last_combat_result = combat_result

    @property    
    def last_combat_result(self):
        return self._last_combat_result

    @last_combat_result.setter
    def last_combat_result(self, value):
        self._last_combat_result = value

    @property
    def current_phase(self):
        return self.PHASES[self.current_phase_index]

    def next_phase(self):
        """
        Advances to the next phase. If at the end of the phase list, advances to the next turn.
        """
        self.current_phase_index += 1
        if self.current_phase_index >= len(self.PHASES):
            self.current_phase_index = 0
            self.next_turn()

    def next_turn(self):
        """
        Advances the game by one turn (one hour).
        """
        self.current_hour += 1
        self.turn_number += 1
        if self.current_hour >= 24:
            self.current_hour = 0
            self.current_day += 1
        self.current_phase_index = 0
        self.side_with_initiative = None  # Reset initiative at the start of a new turn
        self._decide_initiative("Allied", "Japanese")  # Reset initiative for new turn

    def _decide_initiative(self, player1, player2):
        """
        During the Initiative Phase in the Sequence of Play, both players roll one die. The player with the higher roll gains the initiative for that turn. If the die roll is a tie, the player who did not have the initiative last turn gains the initiative this turn. The player with the initiative will go first during the Plane Movement Phase.
        """
        import random
        roll1 = random.randint(1, 6)
        roll2 = random.randint(1, 6)
        if roll1 > roll2:
            self.side_with_initiative = player1
        elif roll2 > roll1:
            self.side_with_initiative = player2
        else:
            # Tie goes to the player who did not have initiative last turn
            self.side_with_initiative = player2 if self.side_with_initiative == player1 else player1

    def reset(self):
        """
        Resets the turn manager to the beginning.
        """
        self.current_day = 1
        self.current_hour = 0
        self.turn_number = 1
        self.current_phase_index = 0

    def is_night(self):
        #determine if the turn hour is night
        return self.current_hour < 6 or self.current_hour >= 18

    def __repr__(self):
        return (f"TurnManager(day={self.current_day}, hour={self.current_hour}, "
                f"turn={self.turn_number}, phase='{self.current_phase}')")
   

    def is_game_over(self):
        """
        Returns True if the scenario has ended.
        """
        return self.current_day > self.total_days


# === Example usage ===
if __name__ == "__main__":
    # Define which hexes are land
    land_hexes = {Hex(0, 0), Hex(1, 1)}
    board = HexBoardModel(3, 3, land_hexes=land_hexes)

    p1 = Piece(side="Player 1", position=Hex(0, 0))
    p2 = Piece(side="Player 2", position=Hex(1, -1))
    board.add_piece(p1)
    board.add_piece(p2)

    print("Initial board:")
    board.display()

    print("\nPlayer 1 moves:")
    move_success = board.move_piece(p1, Hex(1, 0))
    print(f"Move success: {move_success}")
    board.display()

    # Check terrain
    print(board.get_terrain(Hex(0, 0)))  # "land"
    print(board.get_terrain(Hex(0, 1)))  # "sea"

    turn_manager = TurnManager(total_days=2)
    print(turn_manager)
    while not turn_manager.is_game_over():
        # At the start of each turn, reset piece movement
        board.reset_pieces_for_new_turn()
        print(f"Turn {turn_manager.turn_number}: Day {turn_manager.current_day}, Hour {turn_manager.current_hour}")
        # ... game logic here ...
        turn_manager.next_turn()
    print("Game over!")