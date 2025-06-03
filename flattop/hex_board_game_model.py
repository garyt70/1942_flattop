import math

class Hex:
    def __init__(self, q, r):
        self.q = q  # axial q coordinate
        self.r = r  # axial r coordinate

    def __eq__(self, other):
        return self.q == other.q and self.r == other.r

    def __hash__(self):
        return hash((self.q, self.r))

    def __add__(self, other):
        return Hex(self.q + other.q, self.r + other.r)

    def neighbors(self):
        directions = [Hex(1, 0), Hex(1, -1), Hex(0, -1),
                      Hex(-1, 0), Hex(-1, 1), Hex(0, 1)]
        return [self + direction for direction in directions]

    def __repr__(self):
        return f"Hex({self.q}, {self.r})"

class Piece:
    """
    Represents a game piece on the hexagonal board.

    Attributes:
        owner (str): The owner of the piece (e.g., player name or identifier).
        position (Hex): The current position of the piece on the board.
    """
    def __init__(self, owner, position):
        """
        Initializes a Piece object.

        Args:
            owner (str): The owner of the piece.
            position (Hex): The initial position of the piece on the board.
        """
        self.owner = owner
        self.position = position  # A Hex object

    def move(self, target_hex):
        """
        Moves the piece to a new position.

        Args:
            target_hex (Hex): The target position to move the piece to.
        """
        self.position = target_hex

    def __repr__(self):
        """
        Returns a string representation of the Piece object.

        Returns:
            str: A string describing the piece's owner and position.
        """
        return f"Piece(owner={self.owner}, position={self.position})"

class HexBoard:
    def __init__(self, radius):
        self.radius = radius
        self.tiles = self.generate_board(radius)
        self.pieces = []

    def generate_board(self, radius):
        tiles = set()
        for q in range(-radius, radius + 1):
            r1 = max(-radius, -q - radius)
            r2 = min(radius, -q + radius)
            for r in range(r1, r2 + 1):
                tiles.add(Hex(q, r))
        return tiles

    def is_valid_tile(self, hex_coord):
        return hex_coord in self.tiles

    def add_piece(self, piece):
        if self.is_valid_tile(piece.position):
            self.pieces.append(piece)

    def get_piece_at(self, hex_coord):
        for piece in self.pieces:
            if piece.position == hex_coord:
                return piece
        return None

    def move_piece(self, piece, target_hex):
        if self.is_valid_tile(target_hex) and self.get_piece_at(target_hex) is None:
            piece.move(target_hex)
            return True
        return False

    def display(self):
        for piece in self.pieces:
            print(piece)

# === Example usage ===
if __name__ == "__main__":
    board = HexBoard(radius=2)
    p1 = Piece(owner="Player 1", position=Hex(0, 0))
    p2 = Piece(owner="Player 2", position=Hex(1, -1))
    board.add_piece(p1)
    board.add_piece(p2)

    print("Initial board:")
    board.display()

    print("\nPlayer 1 moves:")
    move_success = board.move_piece(p1, Hex(1, 0))
    print(f"Move success: {move_success}")
    board.display()
