import os
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

# ---------------------------------------------------------------------------
# Asset overlay helpers
# ---------------------------------------------------------------------------
_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
_overlay_cache: dict = {}


def _load_overlay(name: str, size: int):
    """Return a pygame.Surface overlay scaled to (size, size), or None on failure."""
    key = (name, size)
    if key in _overlay_cache:
        return _overlay_cache[key]
    path = os.path.join(_ASSETS_DIR, name)
    try:
        #assume pygame is initialized and can load images
        raw = pygame.image.load(path).convert_alpha()
        scaled = pygame.transform.smoothscale(raw, (size, size))
        _overlay_cache[key] = scaled
        return scaled
    except Exception:
        _overlay_cache[key] = None
        return None


class PieceImageFactory:
    """
    Generates pygame.Surface images for AirFormation, Base, and TaskForce pieces.
    Each image is a colored shape (circle, triangle, or square) with a simple icon drawn in the center.
    """

    @staticmethod
    def airformation_image(color, size=int(HEX_HEIGHT) - 2, observed=False, range_condition="normal"):
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        radius = size // 2 - 1

        # --- base layer: colored circle ---
        pygame.draw.circle(surf, color, center, radius)

        # --- emblem overlay: retro aircraft silhouette (PNG), fallback to lines ---
        overlay = _load_overlay("overlay_airformation.png", size)
        if overlay is not None:
            surf.blit(overlay, (0, 0))
        else:
            pygame.draw.line(surf, (255, 255, 255), (center[0] - radius//2, center[1]), (center[0] + radius//2, center[1]), 2)
            pygame.draw.line(surf, (255, 255, 255), (center[0], center[1]), (center[0], center[1] + radius//2), 2)

        # Draw range condition indicators as 4 boxes at the bottom
        box_size = radius // 4
        box_spacing = 2
        total_width = (box_size * 4) + (box_spacing * 3)
        start_x = center[0] - total_width // 2
        start_y = center[1] + radius // 1.5
        
        # Determine how many boxes to fill based on range condition
        filled_boxes = 4  # default "normal"
        if range_condition == "half":
            filled_boxes = 2
        elif range_condition == "low":
            filled_boxes = 1
        
        # Draw 4 boxes
        for i in range(4):
            box_x = start_x + i * (box_size + box_spacing)
            box_rect = pygame.Rect(box_x, start_y, box_size, box_size)
            
            if i < filled_boxes:
                # Filled box
                pygame.draw.rect(surf, (0, 0, 0), box_rect)
            else:
                # Empty box (just outline)
                pygame.draw.rect(surf, (255, 255, 255), box_rect, 1)
                
        if observed:
            #draw a smaill circle coloured orange at the top right corner of the image
            pygame.draw.circle(surf, (255, 165, 0), (size - 5, 5), 5)
            # draw a small white border around the orange circle
            pygame.draw.circle(surf, (255, 255, 255), (size - 5, 5), 5, 1)
        return surf


    @staticmethod
    def base_image(color, size=int(HEX_HEIGHT) - 2):
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        tri_size = size

        # --- base layer: colored upward-pointing triangle ---
        points = [
            (center[0], center[1] - tri_size // 2),
            (center[0] - tri_size // 2, center[1] + tri_size // 2),
            (center[0] + tri_size // 2, center[1] + tri_size // 2),
        ]
        pygame.draw.polygon(surf, color, points)

        # --- emblem overlay: retro anchor symbol (PNG), fallback to building icon ---
        overlay = _load_overlay("overlay_base.png", size)
        if overlay is not None:
            surf.blit(overlay, (0, 0))
        else:
            rect_w, rect_h = tri_size // 2, tri_size // 3
            rect_x = center[0] - rect_w // 2
            rect_y = center[1]
            pygame.draw.rect(surf, (255, 255, 255), (rect_x, rect_y, rect_w, rect_h))
            door_w, door_h = rect_w // 3, rect_h // 2
            door_x = center[0] - door_w // 2
            door_y = rect_y + rect_h - door_h
            pygame.draw.rect(surf, (100, 100, 100), (door_x, door_y, door_w, door_h))
        return surf

    @staticmethod
    def taskforce_image(color, size=int(HEX_HEIGHT) - 2, observed=False):
        surf = pygame.Surface((size, size), pygame.SRCALPHA)

        # --- base layer: colored rounded square ---
        pygame.draw.rect(surf, color, (0, 0, size, size), border_radius=6)
        pygame.draw.rect(surf, (200, 200, 200), (0, 0, size, size), 2, border_radius=6)

        # --- emblem overlay: retro top-down ship silhouettes (PNG), fallback to rectangles ---
        overlay = _load_overlay("overlay_taskforce.png", size)
        if overlay is not None:
            surf.blit(overlay, (0, 0))
        else:
            ship_w = size // 3
            ship_h = size // 8
            spacing = size // 10
            start_x = (size - (2 * ship_w + spacing)) // 2
            start_y = (size - (2 * ship_h + spacing)) // 2
            outline_color = (255, 255, 255)
            for row in range(2):
                for col in range(2):
                    x = start_x + col * (ship_w + spacing)
                    y = start_y + row * (ship_h + spacing)
                    rect = pygame.Rect(x, y, ship_w, ship_h)
                    pygame.draw.rect(surf, color, rect)
                    pygame.draw.rect(surf, outline_color, rect, 2)
                    bridge_w = ship_w // 5
                    bridge_h = ship_h // 2
                    bridge_x = x + ship_w // 2 - bridge_w // 2
                    pygame.draw.rect(surf, outline_color, (bridge_x, y, bridge_w, bridge_h))

        if observed:
            # Draw a small circle in the top right corner to indicate observation
            pygame.draw.circle(surf, (255, 165, 0), (size - 5, 5), 5)
            # Draw a small white border around the orange circle
            pygame.draw.circle(surf, (255, 255, 255), (size - 5, 5), 5, 1)
        return surf

    @staticmethod
    def stack_image(pieces, size=int((int(HEX_HEIGHT) - 2) * 0.9), observed=False):
        """
        Draws a stack indicator for multiple pieces in a hex, as overlapping squares.
        Each square is the same size as the hex, but offset so the stack is visible.
        The top piece is fully visible, and each piece underneath is offset and partially visible.
        pieces: list of Piece objects in the stack (max 4 shown).
        """
        surf_dim = int(size + size * 2 // 3)
        surf = pygame.Surface((surf_dim, surf_dim), pygame.SRCALPHA)
        overlap = size // 4  # Amount each square is offset to show underneath
        max_show = min(len(pieces), 4)

        _OVERLAY_MAP = {
            "AirFormation": "overlay_airformation.png",
            "Base":         "overlay_base.png",
            "TaskForce":    "overlay_taskforce.png",
        }

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

        # Blit the overlay for the top piece (always at offset 0, 0)
        top_piece = pieces[max_show - 1]
        model_type = type(getattr(top_piece, "game_model", None)).__name__
        overlay_name = _OVERLAY_MAP.get(model_type)
        if overlay_name:
            overlay = _load_overlay(overlay_name, size)
            if overlay is not None:
                surf.blit(overlay, (0, 0))

        # Draw a number if more than 4
        if len(pieces) > 4:
            font = pygame.font.SysFont(None, 18)
            text = font.render(str(len(pieces)), True, (255, 255, 255))
            text_rect = text.get_rect(center=(surf_dim * 2 // 3, surf_dim * 2 // 3))
            surf.blit(text, text_rect)

        if observed:
            # Draw a small circle in the top right corner to indicate observation
            pygame.draw.circle(surf, (255, 165, 0), (size - 5, 5), 5)
            # Draw a small white border around the orange circle
            pygame.draw.circle(surf, (255, 255, 255), (size - 5, 5), 5, 1)
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

