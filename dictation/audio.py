"""Audio capture using sounddevice."""

import numpy as np
import sounddevice as sd
from threading import Lock
from typing import Callable

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = np.float32


class AudioRecorder:
    def __init__(self):
        self._buffer: list[np.ndarray] = []
        self._lock = Lock()
        self._stream: sd.InputStream | None = None
        self._recording = False
        self._chunk_callback: Callable[[np.ndarray], None] | None = None
        self._chunk_samples = 0
        self._samples_since_chunk = 0

    def _callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:
        if status:
            print(f"Audio status: {status}")
        with self._lock:
            if self._recording:
                self._buffer.append(indata.copy())

                if self._chunk_callback and self._chunk_samples > 0:
                    self._samples_since_chunk += frames
                    if self._samples_since_chunk >= self._chunk_samples:
                        audio = np.concatenate(self._buffer, axis=0).flatten()
                        self._samples_since_chunk = 0
                        self._chunk_callback(audio)

    def start(self, chunk_callback: Callable[[np.ndarray], None] | None = None, chunk_seconds: float = 0) -> None:
        with self._lock:
            self._buffer.clear()
            self._recording = True
            self._chunk_callback = chunk_callback
            self._chunk_samples = int(chunk_seconds * SAMPLE_RATE) if chunk_seconds > 0 else 0
            self._samples_since_chunk = 0

        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE,
            callback=self._callback,
        )
        self._stream.start()

    def stop(self) -> np.ndarray:
        with self._lock:
            self._recording = False
            self._chunk_callback = None

        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        with self._lock:
            if not self._buffer:
                return np.array([], dtype=DTYPE)
            audio = np.concatenate(self._buffer, axis=0).flatten()
            self._buffer.clear()
            return audio

    def get_audio_so_far(self) -> np.ndarray:
        with self._lock:
            if not self._buffer:
                return np.array([], dtype=DTYPE)
            return np.concatenate(self._buffer, axis=0).flatten()

    @property
    def is_recording(self) -> bool:
        return self._recording


_recorder: AudioRecorder | None = None


def get_recorder() -> AudioRecorder:
    global _recorder
    if _recorder is None:
        _recorder = AudioRecorder()
    return _recorder
