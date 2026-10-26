"""
StemDeck controls - firmware for the Raspberry Pi Pico 2 W (CircuitPython).

Reads four rotary encoders and three buttons and sends them to the
Raspberry Pi as USB MIDI. The Pi never sees a pin number: it only gets
MIDI messages, so the player can be tested on any computer with any
MIDI controller.

Install: copy this file and boot.py onto the CIRCUITPY drive. No extra
libraries are needed. See hardware/README.md for the full steps.

Wiring (physical pin numbers in brackets, see docs/pico-wiring.svg):

    Encoder board  5V            GND           S1            S2
    Tempo          GP1  (2)      GND (3)       GP2  (4)      GP3  (5)
    Vocals         GP5  (7)      GND (8)       GP6  (9)      GP7  (10)
    Drums          GP9  (12)     GND (13)      GP10 (14)     GP11 (15)
    Bass + other   GP13 (17)     GND (18)      GP14 (19)     GP15 (20)

The encoder boards' KEY pin (the push switch) is not used.

    Button module  +             D             -
    Play / pause   GP16 (21)     GP17 (22)     GND (23)
    Search back    GP20 (26)     GP21 (27)     GND (28)
    Search fwd     GP26 (31)     GP27 (32)     GND (33)

Every wire has a pin of its own. The Pico has a single 3.3 V pin, so
the encoder boards' 5V pins are powered from GPIOs this code switches
on to 3.3 V (the boards only hold a few resistors, which work at 3.3 V,
and the Pico's pins must never see 5 V). The buttons' + wires also go to
GPIOs, so the code can choose what to do with them - see "Buttons".

Open the Pico's serial console to watch it work: every pin change,
turn and press is printed.
"""

import time

import board
import digitalio
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

# Signal changes per click. Most detented encoders make four. Some make
# two: if it takes two clicks to move a fader one step, change this to 2.
ENCODER_DIVISOR = 4

# Encoders that count the wrong way round. Swapping the A and B wires
# fixes it too.
REVERSED = set()  # for example {"tempo"}

# A button must hold steady this long to count, which hides the
# chatter of the switch contacts.
DEBOUNCE_SECONDS = 0.02

# Prints turns and presses to the serial console.
DEBUG = True

# Also prints every raw pin change. Very chatty, but it shows exactly
# what each wire is doing, which is what you want while wiring. Set to
# False once everything works.
DEBUG_PINS = True

