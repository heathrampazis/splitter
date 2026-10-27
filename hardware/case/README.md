# StemDeck case

A simple two-part printed box that hides the wiring. The **base** holds
the Pi 5 on four posts, with vents under it and openings for its ports.
The **lid** holds the four DFRobot buttons and the two encoder boards,
and **clips onto the base — no screws**. The 5″ Touch Display 2 drops
into a recess in the lid, landscape and glass up, and rests on a small
shelf in each corner; its back hangs into the box. Only its ribbon and
power wires go down to the Pi. Everything else is held with hot glue or
the encoders' own nuts.

![Assembled](preview/assembled.png)

```
+--------------------------------------------+
|                                            |
|               screen (landscape)           |
|                                            |
|  [VOCALS] [DRUMS] [INSTR]          (TEMPO) |
|                                            |
|  [PLAY]                  (( JOG ))         |
+--------------------------------------------+
                  front
```

Outside size: **176 × 174 × 52.5 mm**; the screen's glass stands about 1 mm above the lid. Every part fits on a 180 mm bed.

![Exploded](preview/assembly_exploded.png)

---

## Parts to print

| File                 | Qty | Orientation               | Notes                         |
|----------------------|-----|---------------------------|-------------------------------|
| `stl/base.stl`       | 1   | As exported, floor down   | The side opening is open at the top, and the power window is a short bridge, so no supports |
| `stl/top_panel.stl`  | 1   | As exported, face down    | The lid. The visible face prints on the bed, so it comes out smooth |
| `stl/encoder_washer.stl` | 2 | As exported, flat       | Goes under each encoder's nut and covers the hole |
| `stl/jog_knob.stl`   | 1   | As exported, top down     | 46 mm jog wheel with a finger dimple |
| `stl/tempo_knob.stl` | 1   | As exported, top down     | The groove on the side marks where it points |

**Settings:** PLA or PETG, 0.2 mm layers, 3 walls, 15–20 % infill, **no
supports** for anything. Brim on the base if your printer is prone to
warping corners.

Both knobs have a plain round 6 mm hole that pushes onto the encoders'
knurled, split shaft; the knurls bite into the plastic and the split
springs it tight. Print the tempo knob first and try it. If it is loose,
change `SHAFT_D` in `build_case.py` to 5.8; if it won't go on, 6.2. Then
rebuild.

`stl/knob.stl`, `stl/screen_frame.stl`, `preview/knob.png` and
`preview/base.png` are left over from earlier versions and are not used
any more; delete them.

---

## You also need

- The **nuts and washers that came with the encoder boards**
- **Hot glue** for the screen and the button modules
- 4 of the **M2.5 screws that came with the display**, to fix the Pi
  to its posts in the base

---

## Assembly

![Panel underside](preview/top_panel_underside.png)

1. **Pi into the base.** Screw the Pi 5 onto the four posts in the base
   with the M2.5 screws, USB and Ethernet towards the left-hand opening,
   USB-C towards the small window in the back, GPIO pins towards the front.
2. **Wire first.** Connect every button and encoder to the Pi with its
   jumper wires, following the [wiring diagram](../docs/pi-wiring.svg),
   and check them with `./scripts/test_controls.py`. It is much easier
   before anything is glued.
3. **Screen.** Plug the display's ribbon (the 22-way to 15-way cable for
   the Pi 5) and its power wires (pins 2 and 6) into the display. Feed
   them down through the screen recess in the lid. Lower the display into
   the recess, glass up, until it sits on the four corner shelves. It is
   a loose fit on purpose (1.5 mm spare each side); a dab of hot glue in two corners stops it
   moving. Plug the ribbon and power wires into the Pi.
4. **Encoders.** Both are the same EC11 "Rotary Encoder Module for
   Arduino". Take the nut and washer off, push the shaft up through its
   hole from underneath so the round board drops between the two rails,
   put a printed washer over the shaft on top of the lid, and tighten the
   nut on it. The holes are 14 mm, deliberately loose; the 21 mm washer
   hides the gap. Lay the boards left-right: **tempo with its pins
   pointing left**, **jog with its pins pointing right**. If the encoder
   has a small anti-rotation tab next to the bushing, snip it off with
   side cutters, or it will not sit flat.
