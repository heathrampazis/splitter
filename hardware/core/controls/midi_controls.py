"""
Optional controls over USB MIDI.

The main controls are wired to the Pi's GPIO (see gpio_controls.py).
This listens for a USB MIDI controller as well, sending the same
actions, which is handy for testing the player on a laptop with any
MIDI controller. Nothing needs to be plugged in for the player to work.

Threading: mido delivers messages on its own background thread, and Qt
widgets must only be touched from the main thread. Every message is
therefore turned into a Qt signal, which Qt queues across to the main
thread before any handler runs.
"""

import mido
from PySide6.QtCore import QObject, QTimer, Signal

# MIDI inputs whose name contains one of these are listened to.
# "StemDeck" and the others match the Pico firmware in hardware/firmware;
# add your own controller's name here to use it.
PORT_KEYWORDS = ("stemdeck", "circuitpython", "pico")

# How often to look for the controller being plugged in or pulled out.
RECONNECT_INTERVAL_MS = 2000

# Control change numbers for the encoders. Relative values: 1-63 is that
# many steps clockwise, 65-127 anticlockwise (127 is one step back).
ENCODER_CCS = {
    1: "tempo",
    2: "jog",
}

# Note numbers for the buttons: note on when pressed, note off when
# released.
BUTTON_NOTES = {
    60: "play",
    61: "vocals",
    62: "drums",
    63: "instrumental",
}


class MidiControls(QObject):
    # Emitted on mido's thread, delivered on the Qt main thread.
    encoder_turned = Signal(str, int)
    button_changed = Signal(str, bool)

    def __init__(self, app):
        super().__init__()

        self.app = app
        self.port = None
        self.port_name = None

        self.encoder_turned.connect(app.handle_turn)
        self.button_changed.connect(app.handle_button)

        # The Pico can be plugged in after the player starts, or pulled
        # out mid-set, so keep checking rather than looking once.
        self.reconnect_timer = QTimer(self)
        self.reconnect_timer.timeout.connect(self.check_connection)
        self.reconnect_timer.start(RECONNECT_INTERVAL_MS)

        self.check_connection()

        if self.port is None:
            print("Controls: no MIDI controller plugged in (that is fine)")

    # =====================================================
    # CONNECTION
    # =====================================================

    @staticmethod
    def find_port(names):
        for name in names:
            lowered = name.lower()

            # ALSA always lists a loopback port, which is never us.
            if "through" in lowered:
                continue

            if any(keyword in lowered for keyword in PORT_KEYWORDS):
                return name

        return None

    def check_connection(self):
        try:
            names = mido.get_input_names()
        except Exception as e:
            print("Controls: cannot list MIDI inputs:", e)
            return

        if self.port is not None:
            if self.port_name in names:
                return

            self.disconnected()

        name = self.find_port(names)

        if name is None:
            return

        try:
            self.port = mido.open_input(name, callback=self.on_message)
        except Exception as e:
            print("Controls: could not open", name, "-", e)
            self.port = None
            return

        self.port_name = name
        print("Controls: connected to", name)

    def disconnected(self):
        print("Controls: disconnected from", self.port_name)

        self.close_port()

        # A button held at the moment the cable came out would otherwise
        # never send its release.
        self.app.release_all()

    def close_port(self):
        if self.port is not None:
            try:
                self.port.close()
            except Exception:
                pass

        self.port = None
        self.port_name = None

    # =====================================================
    # INCOMING MESSAGES (mido's thread - no Qt calls here)
    # =====================================================

    def on_message(self, message):
        if message.type == "control_change":
            name = ENCODER_CCS.get(message.control)

            if name is None:
                return

            # Relative encoding: 1-63 clockwise, 65-127 anticlockwise.
            value = message.value
            steps = value if value < 64 else value - 128

            if steps:
                self.encoder_turned.emit(name, steps)

        elif message.type in ("note_on", "note_off"):
            name = BUTTON_NOTES.get(message.note)

            if name is None:
                return

            # By MIDI convention a note-on with velocity 0 is a release.
            pressed = message.type == "note_on" and message.velocity > 0

            self.button_changed.emit(name, pressed)

    # =====================================================
    # CLEANUP
    # =====================================================

    def close(self):
        self.reconnect_timer.stop()
        self.close_port()
