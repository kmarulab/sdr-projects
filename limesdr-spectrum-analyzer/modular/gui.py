# gui.py
"""Manages the Matplotlib GUI for spectrum visualization and user interaction."""

from __future__ import annotations
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import numpy as np
from collections import deque
import config
from shared_state import AppState

class SpectrumGUI:
    """Encapsulates the Matplotlib figure, plots, and event handlers."""
    def __init__(self, state: AppState):
        self.state = state
        plt.ion()
        self.fig = plt.figure(figsize=(12, 9))
        gs = self.fig.add_gridspec(4, 1, height_ratios=[1, 2, 0.05, 0.05], hspace=0.35)
        
        self.ax_psd = self.fig.add_subplot(gs[0])
        self.ax_wf = self.fig.add_subplot(gs[1])
        ax_tune = self.fig.add_subplot(gs[2])
        ax_vol = self.fig.add_subplot(gs[3])

        self._setup_plots()
        self.sl_f = Slider(ax_tune, "Center MHz", config.F_MIN, config.F_MAX, valinit=state.center_freq_mhz, valstep=config.STEP)
        self.sl_v = Slider(ax_vol, "Volume", 0.0, 1.0, valinit=state.volume, valstep=0.01)
        self._setup_events()
        self.window = np.hanning(config.FFT_N)

    def _setup_plots(self):
        self.freq_axis = np.fft.fftshift(np.fft.fftfreq(config.FFT_N, 1/config.FS_SDR)) / 1e6
        self.line_psd, = self.ax_psd.plot([], [])
        self.ax_psd.set_ylim(-120, 40)
        self.ax_psd.grid(True)
        self.ax_psd.set_ylabel("dB")

        self.wf_deque = deque((np.full(config.FFT_N, -120, np.float32) for _ in range(config.WF_ROWS)))
        self.wfi = self.ax_wf.imshow(np.vstack(self.wf_deque), cmap="inferno", origin='lower', aspect='auto', vmin=-110, vmax=0)
        self.ax_wf.set_ylabel("Time →")

    def _setup_events(self):
        self.sl_f.on_changed(self._update_state)
        self.sl_v.on_changed(self._update_state)
        self.fig.canvas.mpl_connect('key_press_event', self._on_key)

    def _update_state(self, _=None):
        with self.state.lock:
            self.state.center_freq_mhz = self.sl_f.val
            self.state.volume = self.sl_v.val

    def _on_key(self, event):
        if event.key == 'left': self.sl_f.set_val(max(config.F_MIN, self.sl_f.val - config.STEP))
        elif event.key == 'right': self.sl_f.set_val(min(config.F_MAX, self.sl_f.val + config.STEP))
        elif event.key == 'up': self.sl_v.set_val(min(1.0, self.sl_v.val + 0.05))
        elif event.key == 'down': self.sl_v.set_val(max(0.0, self.sl_v.val - 0.05))

    def update_plots(self):
        with self.state.lock:
            iq = self.state.latest_iq.copy() if self.state.latest_iq is not None else None
            current_freq = self.state.center_freq_mhz
        
        if iq is not None:
            spec = 20 * np.log10(np.abs(np.fft.fftshift(np.fft.fft(iq[:config.FFT_N] * self.window))) + 1e-9)
            self.wf_deque.pop()
            self.wf_deque.appendleft(spec.astype(np.float32))
            
            freqs = self.freq_axis + current_freq
            self.line_psd.set_data(freqs, spec)
            self.ax_psd.set_xlim(freqs[0], freqs[-1])
            
            self.wfi.set_data(np.vstack(list(self.wf_deque)))
            self.wfi.set_extent([freqs[0], freqs[-1], 0, config.WF_ROWS])
            
        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()

    def is_active(self) -> bool:
        return plt.fignum_exists(self.fig.number)

    def close(self):
        plt.close(self.fig)