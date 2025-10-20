"""
Test suite for the trace_land_boundary_path pathfinding function.

These tests verify that the AI can correctly navigate task forces around islands
and handle edge cases like off-board hexes.
"""

import unittest
from flattop.hex_board_game_model import HexBoardModel, Hex, Piece
from flattop.operations_chart_models import TaskForce, Ship
from flattop.computer_oponent_engine import ComputerOpponent
from flattop.weather_model import WeatherManager
from flattop.hex_board_game_model import TurnManager


class TestPathfinding(unittest.TestCase):
    """Test pathfinding around islands."""

    def setUp(self):
        """Set up common test fixtures."""
        self.turn_mgr = TurnManager()

    def _create_test_setup(self, width, height, land_hexes, start_pos, end_pos):
        """Helper to create a test board with taskforce."""
        board = HexBoardModel(width, height, land_hexes=land_hexes)
        weather = WeatherManager(board)
        
        tf = TaskForce(1, 'TF1', 'Japanese')
        ship = Ship('TestShip', 'DD', 5, 5)
        tf.add_ship(ship)
        
        start_hex = board.get_hex(*start_pos)
        end_hex = board.get_hex(*end_pos)
        piece = Piece('TF1', 'Japanese', start_hex, tf)
        board.add_piece(piece)
        
        ai = ComputerOpponent('Japanese', board, weather, self.turn_mgr)
        return board, ai, piece, start_hex, end_hex

    def test_path_around_small_island(self):
        """Test finding path around a small 2x2 island."""
        land_hexes = [(2, 2), (2, 3), (3, 2), (3, 3)]
        board, ai, piece, start_hex, end_hex = self._create_test_setup(
            6, 6, land_hexes, (1, 2), (4, 2)
        )
        
        ai._move_taskforce_toward(piece, end_hex)
        
        # Should have moved from start position
        self.assertNotEqual(piece.position, start_hex)
        # Should have moved toward or reached the destination
        self.assertGreaterEqual(piece.position.q, 3)

    def test_path_around_edge_island(self):
        """Test finding path around island near board edge."""
        land_hexes = [(2, 0), (2, 1), (3, 0), (3, 1)]
        board, ai, piece, start_hex, end_hex = self._create_test_setup(
            6, 6, land_hexes, (1, 1), (4, 1)
        )
        
        ai._move_taskforce_toward(piece, end_hex)
        
        # Should have moved from start position
        self.assertNotEqual(piece.position, start_hex)

    def test_direct_path_no_obstacles(self):
        """Test direct path with no obstacles."""
        land_hexes = []  # No land
        board, ai, piece, start_hex, end_hex = self._create_test_setup(
            6, 6, land_hexes, (1, 2), (4, 2)
        )
        
        ai._move_taskforce_toward(piece, end_hex)
        
        # Should have moved from start position
        self.assertNotEqual(piece.position, start_hex)
        # Should have moved directly toward destination
        self.assertGreater(piece.position.q, start_hex.q)

    def test_path_around_large_island(self):
        """Test finding path around a larger island."""
        land_hexes = [
            (1, 0), (2, 0), (3, 0), (4, 0),  # Top row
            (1, 1), (2, 1), (3, 1), (4, 1),  # Second row
            (1, 2), (2, 2), (3, 2), (4, 2),  # Third row
        ]
        board, ai, piece, start_hex, end_hex = self._create_test_setup(
            6, 6, land_hexes, (0, 1), (5, 1)
        )
        
        ai._move_taskforce_toward(piece, end_hex)
        
        # Should have moved from start position
        self.assertNotEqual(piece.position, start_hex)

    def test_surrounded_by_land_can_escape(self):
        """Test that taskforce can escape if there are sea hexes beyond land barrier."""
        # Create a scenario where the taskforce is surrounded by land but can escape
        land_hexes = [
            (0, 0), (1, 0), (2, 0),
            (0, 1),         (2, 1),  # (1, 1) is where the piece starts
            (0, 2), (1, 2), (2, 2),
        ]
        board = HexBoardModel(6, 6, land_hexes=land_hexes)
        weather = WeatherManager(board)
        
        tf = TaskForce(1, 'TF1', 'Japanese')
        ship = Ship('TestShip', 'DD', 5, 5)
        tf.add_ship(ship)
        
        start_hex = board.get_hex(1, 1)  # Surrounded by land
        end_hex = board.get_hex(5, 5)
        piece = Piece('TF1', 'Japanese', start_hex, tf)
        board.add_piece(piece)
        
        ai = ComputerOpponent('Japanese', board, weather, self.turn_mgr)
        ai._move_taskforce_toward(piece, end_hex)
        
        # Should be able to move out since there are sea hexes beyond the land barrier
        # The pathfinding correctly finds a path through available sea hexes
        self.assertNotEqual(piece.position, start_hex)

    def test_path_validates_board_boundaries(self):
        """Test that pathfinding respects board boundaries."""
        # Small board with island that would require going off-board if not checked
        land_hexes = [(1, 1), (2, 1), (1, 2), (2, 2)]
        board, ai, piece, start_hex, end_hex = self._create_test_setup(
            4, 4, land_hexes, (0, 1), (3, 1)
        )
        
        # The pathfinding should not crash and should find a valid path
        # or stay in place if no path exists
        try:
            ai._move_taskforce_toward(piece, end_hex)
            # If it moved, verify it's on a valid board position
            self.assertTrue(board.is_valid_tile(piece.position))
        except Exception as e:
            self.fail(f"Pathfinding raised an exception: {e}")


if __name__ == '__main__':
    unittest.main()