5. **Buttons.** These are DFRobot Digital Push Button V2 modules, and
   their own coloured caps are the buttons - nothing to print. Push each
   module up into the frame under its hole, cap first, with the
   white plug towards the gap in the frame wall (towards the back, or to
   the right for play). Push it up until the cap stands about
   3 mm above the lid, so it is easy to press but its collar is still
   just below the surface, then hot glue the board's edges to the frame
   walls. The board ends up about 6.5 mm under the lid, and the side
   plug (about 5 mm tall) still clears it. Press the button a few times
   before the glue sets to check it clicks and doesn't rub the hole.
6. **Tidy the wires.** Bundle the jumper wires with a cable tie or a dab
   of glue so they don't catch on the encoders or the Pi's fan.
7. **Close it up.** Lower the lid onto the base — the lip on its
   underside goes just inside the walls — and press down round the edges
   until it clicks. To open it, lift at the finger notch in the middle of
   the front edge.
8. **Knobs.** Push the big printed jog knob onto the encoder at the
   front and the small one onto tempo, flat side matching. If your
   encoders came with knobs, you can use one of those for tempo instead.

The USB stick goes in through the opening in the left side, and the
power cable through the small window in the back. The back is otherwise
closed, so the Pi's micro HDMI ports are covered - they aren't used.

![Base with the Pi](preview/base_with_pi.png)

---

## Measure before printing

These come from datasheets and typical parts. A quick check with a ruler
or calipers before printing saves a reprint:

| What                               | Setting in `build_case.py`        | Value used |
|------------------------------------|-----------------------------------|------------|
| Display, left to right             | `SCREEN_W`                        | 143.5 mm   |
| Display, front to back             | `SCREEN_D`                        | 91.5 mm    |
| Display glass part, front to back of its edge | `SCREEN_SINK` sets how deep it sits | sits 5.5 mm down |
| Button module board                | `MODULE_W`, `MODULE_L`            | 22 × 30 mm (DFR0029) |
| Encoder board, across              | `ENC_BOARD_W`                     | rails take boards up to 28 mm across |
| Encoder threaded neck              | `ENCODER_HOLE`                    | 14 mm hole for the M7 neck, covered by the 21 mm printed washer |
| Encoder thread above the lid       | `WASHER_T`                        | washer is 1.5 mm, so the nut needs about 4 mm of thread |
| Encoder shaft                      | `SHAFT_D`                         | 6 mm knurled, split; knob hole 6.0 mm |
| DFR0029 yellow cap                 | `BUTTON_HOLE`                     | 16.5 mm hole for the 12.5 mm collar |
| DFR0029 switch position            | `SWITCH_OFFSET`                   | 3.2 mm from the board's middle, away from the plug |

The screen rests on four triangular corner shelves, 14 mm along each
edge (`CORNER_SHELF`), so the middle of its back is free. It is 16 mm
deep, so its back hangs about 10 mm into the box, well clear of the Pi
(about 20 mm of room is left for the jumper wires on the GPIO pins). If
the glass sits too low or too high, change `SCREEN_SINK`.

**The clips.** If the lid is too tight to press on, or falls off, change
`SNAP` (how far the bumps and ridges stick out, 0.5 mm) by 0.1–0.2 mm.
PLA is stiffer than PETG; PETG clips more forgivingly.

The port openings are generous. If a plug still fouls, widen
`POWER_HOLE_W` or `LEFT_NOTCH_Y`, or move the Pi with `PI_X` and `PI_Y`.

There is deliberately some play everywhere: 1.5 mm round the screen in
its recess, 16.5 mm button holes round the 12.5 mm caps, 1 mm round
each button board in its frame, and 14 mm encoder holes under 21 mm
washers. A little of the boards may show
through the gaps; that is expected.

---

## Changing the design

Everything is in `build_case.py`, with all measurements at the top under
**SETTINGS**: where each button and encoder sits (`BUTTONS`, `ENCODERS`),
where the Pi sits, the screen size, the box size, hole sizes, the button
frames, the clips and the knob shapes. Change a number and rebuild:

```bash
python3 build_case.py
```

It only needs `numpy`, and rewrites the files in `stl/`. The previews in
`preview/` are not regenerated by it.
