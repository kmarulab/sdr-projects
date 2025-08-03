from __future__ import annotations
import math, time, threading
from collections import deque

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import SoapySDR, sounddevice as sd
from scipy.signal import decimate, butter, lfilter, resample_poly

#config
CENTER_MHZ = 103.7
F_MIN, F_MAX, STEP = 88.0, 108.0, 0.1
GAIN_DB = 38
FS_SDR = 2_048_000            # Lime sample‑rate (Hz)
IQ_CHUNK = 131_072            # 64 ms of IQ
DECIM = 42                    # 2.048 MHz / 42 ≈ 48 762 Hz
FS_AUDIO_IN = FS_SDR / DECIM  # 48 762 Hz
FS_AUDIO_OUT = 48_000         # 48 kHz sink
FFT_N = 4096
WF_ROWS = 400
VOL_INIT = 0.4

BLOCK = 1024                  # sounddevice block
PREFILL_S = 0.5               # seconds to pre‑fill before starting
MAX_BUF_S = 1.5               # stop producer when > this seconds queued

#dsp
def fm_disc(iq: np.ndarray) -> np.ndarray:
    return np.angle(iq[1:] * np.conj(iq[:-1])).astype(np.float32)

B_LPF, A_LPF = butter(5, 15e3 / (FS_AUDIO_IN / 2))
ALPHA_DE = math.exp(-1 / (FS_AUDIO_IN * 75e-6))


def iq_to_audio(iq: np.ndarray, vol: float) -> np.ndarray:
    audio = fm_disc(iq)
    audio = decimate(audio, DECIM, ftype='fir')
    audio = lfilter(B_LPF, A_LPF, audio)
    audio = lfilter([1-ALPHA_DE], [1, -ALPHA_DE], audio)
    audio -= np.mean(audio)
    audio = resample_poly(audio, 160, 163)  # 48 762 → 48 000
    audio /= (np.max(np.abs(audio)) + 1e-3)
    return (audio * vol).astype(np.float32)

#shared state
audio_buf: deque[np.ndarray] = deque()
buf_samples = 0
BUF_PREFILL = int(FS_AUDIO_OUT * PREFILL_S)
BUF_MAX = int(FS_AUDIO_OUT * MAX_BUF_S)
latest_iq: np.ndarray | None = None
state_lock = threading.Lock()
start_play = threading.Event()
stop_evt = threading.Event()

#sdr worker
def sdr_worker():
    dev = SoapySDR.Device({"driver": "lime"})
    dev.setSampleRate(SoapySDR.SOAPY_SDR_RX, 0, FS_SDR)
    dev.setGain(SoapySDR.SOAPY_SDR_RX, 0, GAIN_DB)
    dev.setAntenna(SoapySDR.SOAPY_SDR_RX, 0, "LNAW")
    dev.setFrequency(SoapySDR.SOAPY_SDR_RX, 0, CENTER_MHZ*1e6)
    rx = dev.setupStream(SoapySDR.SOAPY_SDR_RX, "CF32")
    dev.activateStream(rx)
    iq = np.empty(IQ_CHUNK, np.complex64)

    try:
        while not stop_evt.is_set():
            if dev.readStream(rx, [iq], IQ_CHUNK, timeoutUs=200000).ret != IQ_CHUNK:
                continue

            # Update centre freq if user moved slider
            new_fc = sl_f.val
            if abs(new_fc*1e6 - dev.getFrequency(SoapySDR.SOAPY_SDR_RX,0)) > 1e3:
                dev.setFrequency(SoapySDR.SOAPY_SDR_RX,0, new_fc*1e6)

            # Audio
            audio = iq_to_audio(iq, sl_v.val)
            with state_lock:
                audio_buf.append(audio)
                global buf_samples, latest_iq
                buf_samples += len(audio)
                latest_iq = iq.copy()
                if buf_samples >= BUF_PREFILL:
                    start_play.set()
            # Back‑pressure
            while buf_samples > BUF_MAX and not stop_evt.is_set():
                time.sleep(0.02)
    finally:
        dev.deactivateStream(rx)
        dev.closeStream(rx)

