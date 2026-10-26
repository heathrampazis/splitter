"""
StemDeck case - generates printable STL files.

    python3 build_case.py

Needs only numpy. Writes these into stl/ next to this file:

    base.stl          open box: Pico mount, vents, port notches
    top_panel.stl     screen, knobs and buttons (prints face down)
    knob.stl          print 4
    button_cap.stl    print 3

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
CASE_H = 56.0         # base height, floor bottom to wall top
WALL = 2.4            # wall thickness
FLOOR = 2.4           # floor thickness
PANEL = 2.5           # top panel thickness. EC11 bushings are short,
                      # so keep this at 2.5 or less for the nut to bite.

# --- Screen: Raspberry Pi Touch Display 2, 5 inch ----------------------

SCREEN_W = 143.5      # glass outline, left to right
SCREEN_D = 91.5       # glass outline, front to back
SCREEN_FIT = 0.6      # gap around the glass in the pocket, each side
SCREEN_LIP = 4.0      # how far the panel overlaps the glass edge.
                      # The window stays bigger than the 111.5 x 63 mm
                      # viewing area even if that is off-centre.
SCREEN_Y = 72.0       # front edge of the screen pocket, from case front
FRAME_WALL = 2.0      # walls that locate the screen under the panel
FRAME_DEPTH = 8.0     # how far those walls hang down

# --- Controls ------------------------------------------------------------

ENCODER_HOLE = 7.4    # EC11 has an M7 bushing
ENCODER_Y = 50.0
ENCODER_X = (28.0, 68.0, 108.0, 148.0)   # vocals, drums, bass+other, tempo

BUTTON_HOLE = 13.0    # the printed cap's stem is 12.2
BUTTON_Y = 20.0
BUTTON_X = (34.0, 108.0, 148.0)          # play, search back, search fwd

# --- Panel fixing ----------------------------------------------------------

SCREW_INSET = 6.0     # corner screw centres, from the outside edges
SCREW_HOLE = 3.4      # clearance for M3 in the panel
PILOT_HOLE = 2.6      # M3 self-tapping into the base posts
POST_RADIUS = 4.0     # corner posts in the base
LIP_FIT = 0.4         # gap between the panel's locating lip and walls
LIP_THICK = 1.6
LIP_DEPTH = 3.0

# --- Port notches (open at the top, so no bridging when printing) --------
# The Pi hangs under the screen, so its ports are at the back half of the
# box. Notches are generous because the Pi's exact position depends on
# how it sits on the display's standoffs - widen them if a plug fouls.

NOTCH_BOTTOM = 8.0                       # notch floor height above z=0
BACK_NOTCH_X = (30.0, 146.0)             # back wall: USB-C power, HDMI
SIDE_NOTCH_Y = (88.0, 160.0)             # both side walls: USB-A, Ethernet

# --- Raspberry Pi Pico 2 WH mount ------------------------------------------

PICO_X = 88.0         # board centre
PICO_Y = 40.0
PICO_HOLES_X = 11.4   # hole spacing across the board
PICO_HOLES_Y = 47.0   # hole spacing along the board
PICO_STANDOFF = 4.0   # height of the pads under the board
PICO_PEG = 1.9        # pegs go through the Pico's 2.1 mm holes

# --- Vents under the Pi ------------------------------------------------------

VENT_Y = (88.0, 156.0)
VENT_X_SPAN = 100.0
VENT_SLOT = 3.0
VENT_PITCH = 8.0

# --- Knob (EC11 D shaft: 6 mm, flat leaves 4.5 mm) ---------------------------

KNOB_D = 22.0
KNOB_H = 16.0
KNOB_TOP = 3.0        # solid top
SHAFT_D = 6.15
SHAFT_FLAT = 1.6      # flat's distance from the shaft centre
KNOB_FLUTES = 20

# --- Button cap ---------------------------------------------------------

CAP_STEM_D = 12.2
CAP_PROUD = 3.0       # how far it stands above the panel
CAP_FLANGE_D = 17.0   # stops it falling out, sits on the switch
CAP_FLANGE_H = 1.6

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


def corner_points():
    s = SCREW_INSET
    return [(s, s), (CASE_W - s, s), (s, CASE_D - s), (CASE_W - s, CASE_D - s)]


def screen_centre():
    pocket_d = SCREEN_D + 2 * SCREEN_FIT
    return CASE_W / 2, SCREEN_Y + pocket_d / 2


def build_base():
    parts = []
    W, D, H = CASE_W, CASE_D, CASE_H

    # Floor, with vent slots under the Pi.
    vents = []
    x = W / 2 - VENT_X_SPAN / 2

    while x + VENT_SLOT <= W / 2 + VENT_X_SPAN / 2 + 1e-9:
        vents.append(rounded_rect(x, VENT_Y[0], x + VENT_SLOT, VENT_Y[1],
                                  VENT_SLOT / 2 - 0.01, n=4))
        x += VENT_PITCH

    parts.append(prism([rect(0, 0, W, D)] + vents, 0, FLOOR))

    # Front wall: plain.
    parts.append(place(extrude([rect(0, 0, W, H)], WALL), XZ_WALL, (0, 0, 0)))

    # Back wall: notch for the Pi's power and HDMI.
    n0, n1 = BACK_NOTCH_X
    back = [(0, 0), (W, 0), (W, H), (n1, H), (n1, NOTCH_BOTTOM),
            (n0, NOTCH_BOTTOM), (n0, H), (0, H)]
    parts.append(place(extrude([back], WALL), XZ_WALL, (0, D - WALL, 0)))

    # Side walls: notch for USB-A and Ethernet, whichever side they face.
    s0, s1 = SIDE_NOTCH_Y
    side = [(0, 0), (D, 0), (D, H), (s1, H), (s1, NOTCH_BOTTOM),
            (s0, NOTCH_BOTTOM), (s0, H), (0, H)]
    parts.append(place(extrude([side], WALL), YZ_WALL, (0, 0, 0)))
    parts.append(place(extrude([side], WALL), YZ_WALL, (W - WALL, 0, 0)))

    # Corner posts for the panel screws. They touch the walls so they
    # print as part of them.
    for cx, cy in corner_points():
        parts.append(prism([circle(cx, cy, POST_RADIUS),
                            circle(cx, cy, PILOT_HOLE / 2, 24)], 0, H))

    # Pico pads and pegs.
    for dx in (-PICO_HOLES_X / 2, PICO_HOLES_X / 2):
        for dy in (-PICO_HOLES_Y / 2, PICO_HOLES_Y / 2):
            cx, cy = PICO_X + dx, PICO_Y + dy
            top = FLOOR + PICO_STANDOFF
            parts.append(prism([circle(cx, cy, 2.5, 32)], FLOOR - 0.2, top))
            parts.append(prism([circle(cx, cy, PICO_PEG / 2, 16)],
                               top - 0.2, top + 3.0))

    return np.concatenate(parts)


def build_panel():
    """Built in place on top of the base, then flipped for printing."""
    parts = []
    W, D, H = CASE_W, CASE_D, CASE_H
    top = H + PANEL

    sx, sy = screen_centre()
    pocket_w = SCREEN_W + 2 * SCREEN_FIT
    pocket_d = SCREEN_D + 2 * SCREEN_FIT
    win_w = SCREEN_W - 2 * SCREEN_LIP
    win_d = SCREEN_D - 2 * SCREEN_LIP

    holes = [rounded_rect(sx - win_w / 2, sy - win_d / 2,
                          sx + win_w / 2, sy + win_d / 2, 3.0)]
    holes += [circle(x, ENCODER_Y, ENCODER_HOLE / 2) for x in ENCODER_X]
    holes += [circle(x, BUTTON_Y, BUTTON_HOLE / 2) for x in BUTTON_X]
    holes += [circle(x, y, SCREW_HOLE / 2, 32) for x, y in corner_points()]

    parts.append(prism([rect(0, 0, W, D)] + holes, H, top))

    # Frame that locates the screen. It reaches 0.5 mm into the panel so
    # the two merge cleanly.
    fw = FRAME_WALL
    frame_outer = rect(sx - pocket_w / 2 - fw, sy - pocket_d / 2 - fw,
                       sx + pocket_w / 2 + fw, sy + pocket_d / 2 + fw)
    frame_inner = rect(sx - pocket_w / 2, sy - pocket_d / 2,
                       sx + pocket_w / 2, sy + pocket_d / 2)
    parts.append(prism([frame_outer, frame_inner], H - FRAME_DEPTH, H + 0.5))

    # Locating lip just inside the walls, stopping short of the corner
    # posts.
    a = WALL + LIP_FIT
    b = a + LIP_THICK
    stop = SCREW_INSET + POST_RADIUS + 4.0
    z0, z1 = H - LIP_DEPTH, H + 0.5

    parts.append(box(stop, a, z0, W - stop, b, z1))
    parts.append(box(stop, D - b, z0, W - stop, D - a, z1))
    parts.append(box(a, stop, z0, b, D - stop, z1))
    parts.append(box(W - b, stop, z0, W - a, D - stop, z1))

    return np.concatenate(parts)


def panel_for_printing(panel):
    # Turn it over, 180 degrees about the left-to-right axis, so the
    # visible face lies flat on the bed.
    top = CASE_H + PANEL
    rot = [[1, 0, 0], [0, -1, 0], [0, 0, -1]]
    return place(panel, rot, (0, CASE_D, top))


def d_shaft(r, flat, n=48):
    pts = []

    for i in range(n):
        a = 2 * math.pi * i / n
        x, y = r * math.cos(a), r * math.sin(a)

        if y <= flat:
            pts.append((x, y))

    # Close the flat with its two exact end points.
    fx = math.sqrt(r * r - flat * flat)
    pts.append((-fx, flat))
    pts.append((fx, flat))

    # Sort round the centre so the loop does not cross itself.
    pts.sort(key=lambda p: math.atan2(p[1], p[0]))
    return pts


def knob_outline():
    r = KNOB_D / 2
    pts = []
    n = KNOB_FLUTES * 8

    for i in range(n):
        a = 2 * math.pi * i / n
        rr = r - 0.7 * (1 - math.cos(KNOB_FLUTES * a)) / 2

        # A deeper groove marks where the knob points.
        if abs(math.remainder(a - math.pi / 2, 2 * math.pi)) < math.radians(5):
            rr = r - 2.2

        pts.append((rr * math.cos(a), rr * math.sin(a)))

    return pts


def build_knob():
    # Printed top-down: solid top on the bed, shaft hole facing up.
    outline = knob_outline()
    cap = prism([outline], 0, KNOB_TOP + 0.3)
    body = prism([outline, d_shaft(SHAFT_D / 2, SHAFT_FLAT)], KNOB_TOP, KNOB_H)
    return np.concatenate([cap, body])


def build_button_cap():
    # Printed flange down.
    flange = prism([circle(0, 0, CAP_FLANGE_D / 2)], 0, CAP_FLANGE_H)
    stem = prism([circle(0, 0, CAP_STEM_D / 2)], CAP_FLANGE_H - 0.3,
                 CAP_FLANGE_H + PANEL + CAP_PROUD)
    return np.concatenate([flange, stem])


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
        "knob": build_knob(),
        "button_cap": build_button_cap(),
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
