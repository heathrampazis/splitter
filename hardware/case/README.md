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

Outside size: **176 × 184 × 52.5 mm**; the screen's glass stands about 1 mm above the lid. The base and lid need a print bed of at least 185 mm each way (a common 220 mm bed is fine).

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

Each knob's shaft hole is a split, springy sleeve, standing free of the
rest of the knob, so it hugs the knurled shaft even if the print comes
out a little big or small. It is 9 mm deep and closed at the top: the
knob pushes on until the shaft's end meets the top, which leaves it
riding about 4 mm above the nut, clear of the lid. If a knob is loose,
change `SHAFT_D` in `build_case.py` from 5.8 to 5.6; if it won't go on,
6.0. Then rebuild and reprint just that knob. For a knob that will never
come off, put a drop of superglue in the hole first.

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
   the recess, glass up, until it sits on the ledge that runs round the
   inside and the four triangular corner shelves. It is
   a loose fit on purpose (2 mm spare each side); a dab of hot glue in two corners stops it
   moving. Plug the ribbon and power wires into the Pi.
4. **Buttons and encoders onto their pillars.** The base has a hollow
   pillar under each button and each encoder, the same shape as its
   board but a little smaller, so its thin rim is always under the board:
   a rectangle for each button, a round tube for each encoder (with a
   slot on the side its pins and plugs are). Anything sticking out of a
   board's underside sits in the hollow middle. The boards are
   glued on top of them, so every press - a button, or the tempo knob -
   pushes straight down through a pillar to the floor.
   1. Put a blob of hot glue on top of each pillar.
   2. Stand each board on its pillar: the button modules cap up, with
      the white plug towards the back (to the right for play), and the
      encoders shaft up, **tempo with its pins pointing left** and **jog
      with its pins pointing right**. If an encoder has a small
      anti-rotation tab next to its threaded neck, snip it off first.
   3. While the glue is still soft, lower the lid on. The button caps
      and encoder shafts come up through their holes, and the frames and
      rails under the lid nudge each board into exactly the right spot.
      Hold the lid down for a minute while the glue sets.
   4. The nuts are optional: the holes are 11 mm, roomy round the 7 mm
      neck and wider than the nut, and the pillars and glue hold the
      encoders. To clamp them as well, put a washer of 13 mm or more
      over each neck on top of the lid and screw the nut down on it.

   The pillars stop 0.5 mm under the boards, which the glue fills. Their
   heights come from two measurements in the table below - check them
   on your parts first, because they decide how high everything sits.
   The button caps stand about 2.5 mm above the lid. To take the lid off
   later, unscrew the two encoder nuts first; the boards stay on their
   pillars.
   The three stem buttons' plugs point back towards the screen. There
   are about 8 mm of open space between them and the screen's recess,
   so their wires can bend straight down and back to the Pi.
5. **Check them.** Press each button and the tempo knob, and turn both
   encoders, with `./scripts/test_controls.py` running.
6. **Tidy the wires.** Bundle the jumper wires with a cable tie or a dab
   of glue so they don't catch on the encoders or the Pi's fan.
7. **The lid.** It went on in step 4. Its lip drops just inside the
   walls (the bottom edge is chamfered, so it finds its own way in) and
   it rests on top of the walls. To lift it off, unscrew the two encoder
   nuts and lift at the finger notch in the middle of the front edge.
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
| Encoder threaded neck              | `ENCODER_HOLE`                    | 11 mm hole for the M7 neck: 2 mm of room each side, like the buttons |
| Encoder shaft                      | `SHAFT_D`, `KNOB_BORE`            | 6 mm knurled, split; knob sleeve 5.8 mm, 9 mm deep |
| DFR0029 yellow cap                 | `BUTTON_HOLE`                     | 16.5 mm hole for the 12.5 mm collar |
| DFR0029 switch position            | `SWITCH_OFFSET`                   | 3.2 mm from the board's middle, away from the plug |
| Button pillar height: board's top to the top of its cap | `CAP_HEIGHT` | 11.7 mm |
| Encoder pillar height: top of the encoder's metal body to the bottom of its board | `ENC_BOARD_DOWN` | 9.5 mm |
| Encoder board, across              | `ENC_BOARD_D`                     | 25 mm |

The screen rests on a 4 mm ledge all round the recess (`SCREEN_LEDGE`)
and four triangular corner shelves, 14 mm along each edge
(`CORNER_SHELF`), so the middle of its back is free. It is 16 mm
deep, so its back hangs about 10 mm into the box, well clear of the Pi
(about 20 mm of room is left for the jumper wires on the GPIO pins). If
the glass sits too low or too high, change `SCREEN_SINK`.

**The lid.** It sits on with 0.6 mm of room each side of its lip
(`LIP_FIT`), which a draft-quality print won't eat up. If it ever
comes out tight, sand the outside of the lip; if you'd like it to snap
shut instead, set `SNAP` to 0.5 and rebuild to add clips.

The port openings are generous. If a plug still fouls, widen
`POWER_HOLE_W` or `LEFT_NOTCH_Y`, or move the Pi with `PI_X` and `PI_Y`.

There is deliberately some play everywhere: 2 mm round the screen in
its recess, 16.5 mm button holes round the 12.5 mm caps, 1 mm round
each button board in its frame, and 11 mm encoder holes round the
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
