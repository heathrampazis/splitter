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
import keypad
import rotaryio
import usb_midi

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
# some pull D high and press it to ground, others the opposite. "auto"
# reads the pins at power-up, when nothing is pressed, and takes the
# other level as "pressed". Set "low" or "high" to fix it instead, for
# example if you power the Pico up with a finger on a button.
BUTTON_ACTIVE = "auto"

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

led_off_at = 0.0


def flash():
    global led_off_at

    if led is not None:
        led.value = True
        led_off_at = time.monotonic() + 0.03


def update_led():
    if led is not None and led.value and time.monotonic() >= led_off_at:
        led.value = False


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


# Works out whether D goes high or low when a button is pressed.
def detect_pressed_value():
    if BUTTON_ACTIVE == "high":
        return True

    if BUTTON_ACTIVE == "low":
        return False

    idle_high = 0

    for _, pin, _, _ in BUTTONS:
        reader = digitalio.DigitalInOut(pin)
        reader.direction = digitalio.Direction.INPUT
        reader.pull = None

        if reader.value:
            idle_high += 1

        reader.deinit()

    # Nothing is pressed yet, so pressed is the opposite of idle.
    return idle_high * 2 <= len(BUTTONS)


pressed_value = detect_pressed_value()

# keypad scans in the background and debounces for us. pull=False
# because the modules have their own resistor holding D steady; the
# Pico's internal pull would only fight it.
buttons = keypad.Keys(
    tuple(pin for _, pin, _, _ in BUTTONS),
    value_when_pressed=pressed_value,
    pull=False,
    interval=0.01,
)

event = keypad.Event()

if DEBUG:
    print("StemDeck controls ready")
    print("Buttons read", "high" if pressed_value else "low", "when pressed")

# ---------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------

while True:
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

    while buttons.events.get_into(event):
        name, _, _, note = BUTTONS[event.key_number]
        send_button(note, event.pressed)
        flash()

        if DEBUG:
            print(name, "pressed" if event.pressed else "released")

    update_led()

    # Fast enough that a quick spin still arrives as a stream of small
    # steps rather than one big jump, slow enough to leave the CPU idle.
    time.sleep(0.002)
