from PySide6.QtCore import QObject, Signal, QThread
from core.worker import Worker

# Manages the processing queue and runs each job in its own thread.
class QueueManager(QObject):
    job_added = Signal(str)
    job_started = Signal(str)
    job_finished = Signal(str)
    job_failed = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.queue = []
        self.current_job = None
        self.thread = None
        self.worker = None

    def add_job(self, audio_file):
        self.queue.append(audio_file)
        self.job_added.emit(audio_file)
        self.start_next()

    def start_next(self):
        # Don't start another job while one is already running.
        if self.current_job:
            return

        if not self.queue:
            return

        self.current_job = self.queue.pop(0)
        self.job_started.emit(self.current_job)

        # Run the worker in a separate thread so the UI stays responsive.
        self.thread = QThread()
        self.worker = Worker(self.current_job)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.job_complete)
        self.worker.error.connect(self.job_error)

        # Stop the thread when the worker finishes or encounters an error.
        self.worker.finished.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)

        # Clean up once the thread has fully stopped.
        self.thread.finished.connect(self.cleanup)
        self.thread.start()

    def job_complete(self):
        finished_file = self.current_job
        self.job_finished.emit(finished_file)

    def job_error(self, message):
        failed_file = self.current_job
        self.job_failed.emit(failed_file, message)

    def cleanup(self):
        if self.worker:
            self.worker.deleteLater()

        if self.thread:
            self.thread.deleteLater()

        self.worker = None
        self.thread = None
        self.current_job = None

        # Start the next queued track.
        self.start_next()