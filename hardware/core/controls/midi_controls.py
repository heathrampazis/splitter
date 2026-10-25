"""
Physical controls, arriving as USB MIDI from the Pico.

The buttons and encoders are wired to a Raspberry Pi Pico 2 W running
the firmware in hardware/firmware/. It plugs into the Pi over USB and
shows up as a MIDI device, so nothing here knows about pins: it only
reads MIDI messages. That also means any MIDI controller sending the
same messages works, which is handy when developing on a laptop.

Threading: mido delivers messages on its own background thread, and Qt
widgets must only be touched from the main thread. Every message is
therefore turned into a Qt signal, which Qt queues across to the main
thread before any handler runs.
"""

import mido
from PySide6.QtCore import QObject, QTimer, Signal

# Any MIDI input whose name contains one of these is taken to be the
# Pico. "StemDeck" is the name boot.py gives it; the others are what it
# is called if boot.py has not run.
PORT_KEYWORDS = ("stemdeck", "circuitpython", "pico")

# How often to look for the controller being plugged in or pulled out.
RECONNECT_INTERVAL_MS = 2000

# Must match ENCODERS and BUTTONS in firmware/code.py.
ENCODER_CCS = {
    1: "tempo",
    2: "vocals",
    3: "drums",
    4: "bass_other",
}

BUTTON_NOTES = {
    60: "play",
    61: "search_back",
    62: "search_forward",
}

# How far one encoder click moves things.
#   Tempo:  slider units of 0.1 %, so 2 is 0.2 % per click and a full
#           sweep of +/-8 % takes 80 clicks, about four turns.
#   Volume: fraction of full scale, so 0.05 is 5 % per click and a
#           20-click encoder goes from silent to full in one turn.
TEMPO_STEP = 2
VOLUME_STEP = 0.05


class MidiControls(QObject):
    # Emitted on mido's thread, delivered on the Qt main thread.
    encoder_turned = Signal(str, int)
    button_changed = Signal(str, bool)

    def __init__(self, app):
        super().__init__()

        self.app = app
        self.port = None
        self.port_name = None

        self.encoder_turned.connect(self.handle_encoder)
        self.button_changed.connect(self.handle_button)

        # The Pico can be plugged in after the player starts, or pulled
        # out mid-set, so keep checking rather than looking once.
        self.reconnect_timer = QTimer(self)
        self.reconnect_timer.timeout.connect(self.check_connection)
        self.reconnect_timer.start(RECONNECT_INTERVAL_MS)

        self.check_connection()

        if self.port is None:
            print("Controls: waiting for the Pico to be plugged in")

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

        # A search button held at the moment the cable came out would
        # otherwise never send its release, and the track would keep
        # scrubbing forever.
        self.app.engine.stop_search()

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
    # HANDLERS (Qt main thread)
    # =====================================================

    def handle_encoder(self, name, steps):
        if name == "tempo":
            self.app.nudge_tempo(steps * TEMPO_STEP)
        else:
            self.app.nudge_stem(name, steps * VOLUME_STEP)

    def handle_button(self, name, pressed):
        engine = self.app.engine

        if name == "play":
            if pressed:
                engine.toggle_play()

        elif name == "search_back":
            if pressed:
                engine.start_search(-1)
            else:
                engine.stop_search()

        elif name == "search_forward":
            if pressed:
                engine.start_search(1)
            else:
                engine.stop_search()

    # =====================================================
    # CLEANUP
    # =====================================================

    def close(self):
        self.reconnect_timer.stop()
        self.close_port()
