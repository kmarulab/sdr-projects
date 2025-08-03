# dsp.py
"""Digital Signal Processing functions for FM demodulation."""

from __future__ import annotations
import math
import numpy as np
from scipy.signal import butter, lfilter, resample_poly, decimate
import config

# Pre-calculate filter coefficients and de-emphasis alpha
B_LPF, A_LPF = butter(5, 15e3 / (config.FS_AUDIO_IN / 2))
ALPHA_DE = math.exp(-1 / (config.FS_AUDIO_IN * 75e-6))

def fm_disc(iq: np.ndarray) -> np.ndarray:
    """Perform FM discrimination."""
    return np.angle(iq[1:] * np.conj(iq[:-1])).astype(np.float32)

def iq_to_audio(iq: np.ndarray, vol: float) -> np.ndarray:
    """
    Demodulates an IQ stream into an audio signal.
    Includes FM discrimination, decimation, filtering, de-emphasis, and resampling.
    """
    audio = fm_disc(iq)
    audio = decimate(audio, config.DECIM, ftype='fir')
    audio = lfilter(B_LPF, A_LPF, audio)
    audio = lfilter([1 - ALPHA_DE], [1, -ALPHA_DE], audio)
    audio -= np.mean(audio)
    audio = resample_poly(audio, 160, 163)  # 48,762 Hz -> 48,000 Hz
    audio /= (np.max(np.abs(audio)) + 1e-3)
    return (audio * vol).astype(np.float32)