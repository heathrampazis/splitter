import time
import subprocess
import threading
from pathlib import Path

import numpy as np
import sounddevice as sd


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

    def audio_callback(self, outdata, frames, time_info, status):
        output = np.zeros((frames, 2), dtype=np.float32)

        with self.lock:
            playing = self.playing
            position = self.position
            searching = self.searching
            search_speed = self.search_speed
            playback_speed = self.playback_speed
            jog = self.jog_adjustment
            stems = dict(self.stems)
            volumes = dict(self.volumes)
            length = self.length

        if not stems:
            outdata[:] = output
            return

        if searching != 0:
            position += searching * search_speed
            position = max(0.0, min(position, max(0, length - 1)))

        if playing and length > 0:
            speed = max(0.01, playback_speed * (1 + jog))

            indexes = position + np.arange(frames) * speed
            indexes = indexes.astype(np.int64)

            for name, audio in stems.items():
                if len(audio) == 0:
                    continue

                safe_indexes = np.clip(indexes, 0, len(audio) - 1)
                chunk = audio[safe_indexes]
                volume = volumes.get(name, 1.0)
                output += chunk * volume

            position += frames * speed

            if position >= length:
                position = 0.0
                playing = False

        with self.lock:
            self.position = position
            self.playing = playing

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