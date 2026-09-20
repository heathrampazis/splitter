import librosa
import numpy as np
from PIL import Image, ImageDraw
from pathlib import Path

# Creates the waveform images for a song
class WaveformGenerator:
    def create(self, input_file, output_folder):
        output_folder = Path(output_folder)
        output_folder.mkdir(exist_ok=True)
        
        # Different resolutions
        sizes = {"overview": 2500, "medium": 10000, "detail": 25000}
        HEIGHT = 180
        BACKGROUND = (10, 10, 15)
        WAVEFORM = (60, 150, 255)

        # Loads audio file
        print("Loading audio...")
        audio, sr = librosa.load(input_file, mono=True)
        
        # Generates waveform images
        print("Generating waveforms...")
        for name, width in sizes.items():
            print("Creating", name, width)
            image = self.create_image(audio, width, HEIGHT, BACKGROUND, WAVEFORM)
            filename = output_folder / f"waveform_{name}.png"
            image.save(filename)
            print("Saved:", filename)
        print("Complete")

    # Creates waveform image
    def create_image(self, audio, width, height, background, waveform_colour):
        samples_per_pixel = max(1, len(audio) // width)
        levels = []
        for x in range(width):
            start = x * samples_per_pixel
            end = start + samples_per_pixel
            chunk = audio[start:end]
            if len(chunk) == 0:
                levels.append(0)
                continue
            rms = np.sqrt(np.mean(chunk ** 2))
            peak = np.max(np.abs(chunk))
            level = rms * 0.6 + peak * 0.4
            levels.append(level)
        maximum = max(levels)
        if maximum:
            levels = [x / maximum for x in levels]
        image = Image.new("RGB", (width, height), background)
        draw = ImageDraw.Draw(image)
        centre = height // 2
        for x, level in enumerate(levels):
            bar_height = int(level * height / 2)
            draw.rectangle((x, centre-bar_height, x+1, centre+bar_height), fill=waveform_colour)
        return image