"""
Physical controls.

The buttons and encoders are wired to the Raspberry Pi's GPIO header
(gpio_controls.py). A USB MIDI controller can be used as well
(midi_controls.py), which also makes it possible to try the player on a
laptop. Both send the same actions to the main window:

    handle_button(name, pressed)   play, vocals, drums, instrumental
    handle_turn(name, steps)       tempo, jog

Nothing here is required for the player to start. If a kind of control
cannot be set up - no GPIO on a laptop, no MIDI library - attach() says
why and carries on without it.
"""

# Set either to False to switch that kind of control off.
USE_GPIO = True
USE_MIDI = True


class Controls:
    def __init__(self, parts):
        self.parts = parts

    def close(self):
        for part in self.parts:
            try:
                part.close()
            except Exception:
                pass


def attach(app):
    parts = []

    if USE_GPIO:
        try:
            from controls.gpio_controls import GPIOControls

            parts.append(GPIOControls(app))

        except Exception as e:
            # The normal case on a laptop: there is no GPIO header.
            print(f"Controls: no GPIO ({type(e).__name__}: {e})")

    if USE_MIDI:
        try:
            from controls.midi_controls import MidiControls

            parts.append(MidiControls(app))

        except Exception as e:
            print(f"Controls: no MIDI ({type(e).__name__}: {e})")

    if not parts:
        print("Controls: touch screen only")

    return Controls(parts)
