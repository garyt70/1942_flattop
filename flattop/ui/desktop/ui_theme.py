"""
Military/Tactical HUD theme constants and reusable UI components for the 1942 Flattop desktop UI.
All popup windows with scrollable content should import from this module for consistent styling.
"""

import pygame

# ---------------------------------------------------------------------------
# Military HUD Colour Palette
# ---------------------------------------------------------------------------

# Backgrounds
THEME_BG = (18, 24, 18)            # Deep olive-black (main popup background)
THEME_PANEL = (28, 36, 28)         # Slightly lighter panel areas

# Borders & separators
THEME_BORDER = (80, 130, 65)       # Muted tactical green
THEME_SEPARATOR = (55, 85, 45)     # Subdued separator line

# Text
THEME_TEXT = (195, 215, 175)       # Off-white with green tint (body text)
THEME_TEXT_HEADER = (220, 185, 65) # Amber (section headers / titles)
THEME_TEXT_DIM = (130, 150, 115)   # Dimmed text (hints, close instructions)

# Buttons
THEME_BTN_BG = (50, 105, 40)       # Active green button
THEME_BTN_HOVER = (70, 140, 55)    # Hover state
THEME_BTN_DISABLED = (45, 52, 45)  # Greyed-out disabled button
THEME_BTN_TEXT = (220, 240, 200)   # Button label text
THEME_BTN_DANGER = (130, 40, 40)   # Red close / danger button
THEME_BTN_DANGER_HOVER = (170, 55, 55)

# Scrollbar
THEME_SCROLLBAR_TRACK = (28, 36, 28)     # Track background
THEME_SCROLLBAR_THUMB = (80, 130, 65)    # Thumb (matches border colour)
THEME_SCROLLBAR_THUMB_HOVER = (110, 165, 90)

# ---------------------------------------------------------------------------
# Spacing Constants
# ---------------------------------------------------------------------------

MARGIN = 16           # Outer popup margin
PADDING = 8           # Inner element padding
LINE_EXTRA = 4        # Extra vertical gap between text lines
SCROLLBAR_WIDTH = 12  # Width of scrollbar track

# ---------------------------------------------------------------------------
# Cached Font Helper
# ---------------------------------------------------------------------------

_font_cache: dict = {}


def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    """Return a cached pygame SysFont.  Avoids recreating fonts on every draw call."""
    key = (size, bold)
    if key not in _font_cache:
        _font_cache[key] = pygame.font.SysFont(None, size, bold=bold)
    return _font_cache[key]


# ---------------------------------------------------------------------------
# ScrollBar Widget
# ---------------------------------------------------------------------------

