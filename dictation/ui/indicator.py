"""Status indicator using libnotify."""

import subprocess
import shutil


def notify_available() -> bool:
    return shutil.which("notify-send") is not None


class StatusIndicator:
    def __init__(self):
        self._current_status = "idle"

    def set_status(self, status: str) -> None:
        if status == self._current_status:
            return
        self._current_status = status

        if not notify_available():
            return

        messages = {
            "recording": ("Dictation", "Recording...", 3000),
            "transcribing": ("Dictation", "Processing...", 3000),
            "idle": ("Dictation", "Done", 1500),
        }

        if status in messages:
            title, body, timeout = messages[status]
            subprocess.Popen(
                ["notify-send", "-t", str(timeout), title, body],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
