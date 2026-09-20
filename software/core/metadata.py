import json
from pathlib import Path
import librosa

# Generates metadata for each processed track.
class MetadataGenerator:

    # Detects the song's BPM and adjusts it to a likely range.
    def detect_bpm(self, filename):
        print("Analysing BPM...")
        y, sr = librosa.load(filename, sr=44100, mono=True)

        # Remove silence before analysing the beat.
        y, _ = librosa.effects.trim(y)
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)

        # Handles different librosa versions.
        if hasattr(tempo, "__len__"):
            bpm = float(tempo[0])
        else:
            bpm = float(tempo)

        # Try common BPM multiples/halves to find a more likely tempo.
        candidates = [bpm, bpm * 2, bpm / 2, bpm * 1.5, bpm / 1.5]
        valid = [x for x in candidates if 70 <= x <= 180]

        # Prefer a BPM closest to 128 when multiple valid options exist.
        if valid:
            final_bpm = min(valid, key=lambda x: abs(x - 128))
        else:
            final_bpm = bpm

        print("Detected BPM:", round(final_bpm))
        return round(final_bpm)

    # Creates the metadata.json file for the track.
    def create(self, audio_file, output_folder):
        audio_file = Path(audio_file)
        output_folder = Path(output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)

        bpm = self.detect_bpm(audio_file)
        duration = librosa.get_duration(path=audio_file)

        metadata = {
            "title": audio_file.stem,
            "source_file": audio_file.name,
            "bpm": bpm,
            "duration": round(duration, 2),
            "stems": ["vocals.wav", "drums.wav", "bass.wav", "other.wav"]
        }

        metadata_file = output_folder / "metadata.json"

        print("Writing metadata...")

        with open(metadata_file, "w") as file:
            json.dump(metadata, file, indent=4)

        print("Metadata saved:")
        print(metadata_file)

        return metadata_file