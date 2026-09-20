from PySide6.QtCore import QObject, Signal
from core.separator import Separator
from core.waveform import WaveformGenerator
from core.metadata import MetadataGenerator

# Processes the audio of a song
class Worker(QObject):
    finished = Signal()
    error = Signal(str)

    def __init__(self, audio_file):
        super().__init__()
        self.audio_file = audio_file
        self.separator = Separator()
        self.waveform = WaveformGenerator()
        self.metadata = MetadataGenerator()

    def run(self):
        try:
            print("Processing:")
            print(self.audio_file)
            
            # Create stems
            song_folder = self.separator.split(self.audio_file)
            
            # Create metadata
            self.metadata.create(self.audio_file, song_folder)
            
            # Create waveforms
            self.waveform.create(self.audio_file, song_folder)
            print("Finished:")
            print(self.audio_file)
            self.finished.emit()
        except Exception as e:
            print("ERROR:")
            print(e)
            self.error.emit(str(e))