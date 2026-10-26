"""
Physical controls wired to the Raspberry Pi's own GPIO header.

Four buttons (play/pause, vocals, drums, instrumental) and two rotary
encoders (tempo and jog). See hardware/docs/pi-wiring.svg for the
wiring, or the table below. Pin numbers in the code are BCM GPIO
numbers, which is what gpiozero uses; physical header pins are in
brackets.

    Encoder board   GND        S1             S2             KEY            5V
    Tempo (BPM)     GND (9)    GPIO17 (11)    GPIO27 (13)    GPIO22 (15)    3V3 (17)
    Jog wheel       GND (39)   GPIO26 (37)    GPIO19 (35)    -              GPIO6 (31)

    Button module   D              +              -
    Play / pause    GPIO9  (21)    GPIO11 (23)    GND (25)
    Vocals          GPIO24 (18)    GPIO23 (16)    GND (14)
    Drums           GPIO8  (24)    GPIO25 (22)    GND (20)
    Instrumental    GPIO20 (38)    GPIO16 (36)    GND (34)

Each module's D, + and - pins sit on three header pins in a row, in the
same order as on the module, so a three-wire ribbon goes straight
across.

The tempo encoder's KEY (pressing the knob) resets the tempo to 0 %; it
is optional. The jog encoder's KEY is not used. Never connect anything here
to the 5 V pins (2 and 4): the Pi's GPIO pins only take 3.3 V, and the
encoder boards pass their supply straight through to S1 and S2.

Two things carried over from the Pico version, because they are what
made the hardware work:

  * The button modules have no resistor holding D steady, so D would
    float. Their + pin goes to a GPIO switched to 0 V, making it a
    second ground, and D uses the Pi's internal pull-up. D then rests
    high and the switch pulls it low, whichever side of the switch the
    module wires D to.

  * The Pi has only two 3.3 V pins, and every wire has a pin of its own,
    so the jog encoder board's 5V pin is powered from a GPIO switched on
    to 3.3 V. The board only holds a few resistors; a GPIO powers it
    easily.

Threading: gpiozero calls back on its own threads, and Qt widgets must
only be touched from the main thread, so every event becomes a Qt
signal that Qt delivers on the main thread.
"""

from gpiozero import Button, DigitalOutputDevice, RotaryEncoder
from PySide6.QtCore import QObject, Signal

# ---------------------------------------------------------------------
# Wiring (BCM GPIO numbers)
# ---------------------------------------------------------------------

# name: (S1, S2, power GPIO or None when wired to a real 3V3 pin)
ENCODERS = {
    "tempo": (17, 27, None),
    "jog": (26, 19, 6),
}

# Push switches built into the encoders: name: GPIO. The encoder board
# holds them high itself, so they read low when pressed.
KEYS = {
    "tempo_reset": 22,
}

# name: (D, +)
BUTTONS = {
    "play": (9, 11),
    "vocals": (24, 23),
    "drums": (8, 25),
    "instrumental": (20, 16),
}

# Encoders that count the wrong way round. Swapping the S1 and S2 wires
# does the same.
REVERSED = set()  # for example {"jog"}

# How a button module is read:
#   "pull-up" - + is switched to 0 V and D uses the Pi's pull-up. Suits
#               modules without their own resistor, like the ones this
#               was built with.
#   "module"  - + is switched to 3.3 V and the module's own resistor
#               holds D. Then BUTTON_ACTIVE_HIGH says which way it goes.
BUTTON_MODE = "pull-up"
BUTTON_ACTIVE_HIGH = True

BOUNCE_SECONDS = 0.02


PIN_HELP = (
    "another driver is using that pin. Check /boot/firmware/config.txt "
    "for dtparam=spi=on or a dtoverlay= line for an old screen, and "
    "comment it out with #, then reboot")


# Turns a gpiozero error into something that says what to do about it.
def describe(error):
    text = f"{type(error).__name__}: {error}"

    if "busy" in text.lower() or "in use" in text.lower():
        return f"{text} ({PIN_HELP})"

    return text


class GPIOControls(QObject):
    # Emitted on gpiozero's threads, delivered on the Qt main thread.
    button_changed = Signal(str, bool)
    encoder_turned = Signal(str, int)

    def __init__(self, app):
        super().__init__()

        self.app = app

        # gpiozero devices stop working once nothing refers to them,
        # so every one is kept here.
        self.devices = []

        self.button_changed.connect(app.handle_button)
        self.encoder_turned.connect(app.handle_turn)

        # Each control is set up on its own, so one pin that cannot be
        # claimed does not take every control after it down too.
        ready, failed = [], []

        controls = (
            [(name, self.add_encoder, spec) for name, spec in ENCODERS.items()]
            + [(name, self.add_button, spec) for name, spec in BUTTONS.items()]
            + [(name, self.add_key, (pin,)) for name, pin in KEYS.items()]
        )

        for name, add, spec in controls:
            try:
                add(name, *spec)
                ready.append(name)
            except Exception as e:
                failed.append(name)
                print(f"Controls: {name} could not be set up - {describe(e)}")

        if not ready:
            raise RuntimeError("no GPIO control could be set up")

        print("Controls: GPIO ready:", ", ".join(ready))

        if failed:
            print("Controls: GPIO not working:", ", ".join(failed))

    def add_encoder(self, name, s1, s2, power):
        if power is not None:
            self.devices.append(DigitalOutputDevice(power, initial_value=True))

        # max_steps=0 means it never stops counting; only the direction
        # of each click matters here.
        encoder = RotaryEncoder(s1, s2, max_steps=0)

        sign = -1 if name in REVERSED else 1

        encoder.when_rotated_clockwise = (
            lambda: self.encoder_turned.emit(name, sign))
        encoder.when_rotated_counter_clockwise = (
            lambda: self.encoder_turned.emit(name, -sign))

        self.devices.append(encoder)

    def add_button(self, name, d_pin, plus_pin):
        if BUTTON_MODE == "pull-up":
            self.devices.append(DigitalOutputDevice(plus_pin, initial_value=False))
            button = Button(d_pin, pull_up=True, bounce_time=BOUNCE_SECONDS)
        else:
            self.devices.append(DigitalOutputDevice(plus_pin, initial_value=True))
            button = Button(d_pin, pull_up=None, active_state=BUTTON_ACTIVE_HIGH,
                            bounce_time=BOUNCE_SECONDS)

        button.when_pressed = lambda: self.button_changed.emit(name, True)
        button.when_released = lambda: self.button_changed.emit(name, False)

        self.devices.append(button)

    def add_key(self, name, pin):
        key = Button(pin, pull_up=True, bounce_time=BOUNCE_SECONDS)
        key.when_pressed = lambda: self.button_changed.emit(name, True)
        key.when_released = lambda: self.button_changed.emit(name, False)
        self.devices.append(key)

    def close(self):
        for device in self.devices:
            try:
                device.close()
            except Exception:
                pass

        self.devices = []
