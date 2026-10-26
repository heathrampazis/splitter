#!/usr/bin/env python3
"""
Checks the buttons and encoders on their own, without starting the
player.

    ./scripts/test_controls.py

Sets up the GPIO pins exactly as the player does, then prints every
press and every click of an encoder as it happens. Press Ctrl+C to stop.

If something shows up here but the player ignores it, the problem is in
the player. If nothing shows up here, it is the wiring or the soldering.
"""

import os
import signal
import sys
from pathlib import Path

HARDWARE_DIR = Path(__file__).resolve().parent.parent
VENV = HARDWARE_DIR / "venv"

# Run inside the environment setup.sh built, where gpiozero is installed,
# even when started as ./scripts/test_controls.py.
if VENV.exists() and Path(sys.prefix).resolve() != VENV.resolve():
    python = str(VENV / "bin" / "python")
    os.execv(python, [python, *sys.argv])

# Use the player's own wiring table, so this tests exactly what it uses.
sys.path.insert(0, str(HARDWARE_DIR / "core"))

try:
    from gpiozero import Button, DigitalOutputDevice, RotaryEncoder
except ImportError:
    print("gpiozero is not installed. Run ./scripts/setup.sh again.")
    sys.exit(1)

from controls.gpio_controls import (BOUNCE_SECONDS, BUTTON_ACTIVE_HIGH,
                                    BUTTON_MODE, BUTTONS, ENCODERS, KEYS,
                                    REVERSED, describe)

devices = []
counts = {}


def report_turn(name, direction):
    counts[name] = counts.get(name, 0) + direction
    print(f"{name:14} {'+1' if direction > 0 else '-1'}   (total {counts[name]:+d})")


def report_button(name, pressed):
    print(f"{name:14} {'pressed' if pressed else 'released'}")


def setup_encoder(name, s1, s2, power):
    if power is not None:
        devices.append(DigitalOutputDevice(power, initial_value=True))

    encoder = RotaryEncoder(s1, s2, max_steps=0)
    sign = -1 if name in REVERSED else 1
    encoder.when_rotated_clockwise = lambda: report_turn(name, sign)
    encoder.when_rotated_counter_clockwise = lambda: report_turn(name, -sign)
    devices.append(encoder)

    return f"encoder on GPIO{s1} and GPIO{s2}"


def setup_button(name, d_pin, plus_pin):
    if BUTTON_MODE == "pull-up":
        devices.append(DigitalOutputDevice(plus_pin, initial_value=False))
        button = Button(d_pin, pull_up=True, bounce_time=BOUNCE_SECONDS)
    else:
        devices.append(DigitalOutputDevice(plus_pin, initial_value=True))
        button = Button(d_pin, pull_up=None, active_state=BUTTON_ACTIVE_HIGH,
                        bounce_time=BOUNCE_SECONDS)

    button.when_pressed = lambda: report_button(name, True)
    button.when_released = lambda: report_button(name, False)
    devices.append(button)

    state = "reads PRESSED before touching it - check its wiring" \
        if button.is_pressed else "up"
    return f"button, D on GPIO{d_pin}, + on GPIO{plus_pin}: {state}"


def setup_key(name, pin):
    key = Button(pin, pull_up=True, bounce_time=BOUNCE_SECONDS)
    key.when_pressed = lambda: report_button(name, True)
    key.when_released = lambda: report_button(name, False)
    devices.append(key)

    return f"push switch on GPIO{pin}"


controls = (
    [(name, setup_encoder, spec) for name, spec in ENCODERS.items()]
    + [(name, setup_button, spec) for name, spec in BUTTONS.items()]
    + [(name, setup_key, (pin,)) for name, pin in KEYS.items()]
)

working = 0

for name, setup, spec in controls:
    try:
        print(f"{name:14} {setup(name, *spec)}")
        working += 1
    except Exception as e:
        print(f"{name:14} FAILED - {describe(e)}")

if not working:
    print()
    print("Nothing could be set up. Run ./scripts/setup.sh, and make sure the")
    print("player is not running at the same time.")
    sys.exit(1)

print()
print("Press the buttons and turn the knobs. Ctrl+C to stop.")
print()

try:
    signal.pause()
except KeyboardInterrupt:
    print()
finally:
    for device in devices:
        device.close()
