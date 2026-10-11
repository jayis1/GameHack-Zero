"""Cancelable, bounded output collection for the handheld OpenCode client."""
import os
import signal
import subprocess
import threading
import time


class PromptJob:
    def __init__(self, command, directory):
        self.output = ""
        self.process = subprocess.Popen(command, cwd=directory, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, start_new_session=True,
                                        env=dict(os.environ, NO_COLOR="1", TERM="dumb"))
        self.started = time.monotonic()
        self.done = threading.Event()
        threading.Thread(target=self.collect, daemon=True).start()

    def collect(self):
        try:
            while True:
                chunk = os.read(self.process.stdout.fileno(), 4096)
                if not chunk:
                    break
                self.output = (self.output + chunk.decode("utf-8", errors="replace"))[-32768:]
        finally:
            self.process.stdout.close()
            self.process.wait()
            self.done.set()

    def cancel(self):
        if not self.done.is_set():
            try:
                os.killpg(self.process.pid, signal.SIGTERM)
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(self.process.pid, signal.SIGKILL)
                self.process.wait()
            except ProcessLookupError:
                pass
