# config.py
"""Configuration constants for the WBFM receiver."""

from __future__ import annotations

# SDR and DSP parameters
CENTER_MHZ = 103.7
F_MIN, F_MAX, STEP = 88.0, 108.0, 0.1
GAIN_DB = 38
FS_SDR = 2_048_000            # Lime sample-rate (Hz)
IQ_CHUNK = 131_072            # 64 ms of IQ
DECIM = 42                    # 2.048 MHz / 42 ≈ 48,762 Hz
FS_AUDIO_IN = FS_SDR / DECIM  # 48,762 Hz
FS_AUDIO_OUT = 48_000         # 48 kHz audio sink

# GUI and visualization parameters
FFT_N = 4096
WF_ROWS = 400
VOL_INIT = 0.4

# Audio buffering parameters
BLOCK = 1024                  # sounddevice block size
PREFILL_S = 0.5               # seconds to pre-fill before starting playback
MAX_BUF_S = 1.5               # max audio buffer size in seconds