"""
StemDeck case - generates printable STL files.

    python3 build_case.py

Needs only numpy. Writes these into stl/ next to this file:

    base.stl          open box: Pi 5 mount, vents and port openings
    top_panel.stl     the lid: screen recess, encoders and buttons; clips
                      onto the base (prints face down)
    tempo_knob.stl    print 1
    jog_knob.stl      print 1, the big one

Every measurement lives in the SETTINGS section below. Change a number,
run the script again, and re-slice. Units are millimetres.

How the geometry is made: every part is built from flat outlines
(polygons, optionally with holes) pushed straight up into solids, which
is all a box with holes needs. The outlines are cut into thin
trapezoids for the top and bottom faces, so no CAD library is needed.
Parts made of several pieces overlap slightly; slicers merge them.
"""

import math
import struct
from pathlib import Path

import numpy as np

# =====================================================================
# SETTINGS
# =====================================================================

# --- Overall box -----------------------------------------------------

CASE_W = 176.0        # left to right
CASE_D = 174.0        # front to back
CASE_H = 50.0         # base height, floor bottom to wall top
WALL = 2.4            # wall thickness
FLOOR = 2.4           # floor thickness
PANEL = 2.5           # top panel thickness. EC11 bushings are short,
                      # so keep this at 2.5 or less for the nut to bite.

# --- Screen: Raspberry Pi Touch Display 2, 5 inch ----------------------
#
# The screen drops into a recess in the lid, glass up, and rests on four
# small corner shelves under it. Its back (the board and standoffs)
# hangs into the box. Only the ribbon and the power wires go down to the
# Pi, which has its own place on the floor.
# Official size: 143.5 x 91.5 mm, 16 mm deep, viewing area 111.5 x 63.

SCREEN_W = 143.5      # outline, left to right
SCREEN_D = 91.5       # outline, front to back
SCREEN_FIT = 1.5      # gap round the screen in its recess, each side
SCREEN_Y = 72.0       # front edge of the recess, from case front
SCREEN_SINK = 5.5     # how far the screen sits down into the lid; the
                      # glass part is about 6.6 mm thick, so it stands
                      # about 1 mm proud
RECESS_WALL = 2.0     # walls of the recess, under the lid
CORNER_SHELF = 14.0   # the corner shelves the screen rests on (each leg)
SHELF_THICK = 1.6

# --- Controls ------------------------------------------------------------
#
# Seen from above, front edge at the bottom:
#
#   +--------------------------------------------+
#   |                                            |
#   |               screen (landscape)           |
#   |                                            |
#   |  [VOCALS] [DRUMS] [INSTR]          (TEMPO) |
#   |                                            |
#   |  [PLAY]                  (( JOG ))         |
#   +--------------------------------------------+
#
# Positions are the centre of each hole, measured from the case's front
# left corner.

ENCODER_HOLE = 8.5    # the EC11's threaded neck is M7, so 0.75 mm spare all
                      # round, while its own nut (about 9.5 mm across) still
                      # clamps on the lid. Bigger needs a washer: see
                      # WASHER_OD below and build_washer().
ENCODERS = {"tempo": (150.0, 52.0), "jog": (120.0, 25.0)}

BUTTON_HOLE = 16.5    # the module's own cap pokes through: 11.2 mm top,
                      # 12.5 mm collar, so 2 mm spare all round
BUTTONS = {
    "play": (28.0, 19.0),
    "vocals": (30.0, 48.0),
    "drums": (62.0, 48.0),
    "instrumental": (94.0, 48.0),
}

# --- EC11 encoder modules ("Rotary Encoder Module for Arduino") ---------
# Both encoders are the same module: an EC11 on a small round blue board,
# five pins (GND, S1, S2, KEY, 5V) pointing down along one edge, a long
# M7 threaded neck and a knurled 6 mm shaft split down the middle. The
# nut on the neck clamps it to the lid. Two rails
# under the lid, either side of the board, stop it twisting when the knob
# turns. They leave room for boards up to 28 mm across; a smaller board
# just has some play, which the nut takes up. The pins go left-right:
# tempo's to the left, jog's to the right.

