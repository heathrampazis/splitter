from pathlib import Path
import subprocess
import shutil

# Separates an audio file into individual stems using Demucs.
class Separator:
    def split(self, input_file):
        input_file = Path(input_file)
        output_root = Path("output")
        output_root.mkdir(exist_ok=True)

        # Create a folder for this song's processed files.
        song_folder = output_root / input_file.stem
        song_folder.mkdir(exist_ok=True)

        # Demucs uses a temporary folder for its output.
        temp_folder = output_root / "temp"
        temp_folder.mkdir(exist_ok=True)

        # Run Demucs to separate the audio into stems.
        subprocess.run(["python3", "-m", "demucs", "--out", str(temp_folder), str(input_file)], check=True)

        demucs_output = temp_folder / "htdemucs" / input_file.stem
        stems = ["vocals.wav", "drums.wav", "bass.wav", "other.wav"]

        # Move the generated stems into the song's output folder.
        for stem in stems:
            source = demucs_output / stem
            destination = song_folder / stem
            if source.exists():
                shutil.move(source, destination)

        # Remove the temporary Demucs output.
        shutil.rmtree(temp_folder, ignore_errors=True)

        return song_folder