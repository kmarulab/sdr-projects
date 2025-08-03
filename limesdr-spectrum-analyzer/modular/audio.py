# audio.py
"""Handles audio output using the sounddevice library."""

from __future__ import annotations
import sounddevice as sd
import numpy as np
from shared_state import AppState
import config

class AudioManager:
    """Manages the audio output stream and callback."""
    def __init__(self, state: AppState):
        self.state = state
        self.stream = None

    def _callback(self, outdata: np.ndarray, frames: int, *_):
        """Pulls audio chunks from the shared buffer to feed the sound card."""
        required = frames
        chunks = []
        with self.state.lock:
            while required > 0 and self.state.audio_buffer:
                chunk = self.state.audio_buffer.popleft()
                self.state.audio_buffer_samples -= len(chunk)
                if len(chunk) <= required:
                    chunks.append(chunk)
                    required -= len(chunk)
                else:
                    chunks.append(chunk[:required])
                    self.state.audio_buffer.appendleft(chunk[required:])
                    self.state.audio_buffer_samples += len(chunk) - required
                    required = 0
        
        if required > 0:
            chunks.append(np.zeros(required, np.float32))
            
        outdata[:, 0] = np.concatenate(chunks) if chunks else np.zeros(frames, np.float32)

    def start(self):
        """Waits for the initial buffer to fill, then starts the audio stream."""
        print("Buffering audio...")
        self.state.start_audio.wait()
        print("Starting audio playback...")
        self.stream = sd.OutputStream(
            samplerate=config.FS_AUDIO_OUT, blocksize=config.BLOCK,
            channels=1, callback=self._callback, dtype='float32'
        )
        self.stream.start()

    def stop(self):
        """Stops and closes the audio stream."""
        if self.stream:
            self.stream.stop()
            self.stream.close()