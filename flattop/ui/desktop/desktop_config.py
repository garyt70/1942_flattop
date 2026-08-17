import math

# Hexagon settings
HEX_SIZE = 20  # Radius of hex
HEX_HEIGHT = math.sqrt(3) * HEX_SIZE
HEX_WIDTH = 2 * HEX_SIZE
HEX_SPACING = 5  # Space between hexes

# Colors
BG_COLOR = (30, 30, 30)
HEX_COLOR = (173, 216, 230)  # Light blue
HEX_BORDER = (100, 100, 100)
COLOR_JAPANESE_PIECE = (255, 0, 0)  # RED
COLOR_ALLIED_PIECE = (0, 128, 255)  # Blue

DISABLE_FOG_OF_WAR_FOR_TESTING = True  # Set to True to disable fog of war for testing