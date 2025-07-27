import unittest
import pygame
import sys
import math

from flattop.hex_board_game_model import HexBoardModel, Hex, Piece, get_distance
from flattop.operations_chart_models import AirFormation
from flattop.ui.desktop.desktop_ui import DesktopUI, PieceImageFactory, HEX_SIZE, HEX_COLOR, HEX_BORDER

class DummyPiece(Piece):
    def __init__(self, q, r, side="Allied", can_move=True, movement_factor=1):
        super().__init__("DummyPiece", side=side, position=Hex(q, r), gameModel=AirFormation(1))
        

class TestPieceImageFactory(unittest.TestCase):
    def test_airformation_image(self):
        img = PieceImageFactory.airformation_image((255, 0, 0))
        self.assertIsInstance(img, pygame.Surface)

    def test_base_image(self):
        img = PieceImageFactory.base_image((0, 255, 0))
        self.assertIsInstance(img, pygame.Surface)

    def test_taskforce_image(self):
        img = PieceImageFactory.taskforce_image((0, 0, 255))
        self.assertIsInstance(img, pygame.Surface)

class TestDesktopUI(unittest.TestCase):
    def setUp(self):
        self.board = HexBoardModel(5, 5)
        self.piece = DummyPiece(2, 2)
        self.board.pieces.append(self.piece)
        self.ui = DesktopUI(self.board)
        pygame.display.init()
        self.ui.screen = pygame.display.set_mode((200, 200))

    def tearDown(self):
        pygame.display.quit()

    def test_hex_to_pixel_and_pixel_to_hex_coord(self):
        q, r = 2, 2
        pixel = self.ui.hex_to_pixel(q, r)
        hex_obj = self.ui.pixel_to_hex_coord(*pixel)
        self.assertIsInstance(hex_obj, Hex)
        self.assertEqual((hex_obj.q, hex_obj.r), (q, r))

    def test_get_piece_at_pixel(self):
        center = self.ui.hex_to_pixel(self.piece.position.q, self.piece.position.r)
        found_piece = self.ui.get_piece_at_pixel(center)
        self.assertIs(found_piece, self.piece)

    def test_get_distance(self):
        h1 = Hex(0, 0)
        h2 = Hex(2, 2)
        dist = get_distance(h1, h2)
        self.assertIsInstance(dist, int)
        self.assertGreaterEqual(dist, 0)

    def test_draw_hex(self):
        center = self.ui.hex_to_pixel(1, 1)
        # Should not raise
        self.ui.draw_hex(center, HEX_COLOR, HEX_BORDER)

    def test_render_screen(self):
        # Should not raise
        self.ui.draw()

    def test_piece_movement_updates_board(self):
        # Simulate moving the piece to a new hex
        new_hex = Hex(3, 3)
        self.board.move_piece(self.piece, new_hex)
        self.assertEqual(self.piece.position.q, 3)
        self.assertEqual(self.piece.position.r, 3)


class TestGetDistance(unittest.TestCase):
    def setUp(self):
        self.board = HexBoardModel(5, 5)
        self.ui = DesktopUI(self.board)
        pygame.display.init()
        self.ui.screen = pygame.display.set_mode((200, 200))

    def tearDown(self):
        pygame.display.quit()

    def test_distance_same_hex(self):
        h1 = Hex(1, 1)
        h2 = Hex(1, 1)
        dist = get_distance(h1, h2)
        self.assertEqual(dist, 0)

    def test_distance_adjacent_hexes(self):
        #testing “odd-q” vertical layout shoves odd columns down
        h1 = Hex(2, 2)
        neighbors = [
            Hex(2, 1), Hex(3, 1), Hex(3, 2),
            Hex(2, 3), Hex(1, 2), Hex(1, 1)
        ]
        for h2 in neighbors:
            with self.subTest(h2=h2):
                dist = get_distance(h1, h2)
                self.assertEqual(dist, 1)

    def test_distance_diagonal(self):
        h1 = Hex(0, 0)
        h2 = Hex(2, 2)
        dist = get_distance(h1, h2)
        self.assertEqual(dist, 3)

    def test_distance_far_apart(self):
        h1 = Hex(0, 0)
        h2 = Hex(4, 4)
        dist = get_distance(h1, h2)
        self.assertIsInstance(dist, int)
        self.assertGreater(dist, 0)

    def test_distance_negative_coords(self):
        h1 = Hex(4, 4)
        h2 = Hex(3, 2)
        dist = get_distance(h1, h2)
        self.assertEqual(dist, 2)
if __name__ == "__main__":
    unittest.main()