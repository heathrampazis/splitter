# StemDeck case

A simple two-part printed box that hides the wiring. The **base** holds
the Pi 5 on four posts, with vents under it and openings for its ports.
The **lid** holds the four DFRobot buttons and the two encoder boards,
and **simply sits on the base — no screws, no clips**. The 5″ Touch Display 2 drops
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
| `stl/jog_knob.stl`   | 1   | As exported, top down     | 38 mm jog wheel with a finger dimple |
| `stl/tempo_knob.stl` | 1   | As exported, top down     | 18 mm; the groove on the side marks where it points |

**Settings:** PLA, **no supports** for anything. A cheap draft setting
- 0.3 mm layers, 20 % infill - is fine for every part. Ask for at least
**3 walls (perimeters)**: the lid's lip, the button frames and the encoder
rails are only 1.4-1.6 mm thick, and the knobs need solid walls round
the shaft. Brim on the base if your printer is prone to warping
corners.

Both knobs have a plain round 6 mm hole, 9 mm deep and closed at the
top. It pushes onto the encoders' knurled, split shaft - the knurls bite
into the plastic and the split springs it tight - until the shaft's end
meets the top of the hole. That leaves the knob riding about 4 mm above
the nut, so it never rubs the lid. If a knob is loose, change `SHAFT_D`
in `build_case.py` to 5.8; if it won't go on, 6.2. Then rebuild and
reprint just that knob.

`stl/knob.stl`, `stl/screen_frame.stl`, `stl/button_cap.stl`,
`stl/encoder_washer.stl`, `preview/knob.png` and
`preview/base.png` are left over from earlier versions and are not used
any more; delete them.

---

## You also need

- The **nuts (and metal washers, if any) that came with the encoders**
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
   Arduino". Take the nut off, push the shaft up through its hole from
   underneath so the round board drops between the two rails, and
   tighten the nut on top of the lid (over its metal washer, if it came
   with one). The holes are 8.5 mm, a little looser than the 7 mm neck
   but small enough for the nut to clamp. Lay the boards left-right: **tempo with its pins
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
7. **Close it up.** Lower the lid onto the base. The lip on its
   underside drops just inside the walls (its bottom edge is chamfered,
   so it finds its own way in) and the lid rests on the top of the walls.
   To lift it off, use the finger notch in the middle of the front edge.
8. **Knobs.** Push the printed jog wheel onto the encoder at the front
   and the small knob onto tempo, until each stops on the end of its
   shaft. Give each a spin: it should turn freely, clear of the lid.

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
| Encoder threaded neck              | `ENCODER_HOLE`                    | 8.5 mm hole for the M7 neck; the nut clamps round it |
| Encoder shaft                      | `SHAFT_D`, `KNOB_BORE`            | 6 mm knurled, split; knob hole 6.0 mm, 9 mm deep |
| DFR0029 yellow cap                 | `BUTTON_HOLE`                     | 16.5 mm hole for the 12.5 mm collar |
| DFR0029 switch position            | `SWITCH_OFFSET`                   | 3.2 mm from the board's middle, away from the plug |

The screen rests on four triangular corner shelves, 14 mm along each
edge (`CORNER_SHELF`), so the middle of its back is free. It is 16 mm
deep, so its back hangs about 10 mm into the box, well clear of the Pi
(about 20 mm of room is left for the jumper wires on the GPIO pins). If
the glass sits too low or too high, change `SCREEN_SINK`.

**The lid.** It sits on with 0.6 mm of room each side of its lip
(`LIP_FIT`), which a draft-quality print won't eat up. If it ever
comes out tight, sand the outside of the lip; if you'd like it to snap
shut instead, set `SNAP` to 0.5 and rebuild to add clips.

The port openings are generous. If a plug still fouls, widen
`POWER_HOLE_W` or `LEFT_NOTCH_Y`, or move the Pi with `PI_X` and `PI_Y`.

There is deliberately some play everywhere: 1.5 mm round the screen in
its recess, 16.5 mm button holes round the 12.5 mm caps, 1 mm round
each button board in its frame, and 8.5 mm encoder holes round the
7 mm necks. A little of the boards may show
through the gaps; that is expected.

---

## Changing the design

Everything is in `build_case.py`, with all measurements at the top under
**SETTINGS**: where each button and encoder sits (`BUTTONS`, `ENCODERS`),
where the Pi sits, the screen size, the box size, hole sizes, the button
frames, the lid's fit and the knob shapes. Change a number and rebuild:

```bash
python3 build_case.py
```

It only needs `numpy`, and rewrites the files in `stl/`. The previews in
`preview/` are not regenerated by it.
