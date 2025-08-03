# shared_state.py
"""Manages the shared state between SDR, audio, and GUI threads."""

from __future__ import annotations
import threading
from collections import deque
import numpy as np
import config

class AppState:
    """A container for state shared across application threads."""
    def __init__(self, center_freq_mhz: float, volume: float):
        # Thread synchronization primitives
        self.lock = threading.Lock()
        self.start_audio = threading.Event()
        self.stop_event = threading.Event()

        # Shared data buffers and parameters
        self.audio_buffer: deque[np.ndarray] = deque()
        self.audio_buffer_samples = 0
        self.latest_iq: np.ndarray | None = None

        # Control values from GUI
        self.center_freq_mhz = center_freq_mhz
        self.volume = volume

        # Buffer size limits
        self.AUDIO_BUFFER_PREFILL_SAMPLES = int(config.FS_AUDIO_OUT * config.PREFILL_S)
        self.AUDIO_BUFFER_MAX_SAMPLES = int(config.FS_AUDIO_OUT * config.MAX_BUF_S)