ENC_BOARD_W = 28.0    # widest board the rails take
ENC_RAIL = 1.6        # rail thickness
ENC_RAIL_DEPTH = 10.0 # how far the rails hang below the lid; the board
                      # sits about 8 mm down, under the encoder's body
# How far the rails run left and right of each encoder's centre.
ENC_RAILS = {"tempo": (-12.0, 12.0), "jog": (-9.0, 12.0)}

# --- DFRobot DFR0029 button modules (Digital Push Button V2) -------------
# A black 22 x 30 mm board with a 12 mm switch under a big yellow cap
# (11.2 mm across the top, a 12.5 mm collar, 12 mm tall from the board)
# and a white side-entry plug at one end, about 5 mm tall, with the cable
# coming straight out of the end. The switch sits 3.2 mm off the middle
# of the board, away from the plug.
#
# The yellow cap pokes up through the lid by itself - no printed cap. An
# open frame under each hole holds the board; push it up until the cap
# stands proud as far as you like (about 3 mm puts the board 6.5 mm under
# the lid, and the plug still clears it) and hot glue the board's edges
# to the frame. A gap in the end wall lets the cable out.

MODULE_W = 22.0       # board size
MODULE_L = 30.0
SWITCH_OFFSET = 3.2   # switch centre from board centre, away from the plug
MODULE_FIT = 1.0      # gap around the board, each side
MODULE_WALL = 1.6
MODULE_DEPTH = 10.0   # how far the frame hangs below the panel
MODULE_GAP = 12.0     # width of the cable gap, for the plug and its wires
# Which way each board's long side runs, with the plug at the far end:
# "x" plug to the right, "y" plug to the back. Play lies sideways so it
# clears the vocals board above it.
MODULE_ALONG = {"play": "x", "vocals": "y", "drums": "y", "instrumental": "y"}

# --- Panel fixing ----------------------------------------------------------

# --- Clip-on lid ------------------------------------------------------------
#
# The lid has a lip all round its underside that fits just inside the
# base's walls. Small bumps on the lip click under matching ridges on
# the inside of the walls. No screws. To open it, lift at the finger
# notch in the front wall.

LIP_FIT = 0.4         # gap between the panel's locating lip and walls
LIP_THICK = 1.4       # thin enough to flex as it clips in
LIP_DEPTH = 10.0      # how far the lip reaches down inside the walls
SNAP = 0.5            # how far each ridge and bump sticks out
SNAP_Z = 6.5          # ridge height below the top of the walls
# Where the ridges run along each wall (they skip the port openings).
SNAPS = {
    "front": (30.0, CASE_W - 30.0),
    "back": (14.0, CASE_W - 14.0),
    "left": (14.0, 96.0),
    "right": (30.0, CASE_D - 30.0),
}
FINGER_NOTCH = (24.0, 3.0)   # width and depth, top of the front wall

# --- Raspberry Pi 5 on the floor ------------------------------------------
#
# Under the screen, at the back left, turned so the USB-C and HDMI ports
# face the back wall, USB-A and Ethernet face the left wall, and the GPIO
# header faces the front, towards the buttons and encoders.

PI_W = 85.0           # board, left to right (USB end on the left)
PI_D = 56.0           # board, front to back
PI_X = 12.0           # board's left edge, from the case's left edge
PI_Y = 106.0          # board's front edge, from the case front
PI_STANDOFF = 5.0     # height of the posts under the board
PI_POST_D = 6.0
PI_PILOT = 2.2        # for the M2.5 screws that came with the display
# Mounting holes, measured from the board's corner at the end away from
# the USB ports.
PI_HOLES = ((3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5))

# --- Port openings (open at the top, so no bridging when printing) -------

NOTCH_BOTTOM = FLOOR + PI_STANDOFF - 0.5    # just under the board
# The back wall is closed except a small window for the USB-C power
# plug. (The micro HDMI ports beside it are not used, so stay covered.)
POWER_HOLE_X = PI_X + PI_W - 11.2     # centre, lined up with the USB-C port
POWER_HOLE_W = 16.0
POWER_HOLE_Z = (FLOOR + PI_STANDOFF, FLOOR + PI_STANDOFF + 11.0)
LEFT_NOTCH_Y = (PI_Y - 2.0, PI_Y + PI_D + 2.0)    # USB-A, Ethernet

