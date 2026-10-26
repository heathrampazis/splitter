"""
StemDeck controls - firmware for the Raspberry Pi Pico 2 W (CircuitPython).

Reads four rotary encoders and three buttons and sends them to the
Raspberry Pi as USB MIDI. The Pi never sees a pin number: it only gets
MIDI messages, so the player can be tested on any computer with any
MIDI controller.

Install: copy this file and boot.py onto the CIRCUITPY drive. No extra
libraries are needed. See hardware/README.md for the full steps.

Wiring (physical pin numbers in brackets, see docs/pico-wiring.svg):

    Encoder        C (middle)    A             B
    Tempo          GND (3)       GP2  (4)      GP3  (5)
    Vocals         GND (8)       GP6  (9)      GP7  (10)
    Drums          GND (13)      GP10 (14)     GP11 (15)
    Bass + other   GND (18)      GP14 (19)     GP15 (20)

    Button module  +             D             -
    Play / pause   GP16 (21)     GP17 (22)     GND (23)
    Search back    GP20 (26)     GP21 (27)     GND (28)
    Search fwd     GP26 (31)     GP27 (32)     GND (33)

Every wire has a pin of its own. The Pico has only one 3V3 pin, so each
button's + is powered from a GPIO that this code switches on to 3.3 V at
start-up. A module draws well under a milliamp, which a GPIO supplies
easily.

Each encoder's A and B must be on neighbouring GPIOs: rotaryio uses the
Pico's PIO hardware, which counts every step without missing one but
needs the two pins side by side.
"""

import time

import board
import digitalio
import rotaryio
import usb_midi

try:
    import traceback
except ImportError:
    traceback = None

# ---------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------

# MIDI channel 1. The player listens on every channel, so this only
# matters if the Pico ever shares a USB hub with another controller.
MIDI_CHANNEL = 0

# Signal changes per click. Most detented encoders make four, which is
# rotaryio's default. Some make two: if it takes two clicks to move a
# fader one step, change this to 2.
ENCODER_DIVISOR = 4

# Encoders that count the wrong way round. Swapping the A and B wires
# fixes it too, but this saves getting the soldering iron out.
REVERSED = set()  # for example {"tempo"}

# What the button modules' D pin reads while pressed. Modules differ:
# some hold D high and pull it low when pressed, others the opposite.
# "auto" takes whatever D reads at rest as "not pressed", and keeps
# checking: if a button seems held down for longer than
# RELEARN_SECONDS, that reading must really be its resting state, and
# it is treated as such from then on. Set "low" or "high" to fix it.
BUTTON_ACTIVE = "auto"
RELEARN_SECONDS = 20.0

# A button must hold steady this long to count, which hides the
# chatter of the switch contacts.
DEBOUNCE_SECONDS = 0.015

# Prints every message to the serial console, which is handy while
# wiring: open the Pico's serial port and turn each knob in turn.
DEBUG = True

# (name, pin A, pin B, MIDI CC number)
ENCODERS = (
    ("tempo", board.GP2, board.GP3, 1),
    ("vocals", board.GP6, board.GP7, 2),
    ("drums", board.GP10, board.GP11, 3),
    ("bass_other", board.GP14, board.GP15, 4),
)

# (name, D pin, + pin, MIDI note number)
BUTTONS = (
    ("play", board.GP17, board.GP16, 60),
    ("search_back", board.GP21, board.GP20, 61),
    ("search_forward", board.GP27, board.GP26, 62),
)

# ---------------------------------------------------------------------
# MIDI output
# ---------------------------------------------------------------------

# ports[0] is MIDI coming in from the Pi, ports[1] is MIDI going out.
midi_out = usb_midi.ports[1]

CONTROL_CHANGE = 0xB0
NOTE_ON = 0x90
NOTE_OFF = 0x80


def send(status, data1, data2):
    midi_out.write(bytes((status | MIDI_CHANNEL, data1 & 0x7F, data2 & 0x7F)))


# Encoders send relative values: 1 to 63 for clockwise steps, 65 to 127
# for anticlockwise (127 is one step back, 126 two, and so on). The Pi
# adds them to whatever the fader is at, so the knob and the screen can
# never disagree. A spin bigger than 63 steps goes as several messages.
def send_turn(cc, steps):
    while steps:
        chunk = max(-63, min(63, steps))
        send(CONTROL_CHANGE, cc, chunk)
        steps -= chunk


def send_button(note, pressed):
    if pressed:
        send(NOTE_ON, note, 127)
    else:
        send(NOTE_OFF, note, 0)


# ---------------------------------------------------------------------
# Status LED
# ---------------------------------------------------------------------

