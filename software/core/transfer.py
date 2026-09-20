from pathlib import Path
import shutil

# Copies the combined track files to the destination folder
class TransferManager:
    def copy_track(self, source_folder, destination_folder):
        source_folder = Path(source_folder)
        destination_folder = Path(destination_folder)
        if not destination_folder.exists():
            raise Exception("Destination folder does not exist")
        track_folder = destination_folder / source_folder.name
        track_folder.mkdir(parents=True, exist_ok=True)
        for item in source_folder.iterdir():
            destination = track_folder / item.name
            if item.is_file():
                shutil.copy2(item, destination)
        return track_folder