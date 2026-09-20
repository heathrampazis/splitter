import time
import threading

from gpiozero import Button, RotaryEncoder


class GPIOController:

    def __init__(self, engine):
        self.engine = engine

        self.jog_direction = 0
        self.jog_strength = 0.0
        self.jog_max = 0.25
        self.jog_acceleration = 0.01

        self.play_button = Button(17, pull_up=True)
        self.search_back = Button(0, pull_up=True)
        self.search_forward = Button(11, pull_up=True)
        self.jog_left = Button(27, pull_up=True)
        self.jog_right = Button(22, pull_up=True)

        self.play_button.when_pressed = self.engine.toggle_play

        self.search_back.when_pressed = (
            lambda: self.engine.start_search(-1)
        )

        self.search_back.when_released = (
            self.engine.stop_search
        )

        self.search_forward.when_pressed = (
            lambda: self.engine.start_search(1)
        )

        self.search_forward.when_released = (
            self.engine.stop_search
        )

        self.jog_left.when_pressed = (
            lambda: self.start_jog(-1)
        )

        self.jog_left.when_released = (
            self.stop_jog
        )

        self.jog_right.when_pressed = (
            lambda: self.start_jog(1)
        )

        self.jog_right.when_released = (
            self.stop_jog
        )

        self.jog_loop_running = True

        self.jog_thread = threading.Thread(
            target=self.jog_loop,
            daemon=True
        )

        self.jog_thread.start()

    def start_jog(self, direction):
        self.jog_direction = direction

    def stop_jog(self):
        self.jog_direction = 0

    def jog_loop(self):

        while self.jog_loop_running:

            if self.jog_direction != 0:

                self.jog_strength = min(
                    self.jog_strength +
                    self.jog_acceleration,
                    self.jog_max
                )

                self.engine.set_jog(
                    self.jog_strength *
                    self.jog_direction
                )

            elif self.jog_strength > 0:

                self.jog_strength = max(
                    self.jog_strength -
                    self.jog_acceleration * 2,
                    0
                )

                self.engine.set_jog(
                    self.jog_strength
                )

            else:

                self.engine.set_jog(0)

            time.sleep(0.02)


class StemEncoder:

    def __init__(
        self,
        app,
        gpio_a,
        gpio_b,
        stem
    ):

        self.app = app
        self.stem = stem
        self.volume = 1.0

        self.encoder = RotaryEncoder(
            a=gpio_a,
            b=gpio_b,
            max_steps=0
        )

        self.last_steps = 0

        self.encoder.when_rotated = (
            self.changed
        )

    def changed(self):

        current_steps = self.encoder.steps

        difference = (
            current_steps -
            self.last_steps
        )

        self.last_steps = current_steps

        change = 0.1

        if difference > 0:
            self.volume += change

        elif difference < 0:
            self.volume -= change

        self.volume = max(
            0,
            min(
                1,
                self.volume
            )
        )

        print(
            self.stem,
            round(
                self.volume,
                2
            )
        )

        if self.stem == "bass_other":

            self.app.engine.set_volume(
                "bass",
                self.volume
            )

            self.app.engine.set_volume(
                "other",
                self.volume
            )

        else:

            self.app.engine.set_volume(
                self.stem,
                self.volume
            )

        self.app.update_stem_slider(
            self.stem,
            self.volume
        )


class TempoEncoder:

    def __init__(self, app):

        self.app = app

        self.encoder = RotaryEncoder(
            a=1,
            b=7,
            max_steps=80
        )

        self.encoder.when_rotated = (
            self.changed
        )

    def changed(self):

        value = self.encoder.steps

        print(
            "Tempo:",
            value
        )

        self.app.change_tempo_encoder(
            value
        )