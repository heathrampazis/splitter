"""
Physical controls, kept optional.

The player is touch-first: it runs on a bare Raspberry Pi with nothing
but a screen attached. Buttons and encoders are an upgrade. They are
wired to a Raspberry Pi Pico 2 W, which plugs into the Pi over USB and
sends everything as MIDI (see hardware/firmware/ and the README). When
it is plugged in, it drives the same audio engine the on-screen controls
do, so the two stay in step.

Nothing here is required for the app to work. If the MIDI library is
missing, attach() reports why and returns None, and the player carries
on as a touch device. The Pico itself can be plugged in or pulled out at
any time while the player is running.
"""

# "auto"  - use the Pico whenever it is plugged in, touch otherwise
# "midi"  - require the MIDI library, fail loudly if it is missing
# "touch" - ignore the Pico even when it is plugged in
MODE = "auto"


# Starts listening for the Pico, if controls are enabled.
#
# Returns a MidiControls object, or None when running touch-only.
def attach(app):
    if MODE == "touch":
        print("Controls: touch only (disabled in controls/__init__.py)")
        return None

    try:
        from controls.midi_controls import MidiControls

        controls = MidiControls(app)

    except Exception as e:
        if MODE == "midi":
            print("Controls: required but unavailable.")
            raise

        # Normally means mido or python-rtmidi is not installed. Not an
        # error for a touch-only build, so say what happened and move on.
        print(f"Controls: touch only ({type(e).__name__}: {e})")
        return None

    return controls