# --- Vents under the Pi ------------------------------------------------------

VENT_Y = (PI_Y + 8.0, PI_Y + PI_D - 8.0)
VENT_X = (PI_X + 10.0, PI_X + PI_W - 10.0)
VENT_SLOT = 3.0
VENT_PITCH = 8.0

# --- Knobs (EC11 knurled, split 6 mm shaft) ----------------------------------

# name: (diameter, height, flutes)
KNOBS = {
    "tempo": (18.0, 13.0, 18),
    "jog": (38.0, 12.0, 40),
}
# Each knob's shaft hole is this deep and closed at the top, so the knob
# bottoms out on the end of the shaft and rides about 4 mm above the nut
# instead of resting on the lid. (The EC11's shaft stands about 17 mm
# above the lid: 4.5 mm of threaded neck, then the knurled part.)
KNOB_BORE = 9.0
SHAFT_D = 6.0         # round hole that presses onto the knurled, split
                      # 6 mm shaft (printed holes come out a little small,
                      # which makes it grip). Loose? Try 5.8. Too tight? 6.2.
JOG_DIMPLE = 7.0      # finger dimple near the jog wheel's edge

# --- Encoder washer (not printed by default) -----------------------------
# Only needed if ENCODER_HOLE is made bigger than the nut. To print one,
# add "encoder_washer": build_washer() to build_all().

WASHER_OD = 21.0
WASHER_ID = 7.4
WASHER_T = 1.5

CIRCLE_SEGMENTS = 64

# =====================================================================
# GEOMETRY
# =====================================================================


