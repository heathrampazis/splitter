#!/usr/bin/env python3
"""
Checks the Pico controller on its own, without starting the player.

    ./scripts/test_controls.py

Lists the MIDI devices the Pi can see, opens the Pico, and prints every
press and turn as it arrives. Press Ctrl+C to stop.

If presses show up here but the player ignores them, the problem is in
the player. If nothing shows up here, it is the Pico, its cable or the
MIDI libraries.
"""

import os
import sys
from pathlib import Path

HARDWARE_DIR = Path(__file__).resolve().parent.parent
VENV = HARDWARE_DIR / "venv"

# Run inside the environment setup.sh built, where mido is installed,
# even when started as ./scripts/test_controls.py.
if VENV.exists() and Path(sys.prefix).resolve() != VENV.resolve():
    python = str(VENV / "bin" / "python")
    os.execv(python, [python, *sys.argv])

# Use the player's own settings, so this tests exactly what it uses.
sys.path.insert(0, str(HARDWARE_DIR / "core"))

try:
    import mido
except ImportError:
    print("mido is not installed. Run ./scripts/setup.sh again.")
    sys.exit(1)

from controls.midi_controls import BUTTON_NOTES, ENCODER_CCS, MidiControls

try:
    names = mido.get_input_names()
except Exception as e:
    print("Could not list MIDI devices:", e)
    print("python-rtmidi is probably missing. Run ./scripts/setup.sh again.")
    sys.exit(1)

print("MIDI inputs the Pi can see:")

for name in names:
    print("   ", name)

if not names:
    print("    (none)")

port_name = MidiControls.find_port(names)

if port_name is None:
    print()
    print("The Pico is not among them. Check it is plugged in with a data")
    print("cable (not charge-only), and that boot.py and code.py are on it.")
    sys.exit(1)

print()
print("Listening to", port_name)
print("Press buttons and turn knobs. Ctrl+C to stop.")
print()

try:
    with mido.open_input(port_name) as port:
        for message in port:
            if message.type == "control_change":
                name = ENCODER_CCS.get(message.control, "unknown CC")
                value = message.value
                steps = value if value < 64 else value - 128
                print(f"{name:15} {steps:+d}   ({message})")

            elif message.type in ("note_on", "note_off"):
                name = BUTTON_NOTES.get(message.note, "unknown note")
                pressed = message.type == "note_on" and message.velocity > 0
                print(f"{name:15} {'pressed' if pressed else 'released':8}   ({message})")

            else:
                print(message)

except KeyboardInterrupt:
    print()