# (name, S1 pin, S2 pin, MIDI CC number, 5V pin)
ENCODERS = (
    ("tempo", board.GP2, board.GP3, 1, board.GP1),
    ("vocals", board.GP6, board.GP7, 2, board.GP5),
    ("drums", board.GP10, board.GP11, 3, board.GP9),
    ("bass_other", board.GP14, board.GP15, 4, board.GP13),
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
# normal GPIO. It flashes on every message sent.
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
# Encoders
# ---------------------------------------------------------------------

# Read in software rather than with rotaryio, so the pins' internal
# pull-ups are definitely on (the encoder's C pin is ground, so A and B
# need pulling up to read anything) and every pin change can be printed.
#
# A and B together make a two-bit state that steps round 11 -> 01 -> 00
# -> 10 -> 11 one way and the opposite order the other way. Each step
# counts +1 or -1, and a click is counted when the encoder comes back
# to rest, so a missed step can never leave it out of sync.

STEP = {
    (0b11, 0b01): 1, (0b01, 0b00): 1, (0b00, 0b10): 1, (0b10, 0b11): 1,
    (0b11, 0b10): -1, (0b10, 0b00): -1, (0b00, 0b01): -1, (0b01, 0b11): -1,
}

# Where a detented encoder sits between clicks.
REST_STATES = (0b11,) if ENCODER_DIVISOR == 4 else (0b11, 0b00)


def input_pin(pin, pull):
    io = digitalio.DigitalInOut(pin)
    io.switch_to_input(pull=pull)
    return io


class Encoder:
    def __init__(self, name, pin_a, pin_b, cc, power_pin):
        self.name = name
        self.cc = cc

        # The board's resistors hold S1 and S2 high from its 5V pin.
        # Without power on it they link S1 and S2 together instead.
        self.power = digitalio.DigitalInOut(power_pin)
        self.power.switch_to_output(value=True)

        self.a = input_pin(pin_a, digitalio.Pull.UP)
        self.b = input_pin(pin_b, digitalio.Pull.UP)
        self.state = self.read()
        self.count = 0

    def read(self):
        return (int(self.a.value) << 1) | int(self.b.value)

    def update(self):
        state = self.read()

        if state == self.state:
            return

        if DEBUG_PINS:
            print(self.name, "S1", state >> 1, "S2", state & 1)

        self.count += STEP.get((self.state, state), 0)
        self.state = state

        if state in REST_STATES and abs(self.count) >= 2:
            steps = 1 if self.count > 0 else -1
            self.count = 0

            if self.name in REVERSED:
                steps = -steps

            send_turn(self.cc, steps)
            flash()

            if DEBUG:
                print(self.name, "+1" if steps > 0 else "-1")

        elif state in REST_STATES:
            self.count = 0


# ---------------------------------------------------------------------
# Buttons
# ---------------------------------------------------------------------

# The modules have three pins: D, + and -. How they are wired inside
# varies, and some have no resistor holding D steady, so D floats and
# flickers between 0 and 1 on its own.
#
# So at start-up each button is tried two ways:
#
#   "pull-up": + is switched to ground, making it a second - pin, and D
#       gets the Pico's own pull-up. D rests at 1 and the switch pulls it
#       to 0 - whichever of + or - the switch connects D to, as both are
#       now ground. This suits modules with no resistor of their own.
#
#   "module": + is switched on to 3.3 V and D is read as it is. This
#       suits modules with their own resistor, which shows up as D being
#       held at 0 in the first test.


class Button:
    def __init__(self, name, pin, power_pin, note):
        self.name = name
        self.note = note

        self.power = digitalio.DigitalInOut(power_pin)
        self.power.switch_to_output(value=False)

        self.io = input_pin(pin, digitalio.Pull.UP)
        time.sleep(0.005)

        if self.io.value:
            self.mode = "pull-up"
            self.rest = True
        else:
            # Something on the module holds D at 0 against the pull-up:
            # it has its own resistor, so power it and let it drive D.
            self.mode = "module"
            self.io.switch_to_input(pull=None)
            self.power.value = True
            time.sleep(0.005)
            self.rest = self.io.value

        now = time.monotonic()
        level = self.io.value
        self.raw = level
        self.raw_since = now
        self.stable = level
        self.pressed = level != self.rest

    def update(self, now):
        level = self.io.value

        if level != self.raw:
            self.raw = level
            self.raw_since = now

            if DEBUG_PINS:
                print(self.name, "D pin reads", int(level))

        if level != self.stable and now - self.raw_since >= DEBOUNCE_SECONDS:
            self.stable = level
            self.set_pressed(level != self.rest)

    def set_pressed(self, pressed):
        if pressed == self.pressed:
            return

        self.pressed = pressed
        send_button(self.note, pressed)
        flash()

        if DEBUG:
            print(self.name, "pressed" if pressed else "released")


# ---------------------------------------------------------------------
# Start-up
# ---------------------------------------------------------------------

encoders = [Encoder(*spec) for spec in ENCODERS]
time.sleep(0.005)

for encoder in encoders:
    encoder.state = encoder.read()
buttons = [Button(name, pin, power, note) for name, pin, power, note in BUTTONS]

if DEBUG:
    print("StemDeck controls ready")

    for encoder in encoders:
        print(encoder.name, "starts at S1", encoder.state >> 1,
              "S2", encoder.state & 1, "(should be S1 1 S2 1)")

    for button in buttons:
        print(button.name, "uses", button.mode, "mode, rests at", int(button.rest))

# ---------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------


def tick():
    for encoder in encoders:
        encoder.update()

    now = time.monotonic()

    for button in buttons:
        button.update(now)

    update_led()


while True:
    # An error is printed and the loop carries on, rather than the code
    # stopping and switching every pin off.
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

    # Short enough to catch every step of a quickly spun encoder.
    time.sleep(0.001)