def circle(cx, cy, r, n=CIRCLE_SEGMENTS):
    return [(cx + r * math.cos(2 * math.pi * i / n),
             cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def rounded_rect(x0, y0, x1, y1, r, n=8):
    pts = []
    corners = [(x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0),
               (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)]

    for cx, cy, start in corners:
        for i in range(n + 1):
            a = math.radians(start + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))

    return pts


def signed_area(loop):
    return 0.5 * sum(loop[i][0] * loop[(i + 1) % len(loop)][1]
                     - loop[(i + 1) % len(loop)][0] * loop[i][1]
                     for i in range(len(loop)))


def oriented(loop, ccw):
    return list(loop) if (signed_area(loop) > 0) == ccw else list(loop)[::-1]


def edge_y(edge, x):
    (x0, y0), (x1, y1) = edge

    if x == x0:
        return y0

    if x == x1:
        return y1

    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def extrude(loops, height):
    """Solid from an outline (loops[0]) with holes (loops[1:]).

    Returns triangles of shape (n, 3, 3) in local (u, v, w) coordinates,
    w from 0 to height, outward-facing.
    """
    # Snap to a fine grid so that points meant to line up do so exactly.
    loops = [[(round(x, 6), round(y, 6)) for x, y in loop] for loop in loops]
    loops = [oriented(l, ccw=(i == 0)) for i, l in enumerate(loops)]

    edges = []

    for loop in loops:
        for i in range(len(loop)):
            edges.append((loop[i], loop[(i + 1) % len(loop)]))

    # Every vertex x becomes a cut line. Between two cuts each edge
    # either spans the whole strip or misses it, so the inside of the
    # strip is a stack of trapezoids, one per pair of edges.
    cuts = sorted({p[0] for loop in loops for p in loop})
    cells = []

    for xa, xb in zip(cuts, cuts[1:]):
        xm = 0.5 * (xa + xb)
        active = [e for e in edges
                  if min(e[0][0], e[1][0]) <= xa
                  and max(e[0][0], e[1][0]) >= xb
                  and e[0][0] != e[1][0]]
        active.sort(key=lambda e: edge_y(e, xm))

        for lower, upper in zip(active[0::2], active[1::2]):
            cells.append((xa, xb, lower, upper))

    # Every point that lies on each cut line: cell corners and vertices.
    # Cell sides and upright walls are split at all of them, so no face
    # has a vertex sitting in the middle of a neighbour's edge.
    on_cut = {x: set() for x in cuts}

    for loop in loops:
        for x, y in loop:
            on_cut[x].add(y)

    for xa, xb, lower, upper in cells:
        for x in (xa, xb):
            on_cut[x].add(edge_y(lower, x))
            on_cut[x].add(edge_y(upper, x))

    on_cut = {x: sorted(ys) for x, ys in on_cut.items()}

    def between(x, y0, y1):
        lo, hi = min(y0, y1), max(y0, y1)
        ys = [y for y in on_cut[x] if lo < y < hi]
        return ys if y0 <= y1 else ys[::-1]

    tris = []

    # Top and bottom faces: each cell becomes a fan round its centre,
    # which handles the extra points along its sides.
    for xa, xb, lower, upper in cells:
        ya0, ya1 = edge_y(lower, xa), edge_y(lower, xb)
        yb0, yb1 = edge_y(upper, xa), edge_y(upper, xb)

        ring = [(xa, ya0), (xb, ya1)]
        ring += [(xb, y) for y in between(xb, ya1, yb1)]
        ring += [(xb, yb1), (xa, yb0)]
        ring += [(xa, y) for y in between(xa, yb0, ya0)]

        # Drop repeats where the two edges meet at a point.
        clean = []

        for p in ring:
            if not clean or p != clean[-1]:
                clean.append(p)

        if len(clean) > 1 and clean[0] == clean[-1]:
            clean.pop()

        cx = sum(p[0] for p in clean) / len(clean)
        cy = sum(p[1] for p in clean) / len(clean)

        for p, q in zip(clean, clean[1:] + clean[:1]):
            area = (p[0] - cx) * (q[1] - cy) - (q[0] - cx) * (p[1] - cy)

            if area > 1e-12:
                tris.append(((cx, cy, height), (p[0], p[1], height),
                             (q[0], q[1], height)))
                tris.append(((cx, cy, 0.0), (q[0], q[1], 0.0),
                             (p[0], p[1], 0.0)))

    # Side walls.
    for edge in edges:
        (x0, y0), (x1, y1) = edge

        if x0 == x1:
            inner = [(x0, y) for y in between(x0, y0, y1)]
        else:
            lo, hi = min(x0, x1), max(x0, x1)
            xs = [c for c in cuts if lo < c < hi]

            if x1 < x0:
                xs = xs[::-1]

            inner = [(c, edge_y(edge, c)) for c in xs]

        pts = [edge[0]] + inner + [edge[1]]

        for a, b in zip(pts, pts[1:]):
            a0, b0 = (a[0], a[1], 0.0), (b[0], b[1], 0.0)
            a1, b1 = (a[0], a[1], height), (b[0], b[1], height)
            tris.append((a0, b0, b1))
            tris.append((a0, b1, a1))

    return np.array(tris, dtype=float)


def place(tris, matrix=None, offset=(0, 0, 0)):
    m = np.eye(3) if matrix is None else np.array(matrix, dtype=float)
    out = tris @ m.T + np.array(offset, dtype=float)

    # A mirroring transform turns every triangle inside out.
    if np.linalg.det(m) < 0:
        out = out[:, ::-1, :]

    return out


def prism(loops, z0, z1):
    return place(extrude(loops, z1 - z0), offset=(0, 0, z0))


def box(x0, y0, z0, x1, y1, z1):
    return prism([rect(x0, y0, x1, y1)], z0, z1)


# Wall profiles are drawn in (along, up) and extruded through the wall.
XZ_WALL = [[1, 0, 0], [0, 0, 1], [0, 1, 0]]     # u->x, v->z, w->y
YZ_WALL = [[0, 0, 1], [1, 0, 0], [0, 1, 0]]     # u->y, v->z, w->x


# =====================================================================
# PARTS
# =====================================================================


def screen_centre():
    pocket_d = SCREEN_D + 2 * SCREEN_FIT
    return CASE_W / 2, SCREEN_Y + pocket_d / 2


def build_base():
    parts = []
    W, D, H = CASE_W, CASE_D, CASE_H

    # Floor, with vent slots under the Pi.
    vents = []
    x = VENT_X[0]

    while x + VENT_SLOT <= VENT_X[1] + 1e-9:
        vents.append(rounded_rect(x, VENT_Y[0], x + VENT_SLOT, VENT_Y[1],
                                  VENT_SLOT / 2 - 0.01, n=4))
        x += VENT_PITCH

    parts.append(prism([rect(0, 0, W, D)] + vents, 0, FLOOR))

    # Front wall: a finger notch in the top edge, to lift the lid.
    fw, fd = FINGER_NOTCH
    front = [(0, 0), (W, 0), (W, H), (W / 2 + fw / 2, H),
             (W / 2 + fw / 2 - fd, H - fd), (W / 2 - fw / 2 + fd, H - fd),
             (W / 2 - fw / 2, H), (0, H)]
    parts.append(place(extrude([front], WALL), XZ_WALL, (0, 0, 0)))

    # Back wall: closed, with a window for the USB-C power plug. The
    # window's top is a short bridge, which prints fine without support.
    hx0 = POWER_HOLE_X - POWER_HOLE_W / 2
    hx1 = POWER_HOLE_X + POWER_HOLE_W / 2
    hz0, hz1 = POWER_HOLE_Z
    parts.append(place(extrude([rect(0, 0, W, H), rect(hx0, hz0, hx1, hz1)], WALL),
                       XZ_WALL, (0, D - WALL, 0)))

    # Left wall: notch for USB-A and Ethernet. Right wall: plain.
    s0, s1 = LEFT_NOTCH_Y
    left = [(0, 0), (D, 0), (D, H), (s1, H), (s1, NOTCH_BOTTOM),
            (s0, NOTCH_BOTTOM), (s0, H), (0, H)]
    parts.append(place(extrude([left], WALL), YZ_WALL, (0, 0, 0)))
    parts.append(place(extrude([rect(0, 0, D, H)], WALL), YZ_WALL, (W - WALL, 0, 0)))

    # Ridges on the inside of the walls that the lid's bumps clip under.
    # Sloped top and bottom, so they print without supports and the lid
    # slides over them.
    zr = H - SNAP_Z
    ridge = [(WALL - 0.2, zr - 1.0), (WALL + SNAP, zr - 0.3),
             (WALL + SNAP, zr + 0.2), (WALL - 0.2, zr + 0.9)]

    for side, (a0, a1) in SNAPS.items():
        parts.append(wall_strip(side, ridge, a0, a1))

    # Posts for the Pi. Its USB end is on the left, so the holes are
    # measured from the right-hand end of the board.
    for hx, hy in pi_holes():
        parts.append(prism([circle(hx, hy, PI_POST_D / 2, 32),
                            circle(hx, hy, PI_PILOT / 2, 24)],
                           FLOOR - 0.2, FLOOR + PI_STANDOFF))

    return np.concatenate(parts)


def wall_strip(side, profile, a0, a1):
    """A strip along the inside of one wall, from a0 to a1 along it.

    profile is drawn as (distance in from the outside face, height).
    """
    W, D = CASE_W, CASE_D

    if side in ("front", "back"):
        pts = [(d if side == "front" else D - d, z) for d, z in profile]
        return place(extrude([pts], a1 - a0), YZ_WALL, (a0, 0, 0))

    pts = [(d if side == "left" else W - d, z) for d, z in profile]
    return place(extrude([pts], a1 - a0), XZ_WALL, (0, a0, 0))


def pi_holes():
    right = PI_X + PI_W
    return [(right - dx, PI_Y + dy) for dx, dy in PI_HOLES]


def build_panel():
    """Built in place on top of the base, then flipped for printing."""
    parts = []
    W, D, H = CASE_W, CASE_D, CASE_H
    top = H + PANEL

    sx, sy = screen_centre()
    pocket_w = SCREEN_W + 2 * SCREEN_FIT
    pocket_d = SCREEN_D + 2 * SCREEN_FIT
    px0, px1 = sx - pocket_w / 2, sx + pocket_w / 2
    py0, py1 = sy - pocket_d / 2, sy + pocket_d / 2

    holes = [rect(px0, py0, px1, py1)]
    holes += [circle(x, y, ENCODER_HOLE / 2) for x, y in ENCODERS.values()]
    holes += [circle(x, y, BUTTON_HOLE / 2) for x, y in BUTTONS.values()]

    parts.append(prism([rect(0, 0, W, D)] + holes, H, top))

    # The screen recess: walls hanging under the opening, with a shelf in
    # each corner for the screen to rest on. The shelves span the corner
    # between two walls, so they print as short bridges.
    shelf_top = top - SCREEN_SINK
    z0 = shelf_top - SHELF_THICK
    t = RECESS_WALL
    parts.append(prism([rect(px0 - t, py0 - t, px1 + t, py1 + t),
                        rect(px0, py0, px1, py1)], z0, H + 0.5))

    c = CORNER_SHELF
    for (cx, cy, dx, dy) in ((px0, py0, 1, 1), (px1, py0, -1, 1),
                             (px0, py1, 1, -1), (px1, py1, -1, -1)):
        tri = [(cx - dx * 0.5, cy - dy * 0.5), (cx + dx * c, cy - dy * 0.5),
               (cx - dx * 0.5, cy + dy * c)]
        parts.append(prism([tri], z0, shelf_top))

    # Rails that stop the encoder boards twisting.
    for name, (ex, ey) in ENCODERS.items():
        r0, r1 = ENC_RAILS[name]
        half = ENC_BOARD_W / 2 + 0.3
        for y0 in (ey - half - ENC_RAIL, ey + half):
            parts.append(box(ex + r0, y0, H - ENC_RAIL_DEPTH,
                             ex + r1, y0 + ENC_RAIL, H + 0.5))

    # Frames that locate the button modules.
    for name, (bx, by) in BUTTONS.items():
        parts.append(module_frame(name, bx, by, H))

    # Lip just inside the walls, stopping short of the corners so each
    # side can flex on its own as it clips in.
    a = WALL + LIP_FIT
    b = a + LIP_THICK
    stop = WALL + 6.0
    z0, z1 = H - LIP_DEPTH, H + 0.5

    parts.append(box(stop, a, z0, W - stop, b, z1))
    parts.append(box(stop, D - b, z0, W - stop, D - a, z1))
    parts.append(box(a, stop, z0, b, D - stop, z1))
    parts.append(box(W - b, stop, z0, W - a, D - stop, z1))

    # Bumps on the outside of the lip that click under the base's
    # ridges, a little shorter than the ridges at each end.
    zb = H - SNAP_Z - 1.2
    bump = [(a + 0.2, zb - 1.6), (a - SNAP, zb - 0.9),
            (a - SNAP, zb), (a + 0.2, zb + 0.7)]

    for side, (a0, a1) in SNAPS.items():
        parts.append(wall_strip(side, bump, a0 + 3.0, a1 - 3.0))

    return np.concatenate(parts)


def module_frame(name, cx, cy, panel_bottom):
    """Open frame round a button module, with a gap for its cable.

    (cx, cy) is the button hole. The board's middle is SWITCH_OFFSET
    further towards the plug end, and the gap is in that end wall.
    """
    along_x = MODULE_ALONG[name] == "x"
    w, l = MODULE_W + 2 * MODULE_FIT, MODULE_L + 2 * MODULE_FIT

    if along_x:
        w, l = l, w
        cx += SWITCH_OFFSET
    else:
        cy += SWITCH_OFFSET

    t = MODULE_WALL
    x0, x1 = cx - w / 2 - t, cx + w / 2 + t
    y0, y1 = cy - l / 2 - t, cy + l / 2 + t
    z0, z1 = panel_bottom - MODULE_DEPTH, panel_bottom + 0.5

    walls = [
        box(x0, y0, z0, x1, y0 + t, z1),                 # front
        box(x0, y0, z0, x0 + t, y1, z1),                 # left
    ]

    if along_x:
        # Plug end on the right: gap in the right-hand wall.
        g0, g1 = cy - MODULE_GAP / 2, cy + MODULE_GAP / 2
        walls += [box(x0, y1 - t, z0, x1, y1, z1),       # back
                  box(x1 - t, y0, z0, x1, g0, z1),
                  box(x1 - t, g1, z0, x1, y1, z1)]
    else:
        # Plug end at the back: gap in the back wall.
        g0, g1 = cx - MODULE_GAP / 2, cx + MODULE_GAP / 2
        walls += [box(x1 - t, y0, z0, x1, y1, z1),       # right
                  box(x0, y1 - t, z0, g0, y1, z1),
                  box(g1, y1 - t, z0, x1, y1, z1)]

    return np.concatenate(walls)


def panel_for_printing(panel):
    # Turn it over, 180 degrees about the left-to-right axis, so the
    # visible face lies flat on the bed.
    top = CASE_H + PANEL
    rot = [[1, 0, 0], [0, -1, 0], [0, 0, -1]]
    return place(panel, rot, (0, CASE_D, top))


def knob_outline(diameter, flutes):
    r = diameter / 2
    pts = []
    n = flutes * 8
    depth = 0.7 if diameter < 30 else 1.0

    for i in range(n):
        a = 2 * math.pi * i / n
        rr = r - depth * (1 - math.cos(flutes * a)) / 2

        # A deeper groove marks where the knob points.
        if abs(math.remainder(a - math.pi / 2, 2 * math.pi)) < math.radians(4):
            rr = r - 2.2

        pts.append((rr * math.cos(a), rr * math.sin(a)))

    return pts


def build_knob(name):
    # Printed top-down: solid top on the bed, shaft hole facing up.
    diameter, height, flutes = KNOBS[name]
    outline = knob_outline(diameter, flutes)
    shaft = circle(0, 0, SHAFT_D / 2, 48)

    top_t = height - KNOB_BORE           # solid top above the shaft hole

    if name != "jog":
        cap = prism([outline], 0, top_t + 0.3)
        body = prism([outline, shaft], top_t, height)
        return np.concatenate([cap, body])

    # The jog wheel: a shallow finger dimple near the edge (printed as a
    # recess in the top face, which is on the bed), a solid top, then a
    # hub round the shaft and a ring round the rim, so it is not a solid
    # puck of plastic.
    r = diameter / 2
    dimple = circle(0, -(r - JOG_DIMPLE / 2 - 4.0), JOG_DIMPLE / 2, 32)
    face = prism([outline, dimple], 0, 1.2)
    top = prism([outline], 1.0, top_t + 0.3)
    hub = prism([circle(0, 0, 6.0, 48), shaft], top_t, height)
    rim = prism([outline, circle(0, 0, r - 2.6, 96)], top_t, height)
    spokes = [box(-1.2, 5.5, top_t, 1.2, r - 2.2, height - 2.0)]
    spokes.append(place(spokes[0], [[0, -1, 0], [1, 0, 0], [0, 0, 1]]))
    spokes.append(place(spokes[0], [[-1, 0, 0], [0, -1, 0], [0, 0, 1]]))
    spokes.append(place(spokes[0], [[0, 1, 0], [-1, 0, 0], [0, 0, 1]]))
    return np.concatenate([face, top, hub, rim] + spokes)


def build_washer():
    return prism([circle(0, 0, WASHER_OD / 2), circle(0, 0, WASHER_ID / 2, 48)],
                 0, WASHER_T)


# =====================================================================
# OUTPUT
# =====================================================================


def write_stl(path, tris):
    tris = np.asarray(tris, dtype=np.float32)
    normals = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    normals = normals / np.where(lengths == 0, 1, lengths)

    with open(path, "wb") as f:
        f.write(b"StemDeck case".ljust(80, b" "))
        f.write(struct.pack("<I", len(tris)))

        for n, t in zip(normals, tris):
            f.write(struct.pack("<12fH", *n, *t[0], *t[1], *t[2], 0))


def build_all():
    return {
        "base": build_base(),
        "top_panel": panel_for_printing(build_panel()),
        "tempo_knob": build_knob("tempo"),
        "jog_knob": build_knob("jog"),
    }


def main():
    out = Path(__file__).resolve().parent / "stl"
    out.mkdir(exist_ok=True)

    for name, tris in build_all().items():
        path = out / f"{name}.stl"
        write_stl(path, tris)
        size = tris.reshape(-1, 3).max(axis=0) - tris.reshape(-1, 3).min(axis=0)
        print(f"{path.name:16} {len(tris):7} triangles   "
              f"{size[0]:6.1f} x {size[1]:6.1f} x {size[2]:5.1f} mm")


if __name__ == "__main__":
    main()
