import math
from flattop import operations_chart_models


class Hex:
    def __init__(self, q, r, terrain="sea"):
        self.q = q  # axial q coordinate
        self.r = r  # axial r coordinate
        self.terrain = terrain  # "sea" or "land"

    def __eq__(self, other):
        return self.q == other.q and self.r == other.r and self.terrain == other.terrain

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
            raise TypeError("game_model must be an AirFormation or TaskForce instance")
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

    def move(self, target_hex):
        """
        Moves the piece to a new position.

        Args:
            target_hex (Hex): The target position to move the piece to.
        """

        #only AirFormation and TaskForce can move
        if self.can_move:
           self.position = target_hex

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
    def __init__(self, width, height, land_hexes=None):
        self.width = width
        self.height = height
        self.land_hexes = set(land_hexes) if land_hexes else set()
        self.tiles = set(self.generate_board(width, height))
        self.pieces = []

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

    def move_piece(self, piece, target_hex):
        is_valid_tile = self.is_valid_tile(target_hex)
        is_empty_tile = self.get_piece_at(target_hex) is None

        # Prevent TaskForce from moving into land hex
        is_task_force = (
            hasattr(piece, "game_model") and
            getattr(operations_chart_models, "TaskForce", None) is not None and
            isinstance(piece.game_model, operations_chart_models.TaskForce)
        )
        is_land_hex = self.get_terrain(target_hex) == "land"
        if is_task_force and is_land_hex:
            return False

        if is_valid_tile and is_empty_tile:
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
