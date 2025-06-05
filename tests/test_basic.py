import unittest

from flattop.hex_board_game_model import HexBoard

class TestHexBoardGamesModel(unittest.TestCase):
    def test_hex_board_initialization(self):
        board = HexBoard(radius=11)
        self.assertEqual(board.radius, 11)
        #self.assertTrue(all(len(row) == 11 for row in board.grid))
"""
    def test_player_creation(self):
        player = Player(name="Alice", color="Red")
        self.assertEqual(player.name, "Alice")
        self.assertEqual(player.color, "Red")

    def test_game_initialization(self):
        game = Game(board_size=11, player1_name="Alice", player2_name="Bob")
        self.assertEqual(game.board.size, 11)
        self.assertEqual(game.player1.name, "Alice")
        self.assertEqual(game.player2.name, "Bob")

    def test_make_move(self):
        game = Game(board_size=11, player1_name="Alice", player2_name="Bob")
        result = game.make_move(player=game.player1, x=5, y=5)
        self.assertTrue(result)
        self.assertEqual(game.board.grid[5][5], game.player1)

    def test_invalid_move(self):
        game = Game(board_size=11, player1_name="Alice", player2_name="Bob")
        game.make_move(player=game.player1, x=5, y=5)
        result = game.make_move(player=game.player2, x=5, y=5)  # Same spot
        self.assertFalse(result)

    def test_check_winner(self):
        game = Game(board_size=3, player1_name="Alice", player2_name="Bob")
        game.make_move(player=game.player1, x=0, y=0)
        game.make_move(player=game.player1, x=1, y=1)
        game.make_move(player=game.player1, x=2, y=2)
        winner = game.check_winner()
        self.assertEqual(winner, game.player1)
"""

if __name__ == "__main__":
    unittest.main()