#audio callback
def audio_cb(outdata, frames, *_):
    global buf_samples
    need = frames
    chunks = []
    with state_lock:
        while need > 0 and audio_buf:
            c = audio_buf.popleft()
            buf_samples -= len(c)
            if len(c) <= need:
                chunks.append(c)
                need -= len(c)
            else:
                chunks.append(c[:need])
                audio_buf.appendleft(c[need:])
                buf_samples += len(c)-need
                need = 0
    if need: chunks.append(np.zeros(need, np.float32))
    outdata[:,0] = np.concatenate(chunks)

#gui setup
plt.ion()
fig = plt.figure(figsize=(12,9))
gs = fig.add_gridspec(4,1,height_ratios=[1,2,0.05,0.05],hspace=0.35)
ax_psd, ax_wf, ax_tune, ax_vol = (fig.add_subplot(gs[i]) for i in range(4))

freq_axis = np.fft.fftshift(np.fft.fftfreq(FFT_N,1/FS_SDR))/1e6
line_psd, = ax_psd.plot([],[])
ax_psd.set_ylim(-120,40)
ax_psd.grid(True)
ax_psd.set_ylabel("dB")
wf_deque = deque(np.full(FFT_N,-120,np.float32) for _ in range(WF_ROWS))
wfi = ax_wf.imshow(np.vstack(wf_deque), cmap="inferno", origin='lower', aspect='auto', vmin=-110, vmax=0, extent=[0,1,0,WF_ROWS])
ax_wf.set_ylabel("Time →")

sl_f = Slider(ax_tune, "Center MHz", F_MIN,F_MAX,valinit=CENTER_MHZ,valstep=STEP)
sl_v = Slider(ax_vol, "Volume",0.0,1.0,valinit=VOL_INIT,valstep=0.01)
plt.show(block=False)

#keyboard shortcuts
def on_key(e):
    if e.key=='left': sl_f.set_val(max(F_MIN,sl_f.val-STEP))
    elif e.key=='right': sl_f.set_val(min(F_MAX,sl_f.val+STEP))
    elif e.key=='up': sl_v.set_val(min(1.0,sl_v.val+0.05))
    elif e.key=='down': sl_v.set_val(max(0.0,sl_v.val-0.05))
fig.canvas.mpl_connect('key_press_event', on_key)

#threads starts
threading.Thread(target=sdr_worker,daemon=True).start()
print("Buffering …")
start_play.wait()
print("Audio start …")

audio_out = sd.OutputStream(channels=1,samplerate=FS_AUDIO_OUT,blocksize=BLOCK,callback=audio_cb)
audio_out.start()

window = np.hanning(FFT_N)

#gui refresh loop
try:
    while plt.fignum_exists(fig.number):
        with state_lock:
            iq = latest_iq.copy() if latest_iq is not None else None
        if iq is not None:
            spec = 20*np.log10(np.abs(np.fft.fftshift(np.fft.fft(iq[:FFT_N]*window)))+1e-9)
            wf_deque.pop()
            wf_deque.appendleft(spec.astype(np.float32))
            freqs = freq_axis + sl_f.val
            line_psd.set_data(freqs,spec)
            ax_psd.set_xlim(freqs[0],freqs[-1])
            wfi.set_data(np.vstack(wf_deque))
            wfi.set_extent([freqs[0],freqs[-1],0,WF_ROWS])
        fig.canvas.draw_idle()
        fig.canvas.flush_events()
        plt.pause(0.05)
except KeyboardInterrupt:
    pass
finally:
    stop_evt.set()
    audio_out.stop()
    audio_out.close()
    plt.close(fig)
    print("Done.")

