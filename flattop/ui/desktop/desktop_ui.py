import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt5.QtGui import QPainter, QColor, QPolygonF
from PyQt5.QtCore import QPointF
import os

import importlib.util

from flattop.hex_board_game_model import HexBoard, Piece, Hex

class HexBoardWidget(QWidget):
    def __init__(self, board, parent=None):
        super().__init__(parent)
        self.board = board
        self.hex_size = 40
        self.margin = 20

    def paintEvent(self, event):
        painter = QPainter(self)
        for y, row in enumerate(self.board.grid):
            for x, cell in enumerate(row):
                center = self.hex_center(x, y)
                polygon = self.hex_polygon(center)
                color = QColor(200, 200, 255) if cell is None else QColor(100, 200, 100)
                painter.setBrush(color)
                painter.drawPolygon(polygon)

    def hex_center(self, x, y):
        size = self.hex_size
        width = size * 3/2
        height = size * (3**0.5)
        cx = self.margin + x * width
        cy = self.margin + y * height + (x % 2) * (height / 2)
        return QPointF(cx, cy)

    def hex_polygon(self, center):
        size = self.hex_size
        points = []
        for i in range(6):
            angle_deg = 60 * i - 30
            angle_rad = 3.14159 / 180 * angle_deg
            x = center.x() + size * 0.95 * (3**0.5) * 0.5 * (2 if i % 3 == 0 else 1) * (1 if i < 3 else -1) * (1 if i % 2 == 0 else 0)
            y = center.y() + size * 0.95 * (1 if i % 2 == 1 else 0)
            # Use trigonometry for accurate hex points
            x = center.x() + size * 0.95 * (3**0.5) * 0.5 * (1 if i in [0,5] else -1 if i in [2,3] else 0)
            y = center.y() + size * 0.95 * (1 if i in [1,2] else -1 if i in [4,5] else 0)
            points.append(QPointF(
                center.x() + size * 0.95 * (3**0.5) * 0.5 * (1 if i in [0,5] else -1 if i in [2,3] else 0),
                center.y() + size * 0.95 * (1 if i in [1,2] else -1 if i in [4,5] else 0)
            ))
        return QPolygonF(points)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hex Board Game Visualizer")
        # Assume hex_board_game_model has a Board class with a 'grid' attribute
        board = HexBoard(radius=2)
        p1 = Piece(owner="Player 1", position=Hex(0, 0))
        p2 = Piece(owner="Player 2", position=Hex(1, -1))
        board.add_piece(p1)
        board.add_piece(p2)



        widget = HexBoardWidget(board)
        layout = QVBoxLayout()
        layout.addWidget(widget)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())