"""
Runs once when the Pico powers up, before code.py.

Gives the Pico a recognisable USB name so the player on the Pi can pick
it out from any other MIDI device. Changes here only take effect after
unplugging the Pico and plugging it back in: saving code.py restarts
code.py, but not this file.
"""

import usb_midi

# Shows as "StemDeck Controls" in `amidi -l`, `aconnect -l` and mido.
# Both calls are wrapped because older CircuitPython releases lack them;
# the player also recognises the default "CircuitPython" name.
try:
    import supervisor

    supervisor.set_usb_identification("StemDeck", "StemDeck Controls")
except Exception:
    pass

try:
    usb_midi.set_names(
        streaming_interface_name="StemDeck Controls",
        audio_control_interface_name="StemDeck Controls",
        in_jack_name="StemDeck in",
        out_jack_name="StemDeck out",
    )
except Exception:
    pass

usb_midi.enable()