class ScrollBar:
    """
    A visible, draggable vertical scrollbar for pygame surfaces.

    Coordinate system: all (x, y) values are *surface-local* — relative to the
    surface passed to draw().  When the popup is blitted onto the main screen at
    an offset, pass that offset as ``surface_offset`` to ``handle_event()`` so
    that raw screen-space mouse positions are correctly translated.

    Usage example::

        # Create once (outside the draw loop)
        scrollbar = ScrollBar(x=popup_width - SCROLLBAR_WIDTH - 2,
                              y=content_start_y,
                              height=viewport_height)

        # In draw function
        scrollbar.draw(popup_surface, scroll_y, content_height, viewport_height)

        # In event loop
        scroll_y = scrollbar.handle_event(event, scroll_y, max_scroll,
                                          surface_offset=popup_rect.topleft)
    """

    _MIN_THUMB_SIZE = 20  # Minimum thumb height in pixels

    def __init__(self, x: int, y: int, height: int):
        self.x = x
        self.y = y
        self.height = height
        self._dragging = False
        self._drag_start_mouse_y = 0
        self._drag_start_scroll_y = 0
        self._last_scroll_y = 0
        self._last_content_height = 1
        self._last_viewport_height = 1

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _thumb_rect(self, scroll_y: int, content_height: int, viewport_height: int) -> pygame.Rect:
        """Calculate the thumb rect in surface-local coordinates."""
        if content_height <= viewport_height:
            # Content fits; thumb fills the full track
            return pygame.Rect(self.x, self.y, SCROLLBAR_WIDTH, self.height)

        ratio = viewport_height / content_height
        thumb_h = max(self._MIN_THUMB_SIZE, int(self.height * ratio))
        scroll_ratio = scroll_y / max(1, content_height - viewport_height)
        thumb_y = self.y + int((self.height - thumb_h) * scroll_ratio)
        return pygame.Rect(self.x, thumb_y, SCROLLBAR_WIDTH, thumb_h)

    def _is_scrollable(self, content_height: int, viewport_height: int) -> bool:
        return content_height > viewport_height

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, scroll_y: int,
             content_height: int, viewport_height: int) -> None:
        """Draw the scrollbar track and thumb onto *surface*."""
        # Cache for use in handle_event
        self._last_scroll_y = scroll_y
        self._last_content_height = content_height
        self._last_viewport_height = viewport_height

        if not self._is_scrollable(content_height, viewport_height):
            return  # Nothing to scroll; hide scrollbar

        # Track
        track_rect = pygame.Rect(self.x, self.y, SCROLLBAR_WIDTH, self.height)
        pygame.draw.rect(surface, THEME_SCROLLBAR_TRACK, track_rect)
        pygame.draw.rect(surface, THEME_SEPARATOR, track_rect, 1)

        # Thumb — use hover colour if dragging or mouse is over it
        thumb = self._thumb_rect(scroll_y, content_height, viewport_height)
        mouse_local = self._mouse_local((0, 0))  # will be updated in handle_event
        is_hover = self._dragging or thumb.collidepoint(self._last_local_mouse)
        colour = THEME_SCROLLBAR_THUMB_HOVER if is_hover else THEME_SCROLLBAR_THUMB
        pygame.draw.rect(surface, colour, thumb)

    def hit_test(self, mouse_pos: tuple, surface_offset: tuple = (0, 0)) -> bool:
        """Return True if the given screen-space mouse position hits the track or thumb."""
        lx = mouse_pos[0] - surface_offset[0]
        ly = mouse_pos[1] - surface_offset[1]
        track_rect = pygame.Rect(self.x, self.y, SCROLLBAR_WIDTH, self.height)
        thumb = self._thumb_rect(self._last_scroll_y, self._last_content_height, self._last_viewport_height)
        return track_rect.collidepoint(lx, ly) or thumb.collidepoint(lx, ly)

    def _mouse_local(self, surface_offset: tuple) -> tuple:
        mx, my = pygame.mouse.get_pos()
        return (mx - surface_offset[0], my - surface_offset[1])

    # Keep track of last local mouse position for hover effect in draw()
    _last_local_mouse: tuple = (-1, -1)

    def handle_event(self, event: pygame.event.Event, scroll_y: int,
                     max_scroll: int, surface_offset: tuple = (0, 0)) -> int:
        """
        Process a pygame event and return the updated scroll_y value
        (clamped to [0, max_scroll]).

        Parameters
        ----------
        event          : pygame event to process
        scroll_y       : current scroll position in pixels
        max_scroll     : maximum allowed scroll_y
        surface_offset : (left, top) of the popup surface on screen; used to
                         translate screen mouse coords to surface-local coords
        """
        # Keep last local mouse for hover colouring in draw()
        lx, ly = self._mouse_local(surface_offset)
        ScrollBar._last_local_mouse = (lx, ly)

        content_h = self._last_content_height
        viewport_h = self._last_viewport_height

        if not self._is_scrollable(content_h, viewport_h):
            return scroll_y

        if event.type == pygame.MOUSEWHEEL:
            scroll_y -= event.y * 20
            return max(0, min(scroll_y, max_scroll))

        thumb = self._thumb_rect(scroll_y, content_h, viewport_h)
        track_rect = pygame.Rect(self.x, self.y, SCROLLBAR_WIDTH, self.height)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if thumb.collidepoint(lx, ly):
                # Start drag
                self._dragging = True
                self._drag_start_mouse_y = ly
                self._drag_start_scroll_y = scroll_y
            elif track_rect.collidepoint(lx, ly):
                # Click on track above/below thumb — jump to position
                click_ratio = (ly - self.y) / max(1, self.height)
                scroll_y = int(click_ratio * max_scroll)
                return max(0, min(scroll_y, max_scroll))

        elif event.type == pygame.MOUSEMOTION and self._dragging:
            delta_y = ly - self._drag_start_mouse_y
            track_range = self.height - thumb.height
            if track_range > 0:
                scroll_delta = delta_y * max_scroll / track_range
                scroll_y = self._drag_start_scroll_y + int(scroll_delta)
            return max(0, min(scroll_y, max_scroll))

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging = False

        return max(0, min(scroll_y, max_scroll))
