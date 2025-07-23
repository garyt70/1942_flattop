import pygame
import flattop.ui.desktop.desktop_config as config
import math


# Import color and size constants from config
HEX_SIZE = config.HEX_SIZE
HEX_HEIGHT = config.HEX_HEIGHT
HEX_WIDTH = config.HEX_WIDTH
HEX_SPACING = config.HEX_SPACING
BG_COLOR = config.BG_COLOR
HEX_COLOR = config.HEX_COLOR
HEX_BORDER = config.HEX_BORDER
COLOR_JAPANESE_PIECE = config.COLOR_JAPANESE_PIECE
COLOR_ALLIED_PIECE = config.COLOR_ALLIED_PIECE

class PieceImageFactory:
    """
    Generates pygame.Surface images for AirFormation, Base, and TaskForce pieces.
    Each image is a colored shape (circle, triangle, or square) with a simple icon drawn in the center.
    """

    @staticmethod
    def airformation_image(color, size=HEX_SIZE):
        # Circle with a simple "plane" icon (horizontal line and tail)
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        radius = size // 1.5 #3
        pygame.draw.circle(surf, color, center, radius)
        # Draw a simple plane: a line with a tail
        pygame.draw.line(surf, (255, 255, 255), (center[0] - radius//2, center[1]), (center[0] + radius//2, center[1]), 2)
        pygame.draw.line(surf, (255, 255, 255), (center[0], center[1]), (center[0], center[1] + radius//2), 2)
        return surf

    @staticmethod
    def base_image(color, size=HEX_SIZE):
        # Triangle with a simple "building" icon (rectangle and door)
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        tri_size = size #// 2
        points = [
            (center[0], center[1] - tri_size//2),
            (center[0] - tri_size//2, center[1] + tri_size//2),
            (center[0] + tri_size//2, center[1] + tri_size//2)
        ]
        pygame.draw.polygon(surf, color, points)
        # Draw a simple building: rectangle and door
        rect_w, rect_h = tri_size//2, tri_size//3
        rect_x = center[0] - rect_w//2
        rect_y = center[1]
        pygame.draw.rect(surf, (255, 255, 255), (rect_x, rect_y, rect_w, rect_h))
        # Door
        door_w, door_h = rect_w//3, rect_h//2
        door_x = center[0] - door_w//2
        door_y = rect_y + rect_h - door_h
        pygame.draw.rect(surf, (100, 100, 100), (door_x, door_y, door_w, door_h))
        return surf

    @staticmethod
    def taskforce_image(color, size=HEX_SIZE):
        # Draw a fleet of 4 ships (rectangles) in formation, top-down view, on a square playing piece with background color
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        # Draw the square playing piece background
        bg_color = color  # Board background color, adjust as needed
        pygame.draw.rect(surf, bg_color, (0, 0, size, size), border_radius=6)
        pygame.draw.rect(surf, (200, 200, 200), (0, 0, size, size), 2, border_radius=6)

        ship_w = size // 3
        ship_h = size // 8
        spacing = size // 10
        # Arrange ships in two rows of two
        start_x = (size - (2 * ship_w + spacing)) // 2
        start_y = (size - (2 * ship_h + spacing)) // 2
        ship_color = color
        outline_color = (255, 255, 255)
        for row in range(2):
            for col in range(2):
                x = start_x + col * (ship_w + spacing)
                y = start_y + row * (ship_h + spacing)
                rect = pygame.Rect(x, y, ship_w, ship_h)
                pygame.draw.rect(surf, ship_color, rect)
                pygame.draw.rect(surf, outline_color, rect, 2)
                # Draw a small bridge on each ship (a small square at the front)
                bridge_w = ship_w // 5
                bridge_h = ship_h // 2
                bridge_x = x + ship_w // 2 - bridge_w // 2
                bridge_y = y
                pygame.draw.rect(surf, outline_color, (bridge_x, bridge_y, bridge_w, bridge_h))
        return surf

    @staticmethod
    def stack_image(pieces, size=HEX_SIZE):
        """
        Draws a stack indicator for multiple pieces in a hex, as overlapping squares.
        Each square is the same size as the hex, but offset so the stack is visible.
        The top piece is fully visible, and each piece underneath is offset and partially visible.
        pieces: list of Piece objects in the stack (max 4 shown).
        """
        surf = pygame.Surface((size + size // 1.5, size + size // 1.5), pygame.SRCALPHA)
        overlap = size // 4  # Amount each square is offset to show underneath
        max_show = min(len(pieces), 4)

        def piece_color(piece):
            color = (200, 200, 255, 120) # assume cloud or storm
            if getattr(piece, "side", "") == "Allied":
                color = COLOR_ALLIED_PIECE
            elif getattr(piece, "side", "") == "Japanese":
                color = COLOR_JAPANESE_PIECE
            return color

        # Draw from bottom to top so the top piece is fully visible
        for i in range(max_show):
            color = piece_color(pieces[i])
            offset = (max_show - 1 - i) * overlap
            rect = pygame.Rect(offset, offset, size, size)
            pygame.draw.rect(surf, color, rect)
            pygame.draw.rect(surf, (200, 200, 200), rect, 2)

        # Draw a number if more than 4
        if len(pieces) > 4:
            font = pygame.font.SysFont(None, 18)
            text = font.render(str(len(pieces)), True, (255, 255, 255))
            text_rect = text.get_rect(center=(surf.get_width() // 1.5, surf.get_height() // 1.5))
            surf.blit(text, text_rect)
        return surf

    @staticmethod
    def cloud_image(size=HEX_SIZE):
        """
        Draws a semi-transparent blue/white circle for a cloud marker.
        """
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        radius = size // 2
        pygame.draw.circle(surf, (200, 200, 255, 120), center, radius)
        # Optional: add a "C" label
        font = pygame.font.SysFont(None, 18)
        label = font.render("C", True, (80, 80, 255))
        surf.blit(label, (center[0] - 8, center[1] - 8))
        return surf

    @staticmethod
    def storm_image(size=HEX_SIZE):
        """
        Draws a semi-transparent dark gray/blue circle for a storm marker.
        """
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        radius = size // 2
        pygame.draw.circle(surf, (80, 80, 160, 160), center, radius)
        # Optional: add an "S" label
        font = pygame.font.SysFont(None, 18, bold=True)
        label = font.render("S", True, (255, 255, 0))
        surf.blit(label, (center[0] - 8, center[1] - 8))
        return surf

    @staticmethod
    def wind_direction_image(direction, sector, size=HEX_SIZE):
        """
        Draws a wind direction arrow and sector label.
        direction: 1-6 (hex direction)
        sector: 1-8
        """
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        arrow_length = size // 2
        angle = (direction - 1) * 60  # 0 is east, 1 is NE, etc.
        radians = math.radians(angle)
        end_x = center[0] + arrow_length * math.cos(radians)
        end_y = center[1] + arrow_length * math.sin(radians)
        pygame.draw.line(surf, (255, 255, 0), center, (end_x, end_y), 3)
        # Draw sector number
        font = pygame.font.SysFont(None, 18)
        label = font.render(f"W{sector}", True, (255, 255, 0))
        surf.blit(label, (center[0] - 12, center[1] - 12))
        return surf

