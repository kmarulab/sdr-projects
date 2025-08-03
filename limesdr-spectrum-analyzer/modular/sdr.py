# sdr.py
"""Manages the SDR device, data streaming, and processing thread."""

from __future__ import annotations
import SoapySDR
import numpy as np
import threading
import time
import config
import dsp
from shared_state import AppState

class SDRManager:
    """Encapsulates SDR device setup and the worker thread."""
    def __init__(self, state: AppState):
        self.state = state
        self.device = None
        self.rx_stream = None

    def _worker(self):
        """The main worker function running in a dedicated thread."""
        try:
            self.device = SoapySDR.Device({"driver": "lime"})
            self.device.setSampleRate(SoapySDR.SOAPY_SDR_RX, 0, config.FS_SDR)
            self.device.setGain(SoapySDR.SOAPY_SDR_RX, 0, config.GAIN_DB)
            self.device.setAntenna(SoapySDR.SOAPY_SDR_RX, 0, "LNAW")
            self.device.setFrequency(SoapySDR.SOAPY_SDR_RX, 0, self.state.center_freq_mhz * 1e6)

            self.rx_stream = self.device.setupStream(SoapySDR.SOAPY_SDR_RX, "CF32")
            self.device.activateStream(self.rx_stream)
            iq_chunk = np.empty(config.IQ_CHUNK, np.complex64)

            while not self.state.stop_event.is_set():
                if self.device.readStream(self.rx_stream, [iq_chunk], config.IQ_CHUNK, timeoutUs=200000).ret != config.IQ_CHUNK:
                    continue

                with self.state.lock:
                    freq = self.state.center_freq_mhz
                    vol = self.state.volume
                
                if abs(freq * 1e6 - self.device.getFrequency(SoapySDR.SOAPY_SDR_RX, 0)) > 1e3:
                    self.device.setFrequency(SoapySDR.SOAPY_SDR_RX, 0, freq * 1e6)
                
                audio = dsp.iq_to_audio(iq_chunk, vol)

                with self.state.lock:
                    self.state.audio_buffer.append(audio)
                    self.state.audio_buffer_samples += len(audio)
                    self.state.latest_iq = iq_chunk.copy()
                    if not self.state.start_audio.is_set() and self.state.audio_buffer_samples >= self.state.AUDIO_BUFFER_PREFILL_SAMPLES:
                        self.state.start_audio.set()
                
                while self.state.audio_buffer_samples > self.state.AUDIO_BUFFER_MAX_SAMPLES and not self.state.stop_event.is_set():
                    time.sleep(0.02)
        finally:
            if self.device and self.rx_stream:
                self.device.deactivateStream(self.rx_stream)
                self.device.closeStream(self.rx_stream)

    def start(self):
        """Starts the SDR worker thread."""
        threading.Thread(target=self._worker, daemon=True).start()