# On the Pico 2 W the LED hangs off the wireless chip rather than a
# normal GPIO. It flashes on every message so you can see the Pico
# heard a knob even before the Pi is plugged in.
try:
    led = digitalio.DigitalInOut(board.LED)
    led.direction = digitalio.Direction.OUTPUT
except Exception:
    led = None

led_on = False
led_off_at = 0.0


def flash():
    global led_on, led_off_at

    if led is not None:
        led.value = True
        led_on = True
        led_off_at = time.monotonic() + 0.03


def update_led():
    global led_on

    if led is not None and led_on and time.monotonic() >= led_off_at:
        led.value = False
        led_on = False


# ---------------------------------------------------------------------
# Hardware
# ---------------------------------------------------------------------

encoders = []

for name, pin_a, pin_b, cc in ENCODERS:
    encoder = rotaryio.IncrementalEncoder(pin_a, pin_b, divisor=ENCODER_DIVISOR)
    encoders.append([name, encoder, cc, encoder.position])

# Each module's + pin is a GPIO held at 3.3 V. Kept in a list so the
# pins stay claimed for as long as the code runs.
button_power = []

for _, _, power_pin, _ in BUTTONS:
    supply = digitalio.DigitalInOut(power_pin)
    supply.switch_to_output(value=True)
    button_power.append(supply)

# Give the modules a moment to settle before reading them.
time.sleep(0.05)


# Reads a button's D pin.
#
# Each reading claims the pin, reads it and lets it go again, rather
# than leaving it set up as an input. That works around erratum E9 of
# the Pico 2's RP2350 chip: a pin left as an input, held low only by a
# module's weak resistor, can get stuck reading high, so the button
# appears to press once and then never again.
def read_pin(pin):
    reader = digitalio.DigitalInOut(pin)
    reader.switch_to_input(pull=None)
    value = reader.value
    reader.deinit()
    return value


class Button:
    def __init__(self, name, pin, note):
        self.name = name
        self.pin = pin
        self.note = note

        now = time.monotonic()
        level = read_pin(pin)

        # The level that means "not pressed".
        if BUTTON_ACTIVE == "high":
            self.rest = False
        elif BUTTON_ACTIVE == "low":
            self.rest = True
        else:
            self.rest = level

        self.raw = level            # latest reading
        self.raw_since = now
        self.stable = level         # latest reading that held steady
        self.stable_since = now
        self.pressed = level != self.rest

    def update(self, now):
        level = read_pin(self.pin)

        if level != self.raw:
            self.raw = level
            self.raw_since = now

            if DEBUG:
                print(self.name, "D pin reads", int(level))

        if level != self.stable and now - self.raw_since >= DEBOUNCE_SECONDS:
            self.stable = level
            self.stable_since = now
            self.set_pressed(level != self.rest)

        # Held "down" for ages: the resting level was guessed wrong, for
        # example because a button was pressed while the Pico started.
        if (BUTTON_ACTIVE == "auto" and self.pressed
                and now - self.stable_since >= RELEARN_SECONDS):
            self.rest = self.stable

            if DEBUG:
                print(self.name, "now treats", int(self.rest), "as not pressed")

            self.set_pressed(False)

    def set_pressed(self, pressed):
        if pressed == self.pressed:
            return

        self.pressed = pressed
        send_button(self.note, pressed)
        flash()

        if DEBUG:
            print(self.name, "pressed" if pressed else "released")


buttons = [Button(name, pin, note) for name, pin, _, note in BUTTONS]

if DEBUG:
    print("StemDeck controls ready")

    for button in buttons:
        print(button.name, "rests at", int(button.rest))

# ---------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------


def tick():
    for entry in encoders:
        name, encoder, cc, last = entry
        position = encoder.position
        steps = position - last

        if steps:
            entry[3] = position

            if name in REVERSED:
                steps = -steps

            send_turn(cc, steps)
            flash()

            if DEBUG:
                print(name, "+" if steps > 0 else "-", abs(steps))

    now = time.monotonic()

    for button in buttons:
        button.update(now)

    update_led()


while True:
    # An error is printed and the loop carries on, rather than the code
    # stopping and switching every pin - including the buttons' power -
    # off.
    try:
        tick()
    except Exception as e:
        print("Error:", repr(e))

        if traceback is not None:
            try:
                traceback.print_exception(e)
            except Exception:
                pass

        time.sleep(0.5)

    # Fast enough that a quick spin still arrives as a stream of small
    # steps rather than one big jump, slow enough to leave the CPU idle.
    time.sleep(0.002)
