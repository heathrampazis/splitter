import math
import time
import subprocess
import threading
from pathlib import Path

import numpy as np
import sounddevice as sd


# Dragging the waveform plays the track at whatever speed and direction
# the finger moves, like spinning a CDJ's jog wheel in vinyl mode.
#   SCRUB_FOLLOW_SECONDS  how quickly the sound catches up with the finger
#   SCRUB_MAX_SPEED       fastest it plays, forwards or backwards (x normal)
#   COAST_SECONDS         after a flick, how long it takes to wind back to
#                         normal speed (or to a stop, when paused)
SCRUB_FOLLOW_SECONDS = 0.06
SCRUB_MAX_SPEED = 16.0
COAST_SECONDS = 0.35


class AudioEngine:

    def __init__(self):
        # Audio settings
        self.sample_rate = 44100
        self.channels = 2
        self.output_device = self.find_usb_audio_device()

        print("Audio output device:", self.output_device)

        # Stems
        self.stems = {}
        self.volumes = {"drums": 1.0, "bass": 1.0, "vocals": 1.0, "other": 1.0}

        # Playback
        self.position = 0.0
        self.length = 0
        self.playing = False

        # Search
        self.searching = 0
        self.search_speed = 5000

        # BPM
        self.original_bpm = 138

        # Tempo
        self.playback_speed = 1.0

        # Jog
        self.jog_adjustment = 0.0

        # Dragging the waveform. While scrub_target is set, the sound
        # chases it; scrub_speed is the speed it is playing at right now
        # (negative is backwards). coast_speed is set after a flick and
        # winds back down to normal.
        self.scrub_target = None
        self.scrub_speed = 0.0
        self.coast_speed = None

        # Thread safety
        self.lock = threading.Lock()

        # Audio stream
        self.stream = sd.OutputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            device=self.output_device,
            blocksize=1024,
            dtype="float32",
            callback=self.audio_callback
        )

        print("Audio stream created.")

    def find_usb_audio_device(self):
        try:
            devices = sd.query_devices()

            for index, device in enumerate(devices):
                name = device.get("name", "")
                outputs = device.get("max_output_channels", 0)

                if outputs > 0 and "USB" in name.upper():
                    print("Found USB audio:", index, name)
                    return index

            default_device = sd.default.device
            default_output = default_device[1] if isinstance(default_device, (list, tuple)) else default_device

            print("USB audio not found.")
            print("Using default output:", default_output)

            return default_output

        except Exception as e:
            print("Audio device detection error:", e)
            return None

    def find_audio_file(self, folder, stem):
        folder = Path(folder)

        for ext in [".wav", ".mp3", ".aif", ".aiff"]:
            filename = folder / f"{stem}{ext}"

            if filename.exists():
                return filename

        return None

    def decode_audio(self, filename):
        print("Decoding:", filename)

        command = [
            "ffmpeg",
            "-v", "error",
            "-i", str(filename),
            "-f", "f32le",
            "-ac", "2",
            "-ar", str(self.sample_rate),
            "pipe:1"
        ]

        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )

        except FileNotFoundError:
            print("ERROR: ffmpeg is not installed.")
            print("Install it with: sudo apt install ffmpeg")
            return None

        except subprocess.CalledProcessError as e:
            print("FFmpeg error:")
            print(e.stderr.decode(errors="ignore"))
            return None

        if not result.stdout:
            print("FFmpeg returned no audio.")
            return None

        audio = np.frombuffer(result.stdout, dtype=np.float32)

        try:
            return audio.reshape((-1, 2))
        except ValueError:
            print("Invalid decoded audio shape.")
            return None

    def load_song(self, folder):
        print()
        print("================================")
        print("Loading song:")
        print(folder)
        print("================================")

        self.playing = False

        with self.lock:
            self.stems.clear()

        longest = 0

        for stem in ["drums", "bass", "vocals", "other"]:
            filename = self.find_audio_file(folder, stem)

            if filename is None:
                print("Missing stem:", stem)
                continue

            audio = self.decode_audio(filename)

            if audio is None:
                print("Could not load:", filename)
                continue

            print(stem, "frames:", len(audio))

            with self.lock:
                self.stems[stem] = audio

            longest = max(longest, len(audio))

        if longest <= 0:
            self.length = 0
            print("ERROR: No audio stems loaded.")
            return

        self.length = longest
        self.position = 0.0

        print("Loaded stems:", list(self.stems.keys()))
        print("Length:", self.length, "frames")
        print("Length:", round(self.length / self.sample_rate, 2), "seconds")

    def play(self):
        if self.length <= 0:
            print("No song loaded.")
            return

        try:
            if not self.stream.active:
                self.stream.start()

        except Exception as e:
            print("Could not start audio stream:", e)
            return

        with self.lock:
            self.playing = True

        print("PLAY")

    def pause(self):
        with self.lock:
            self.playing = False

        print("PAUSE")

    def toggle_play(self):
        if self.playing:
            self.pause()
        else:
            self.play()

    def restart(self):
        with self.lock:
            self.position = 0.0

        print("RESTART")

    def stop(self):
        with self.lock:
            self.playing = False
            self.position = 0.0

        print("STOP")

    def set_volume(self, stem, value):
        value = max(0.0, min(float(value), 1.0))

        if stem in self.volumes:
            with self.lock:
                self.volumes[stem] = value

            print(stem, "volume:", round(value, 2))

    def get_volume(self, stem):
        return self.volumes.get(stem, 1.0)

    def set_search_speed(self, value):
        self.search_speed = value

    def start_search(self, direction):
        self.searching = direction

    def stop_search(self):
        self.searching = 0

    def set_tempo(self, value):
        self.playback_speed = max(0.01, 1.0 + float(value) / 100.0)

    def set_jog(self, value):
        self.jog_adjustment = float(value)

    def get_jog(self):
        return round(self.jog_adjustment * 100, 2)

    def get_current_bpm(self):
        speed = self.playback_speed * (1 + self.jog_adjustment)
        return round(self.original_bpm * speed, 1)

    def get_time_info(self):
        with self.lock:
            position = self.position
            length = self.length

        current = position / self.sample_rate
        total = length / self.sample_rate
        remaining = max(0, total - current)

        return current, remaining, total

    # Jumps to a point in the track, in seconds. Used when the waveform
    # is dragged on screen.
    def set_position(self, seconds):
        with self.lock:
            if self.length <= 0:
                return

            frame = float(seconds) * self.sample_rate
            self.position = max(0.0, min(frame, self.length - 1))

    # Moves the play position by a number of seconds, forwards or back.
    # Used by the jog wheel to cue while paused.
    def nudge_position(self, seconds):
        with self.lock:
            if self.length <= 0:
                return

            frame = self.position + float(seconds) * self.sample_rate
            self.position = max(0.0, min(frame, self.length - 1))

    # ---- dragging the waveform ----

    def start_stream(self):
        try:
            if not self.stream.active:
                self.stream.start()
            return True
        except Exception as e:
            print("Could not start audio stream:", e)
            return False

    # A finger has gone down on the waveform.
    def scrub_begin(self):
        if self.length <= 0 or not self.start_stream():
            return

        with self.lock:
            self.scrub_target = self.position
            self.scrub_speed = 0.0
            self.coast_speed = None

    # Where the finger has moved the track to, in seconds.
    def scrub_to(self, seconds):
        with self.lock:
            if self.scrub_target is None or self.length <= 0:
                return

            frame = float(seconds) * self.sample_rate
            self.scrub_target = max(0.0, min(frame, self.length - 1))

    # The finger has lifted. fling is how fast it was moving, as a
    # multiple of normal speed (negative is backwards); playing says
    # whether to carry on playing afterwards.
    def scrub_end(self, fling, playing):
        with self.lock:
            self.scrub_target = None
            self.playing = bool(playing) and self.length > 0

            fling = max(-SCRUB_MAX_SPEED, min(SCRUB_MAX_SPEED, float(fling)))
            self.coast_speed = fling if abs(fling) > 0.5 else None
            self.scrub_speed = 0.0

    # Mixes the stems from position, with the speed sliding from
    # start_speed to end_speed across the block. Returns the audio and
    # the position afterwards.
    def render(self, stems, volumes, position, frames, start_speed, end_speed,
               length):
        output = np.zeros((frames, 2), dtype=np.float32)

        speeds = np.linspace(start_speed, end_speed, frames, endpoint=False)
        steps = np.cumsum(speeds) - speeds
        indexes = (position + steps).astype(np.int64)

        for name, audio in stems.items():
            if len(audio) == 0:
                continue

            chunk = audio[np.clip(indexes, 0, len(audio) - 1)]
            output += chunk * volumes.get(name, 1.0)

        position += float(np.sum(speeds))
        return output, max(0.0, min(position, max(0, length - 1)))

    def audio_callback(self, outdata, frames, time_info, status):
        with self.lock:
            playing = self.playing
            start_playing = playing
            position = self.position
            start_position = position
            playback_speed = self.playback_speed
            jog = self.jog_adjustment
            stems = dict(self.stems)
            volumes = dict(self.volumes)
            length = self.length
            target = self.scrub_target
            scrub_speed = self.scrub_speed
            coast_speed = self.coast_speed

        if not stems or length <= 0:
            outdata[:] = 0
            return

        normal = max(0.01, playback_speed * (1 + jog))

        if target is not None:
            # Play towards the finger: the further behind, the faster.
            wanted = (target - position) / (self.sample_rate * SCRUB_FOLLOW_SECONDS)
            wanted = max(-SCRUB_MAX_SPEED, min(SCRUB_MAX_SPEED, wanted))
            new_speed = scrub_speed + (wanted - scrub_speed) * 0.5

            output, position = self.render(stems, volumes, position, frames,
                                           scrub_speed, new_speed, length)
            scrub_speed = new_speed

        elif coast_speed is not None:
            # After a flick: wind back to normal speed, or to a stop.
            rest = normal if playing else 0.0
            fade = math.exp(-frames / (self.sample_rate * COAST_SECONDS))
            new_speed = rest + (coast_speed - rest) * fade

            output, position = self.render(stems, volumes, position, frames,
                                           coast_speed, new_speed, length)
            coast_speed = None if abs(new_speed - rest) < 0.02 else new_speed

        elif playing:
            output, position = self.render(stems, volumes, position, frames,
                                           normal, normal, length)

            if position >= length - 1:
                position = 0.0
                playing = False
        else:
            outdata[:] = 0
            return

        with self.lock:
            # If the position was moved while this block was being mixed
            # (a tap on the overview, say), keep that instead.
            if self.position == start_position:
                self.position = position

            # Only the end of the track changes playing here; leave a
            # press of play that came in meanwhile alone.
            if playing != start_playing:
                self.playing = playing

            if target is not None and self.scrub_target is not None:
                self.scrub_speed = scrub_speed

            # Same for a new drag or a flick that started meanwhile.
            if target is None and self.scrub_target is None:
                self.coast_speed = coast_speed

        outdata[:] = np.clip(output, -1.0, 1.0)

    def close(self):
        with self.lock:
            self.playing = False

        try:
            if self.stream.active:
                self.stream.stop()

            self.stream.close()

        except Exception as e:
            print("Audio stream close error:", e)