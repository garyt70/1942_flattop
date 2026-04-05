"""
One-time script to generate retro wargame-style PNG overlay assets for
piece_image_factory.py.  Run from repo root with the venv activated.

All overlays are 64x64, white line-art on transparent background.
They are blitted on top of procedurally-drawn colored base shapes at runtime.
"""
import os
import sys

import pygame

pygame.init()
# Need a display surface only to allow image.save; use off-screen
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
pygame.display.set_mode((1, 1))

SIZE = 64
WHITE = (255, 255, 255, 255)
TRANSPARENT = (0, 0, 0, 0)
OUT_DIR = os.path.join(os.path.dirname(__file__), "flattop", "ui", "desktop", "assets")
os.makedirs(OUT_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# AirFormation overlay — 3 WWII top-down plane silhouettes in V-formation
# ---------------------------------------------------------------------------
def make_airformation_overlay() -> pygame.Surface:
    surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    surf.fill(TRANSPARENT)

    def draw_plane(cx, cy, sc=1.0):
        """WWII top-down plane silhouette pointing upward at (cx, cy), scale sc."""
        def s(v):
            return max(1, int(round(v * sc)))

        # --- fuselage: 6-point tapered body ---
        fl = s(8)   # half length (nose to tail)
        fw = s(2)   # half width at widest
        fuselage = [
            (cx,        cy - fl),           # nose tip
            (cx + fw,   cy - fl + s(4)),    # port shoulder
            (cx + fw,   cy + fl - s(4)),    # port hip
            (cx,        cy + fl),           # tail tip
            (cx - fw,   cy + fl - s(4)),    # starboard hip
            (cx - fw,   cy - fl + s(4)),    # starboard shoulder
        ]
        pygame.draw.polygon(surf, WHITE, fuselage)

        # --- main wings: wide, slightly swept ---
        wy = cy - s(1)          # wing root centre Y
        wspan = s(11)           # half wingspan
        sweep = s(2)            # trailing edge sweep
        wroot = s(3)            # root half-chord
        wtip  = s(2)            # tip half-chord

        left_wing = [
            (cx - fw,    wy - wroot),               # inner LE
            (cx - wspan, wy - wtip  + sweep),       # outer LE
            (cx - wspan, wy + wtip  + sweep),       # outer TE
            (cx - fw,    wy + wroot),               # inner TE
        ]
        right_wing = [
            (cx + fw,    wy - wroot),
            (cx + wspan, wy - wtip  + sweep),
            (cx + wspan, wy + wtip  + sweep),
            (cx + fw,    wy + wroot),
        ]
        pygame.draw.polygon(surf, WHITE, left_wing)
        pygame.draw.polygon(surf, WHITE, right_wing)

        # --- horizontal tail stabilizers ---
        ty     = cy + fl - s(3)
        tspan  = s(5)
        tchord = s(2)
        left_tail = [
            (cx - fw,    ty),
            (cx - tspan, ty + tchord),
            (cx - tspan, ty + tchord * 2),
            (cx - fw,    ty + tchord),
        ]
        right_tail = [
            (cx + fw,    ty),
            (cx + tspan, ty + tchord),
            (cx + tspan, ty + tchord * 2),
            (cx + fw,    ty + tchord),
        ]
        pygame.draw.polygon(surf, WHITE, left_tail)
        pygame.draw.polygon(surf, WHITE, right_tail)

        # --- engine cowling: small filled circle at nose ---
        pygame.draw.circle(surf, WHITE, (cx, cy - fl + s(2)), s(2))

    # V-formation: lead plane centre-top, two wingmen lower-left and lower-right
    draw_plane(cx=32, cy=17, sc=1.0)   # lead
    draw_plane(cx=11, cy=46, sc=0.85)  # left wingman
    draw_plane(cx=53, cy=46, sc=0.85)  # right wingman

    return surf


# ---------------------------------------------------------------------------
# Base overlay — retro wargame naval-base anchor symbol
# ---------------------------------------------------------------------------
def make_base_overlay() -> pygame.Surface:
    surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    surf.fill(TRANSPARENT)

    cx = SIZE // 2
    # Anchor sits in the lower 2/3 of the surface to align with the triangle shape
    top_y = 10
    bot_y = SIZE - 10

    shaft_top = top_y + 8      # below the ring
    shaft_bot = bot_y - 2

    # --- ring at the top ---
    ring_cy = top_y + 4
    pygame.draw.circle(surf, WHITE, (cx, ring_cy), 5, 2)

    # --- vertical shaft ---
    pygame.draw.line(surf, WHITE, (cx, ring_cy + 5), (cx, shaft_bot), 3)

    # --- horizontal crossbar ---
    bar_y = top_y + 16
    pygame.draw.line(surf, WHITE, (cx - 14, bar_y), (cx + 14, bar_y), 3)
    # Small endcaps on the bar
    pygame.draw.circle(surf, WHITE, (cx - 14, bar_y), 2)
    pygame.draw.circle(surf, WHITE, (cx + 14, bar_y), 2)

    # --- curved anchor arms at the bottom ---
    # Classic anchor: the flukes angle outward from the bottom of the shaft
    arm_root = (cx, shaft_bot)
    left_fluke_tip = (cx - 16, shaft_bot - 10)
    right_fluke_tip = (cx + 16, shaft_bot - 10)
    pygame.draw.line(surf, WHITE, arm_root, left_fluke_tip, 3)
    pygame.draw.line(surf, WHITE, arm_root, right_fluke_tip, 3)

    # Small filled circles at fluke tips
    pygame.draw.circle(surf, WHITE, left_fluke_tip, 3)
    pygame.draw.circle(surf, WHITE, right_fluke_tip, 3)

    # Thin horizontal "stock" connecting fluke tips
    pygame.draw.line(surf, WHITE, left_fluke_tip, right_fluke_tip, 1)

    return surf


# ---------------------------------------------------------------------------
# TaskForce overlay — top-down silhouette of two warships in formation
# ---------------------------------------------------------------------------
def make_taskforce_overlay() -> pygame.Surface:
    surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    surf.fill(TRANSPARENT)

    def draw_ship(cx, cy, length, beam):
        """Draw a top-down warship hull pointing upward centred at (cx, cy)."""
        half_l = length // 2
        half_b = beam // 2

        # Hull: elongated diamond-ish shape with flattened midship sides
        # bow tip → flare out → widest beam → narrowing → stern tip
        hull = [
            (cx,             cy - half_l),              # bow tip
            (cx + half_b,    cy - half_l + length // 4),# port widest
            (cx + half_b,    cy + half_l - length // 4),# port widest lower
            (cx,             cy + half_l),              # stern tip
            (cx - half_b,    cy + half_l - length // 4),# stbd widest lower
            (cx - half_b,    cy - half_l + length // 4),# stbd widest
        ]
        pygame.draw.polygon(surf, WHITE, hull)

        # Superstructure: rect offset toward bow
        ss_w = max(4, beam // 2)
        ss_h = length // 4
        ss_x = cx - ss_w // 2
        ss_y = cy - half_l // 2 - ss_h // 2
        pygame.draw.rect(surf, (60, 60, 60, 255), (ss_x, ss_y, ss_w, ss_h))
        pygame.draw.rect(surf, WHITE, (ss_x, ss_y, ss_w, ss_h), 1)

    # Left ship: larger (cruiser) — runs nearly full height
    draw_ship(cx=20, cy=32, length=50, beam=14)

    # Right ship: smaller (destroyer) — staggered slightly forward
    draw_ship(cx=44, cy=30, length=38, beam=9)

    return surf


# ---------------------------------------------------------------------------
# Save all overlays
# ---------------------------------------------------------------------------
def main():
    assets = {
        "overlay_airformation.png": make_airformation_overlay(),
        "overlay_base.png": make_base_overlay(),
        "overlay_taskforce.png": make_taskforce_overlay(),
    }
    for filename, surface in assets.items():
        path = os.path.join(OUT_DIR, filename)
        pygame.image.save(surface, path)
        print(f"Saved {path}")

    pygame.quit()
    print("Done.")


if __name__ == "__main__":
    main()
